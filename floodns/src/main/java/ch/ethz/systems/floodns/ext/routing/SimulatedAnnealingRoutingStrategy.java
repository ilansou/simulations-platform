package ch.ethz.systems.floodns.ext.routing;

import ch.ethz.systems.floodns.core.*;
import ch.ethz.systems.floodns.deeplearningtraining.Job;
import ch.ethz.systems.floodns.ext.basicsim.topology.Topology;
import org.apache.commons.lang3.tuple.ImmutablePair;

import java.util.*;
import java.util.stream.Collectors;

public class SimulatedAnnealingRoutingStrategy extends CentralizedRoutingStrategy {

    private final Set<Connection> connections = new HashSet<>();
    private final Random random;


    public SimulatedAnnealingRoutingStrategy(Simulator simulator, Topology topology, Random random) {
        super(simulator, topology);
        this.random = random;
    }

    @Override
    public void addSrcDst(Connection connection) {
        connections.add(connection);
    }

    @Override
    public void clearResources(Connection connection) {
        super.clearResources(connection);
        connections.remove(connection);
    }

    @Override
    public void determinePathAssignments() {
        if (connections.isEmpty()) {
            return;
        } else if (connections.size() == 1) {
            Connection connection = connections.iterator().next();
            AcyclicPath path = RoutingUtility.constructPath(network, connection, getCoreIds().get(0));
            RoutingUtility.resetPath(simulator, connection, path);
            return;
        }
        long start = System.currentTimeMillis();
        Map<Integer, Integer> currentState = getInitialState();
        int currentEnergy = calculateEnergy(currentState);

        // Simulated annealing
        double temperature = 1000;
        double coolingRate = 0.01;
        while (temperature > 0.1) {
            Map<Integer, Integer> neighbourState = getNeighbour(currentState);
            int neighbourEnergy = calculateEnergy(neighbourState);
            if (neighbourEnergy < currentEnergy) {
                currentState = new HashMap<>(neighbourState);
                currentEnergy = neighbourEnergy;
            } else if (acceptanceProbability(currentEnergy, neighbourEnergy, temperature) > random.nextDouble()) {
                currentState = new HashMap<>(neighbourState);
                currentEnergy = neighbourEnergy;
            }
            temperature *= 1 - coolingRate;
        }

        // Set the path assignments
        List<Integer> coreIds = getCoreIds();

        int numCores = topologyDetails.getNumCores() - network.getFailedNodes().size();
        currentState.forEach((dstNodeId, selectedCoreId) -> {
            Set<Connection> dstConnections = connections
                    .stream().filter(connection -> connection.getDstNodeId() == dstNodeId)
                    .collect(Collectors.toSet());
            dstConnections.forEach(dstConnection -> {
                int connId = dstConnection.getConnectionId();
                int coreId = selectedCoreId % numCores;
                AcyclicPath path = RoutingUtility.constructPath(network, dstConnection, coreIds.get(coreId));
                if (activeConnections.contains(connId)) {
                    RoutingUtility.resetPath(simulator, simulator.getActiveConnection(connId), path);
                }
                Job job = simulator.getJobs().get(dstConnection.getJobId());
                ImmutablePair<Integer, Integer> commodity = ImmutablePair.of(dstConnection.getSrcNodeId(), dstConnection.getDstNodeId());
                job.getCommoditiesPathMap().put(commodity, path);
            });
        });
        durations.add(System.currentTimeMillis() - start);
    }

    private Map<Integer, Integer> getInitialState() {
        Map<Integer, Integer> initialState = new HashMap<>();
        connections.forEach(connection -> {
            int dstNodeId = connection.getDstNodeId();
            int dstTorId = connection.getDstNode().getIncomingConnectedToNodes().iterator().next();
            List<Integer> torHostIds = new ArrayList<>(topologyDetails.getServersOfTor(dstTorId));
            int coreId = torHostIds.indexOf(dstNodeId);
            initialState.putIfAbsent(connection.getDstNodeId(), coreId);
        });

        return initialState;
    }

    private Map<Integer, Integer> getNeighbour(Map<Integer, Integer> currentState) {
        return random.nextDouble() > 0.5 ? swapConnections(currentState) : swapDestinationsCores(currentState);
    }

    /**
     * Calculate the energy of the current state.
     * The energy is the sum of all most utilized links, i.e.,
     * the number of flows that pass through the most utilized links.
     * For example, if we have the following links:
     * - Link 1: 10 flows
     * - Link 2: 5 flows
     * - Link 3: 5 flows
     * - Link 4: 10 flows
     * Then the energy is 10 + 10 = 20.
     *
     * @param state The current state
     * @return The energy of the current state
     */
    private int calculateEnergy(Map<Integer, Integer> state) {
        int energy = 0;
        List<Integer> coreIds = new ArrayList<>(topology.getDetails().getCoreNodeIds());
        Set<Integer> failedNodes = network.getFailedNodes().stream().map(Node::getNodeId).collect(Collectors.toSet());
        coreIds.removeAll(failedNodes);
        Map<Link, Integer> linkNumActiveFlows = new HashMap<>();
        state.forEach((dstNodeId, coreIndex) -> {
            int coreId = coreIds.get(coreIndex % coreIds.size());
            Set<Connection> dstConnections = connections
                    .stream().filter(connection -> connection.getDstNodeId() == dstNodeId)
                    .collect(Collectors.toSet());
            dstConnections.forEach(connection -> {
                assert connection.getSrcNode().getOutgoingConnectedToNodes().size() == 1; // Host is connected to only one ToR
                int srcTorId = connection.getSrcNode().getOutgoingConnectedToNodes().iterator().next();
                network.getPresentLinksBetween(srcTorId, coreId).forEach(link -> linkNumActiveFlows.put(link, linkNumActiveFlows.getOrDefault(link, 0) + 1));
                assert connection.getDstNode().getIncomingConnectedToNodes().size() == 1; // Host is connected to only one ToR
                int dstTorId = connection.getDstNode().getIncomingConnectedToNodes().iterator().next();
                network.getPresentLinksBetween(coreId, dstTorId).forEach(link -> linkNumActiveFlows.put(link, linkNumActiveFlows.getOrDefault(link, 0) + 1));
            });
        });
        // Get the most utilized links
        List<Integer> numActiveFlows = new ArrayList<>(linkNumActiveFlows.values());
        numActiveFlows.sort(Collections.reverseOrder());
        int maxNumActiveFlows = numActiveFlows.get(0);
        // Calculate the energy
        for (int numActiveFlow : numActiveFlows) {
            if (numActiveFlow == maxNumActiveFlows) {
                energy += numActiveFlow;
            } else {
                break;
            }
        }
        return energy;
    }

    private double acceptanceProbability(double currentEnergy, double candidateEnergy, double temperature) {
        if (currentEnergy > candidateEnergy) {
            return 1;
        }
        return Math.exp((currentEnergy - candidateEnergy) / temperature);
    }

    private Map<Integer, Integer> swapDestinationsCores(Map<Integer, Integer> currentState) {
        List<Integer> dstIds = new ArrayList<>(currentState.keySet());
        Map<Integer, List<Integer>> torToDstIds = new HashMap<>();
        dstIds.forEach(dstId -> {
            int dstTorId = topologyDetails.getTorIdOfServer(dstId);
            torToDstIds.putIfAbsent(dstTorId, new ArrayList<>());
            torToDstIds.get(dstTorId).add(dstId);
        });
        // keep only the tor ids that have more than one dst ids
        Map<Integer, List<Integer>> finalTorToDstIds = torToDstIds.entrySet().stream().filter(entry -> entry.getValue().size() > 1).collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue));
        if (finalTorToDstIds.isEmpty()) {
            return swapConnections(currentState);
        }

        List<Integer> torIds = new ArrayList<>(finalTorToDstIds.keySet());
        int torId = torIds.get(random.nextInt(torIds.size()));

        Map<Integer, Integer> neighbour = new HashMap<>(currentState);
        List<Integer> hostIds = finalTorToDstIds.get(torId);
        swap(hostIds, neighbour);
        return neighbour;
    }

    private Map<Integer, Integer> swapConnections(Map<Integer, Integer> currentState) {
        Map<Integer, Integer> neighbour = new HashMap<>(currentState);
        List<Integer> dstIds = new ArrayList<>(neighbour.keySet());
        swap(dstIds, neighbour);
        return neighbour;
    }

    private void swap(List<Integer> hostIds, Map<Integer, Integer> neighbour) {
        int firstDstId = hostIds.get(random.nextInt(hostIds.size()));
        int secondDstId = hostIds.get(random.nextInt(hostIds.size()));
        while (firstDstId == secondDstId) {
            secondDstId = hostIds.get(random.nextInt(hostIds.size()));
        }

        // Swap the core ids
        int firstCoreId = neighbour.get(firstDstId);
        int secondCoreId = neighbour.get(secondDstId);
        neighbour.put(firstDstId, secondCoreId);
        neighbour.put(secondDstId, firstCoreId);
    }
}
