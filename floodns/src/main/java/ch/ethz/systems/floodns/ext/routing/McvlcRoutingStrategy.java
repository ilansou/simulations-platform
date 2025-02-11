package ch.ethz.systems.floodns.ext.routing;

import ch.ethz.systems.floodns.core.AcyclicPath;
import ch.ethz.systems.floodns.core.Connection;
import ch.ethz.systems.floodns.core.Link;
import ch.ethz.systems.floodns.core.Simulator;
import ch.ethz.systems.floodns.deeplearningtraining.Job;
import ch.ethz.systems.floodns.ext.basicsim.topology.Topology;
import org.apache.commons.lang3.tuple.ImmutablePair;

import java.util.*;
import java.util.stream.Collectors;

/**
 * Routing decider that Minimizes Crossing Virtual Link Collisions (MCVLC).
 * A Virtual Link is an Elephant Flow. Valid for 2-layer Fat-Tree topologies.
 * Steps of the algorithm:
 * - For each ToR in ToRs:
 * - For each virtual link in ToR(outgoing_virtual_links):
 * - Assign the virtual link to the path with the least number of assigned virtual links.
 * - Update the number of assigned virtual links for the assigned path (on each edge).
 * - For each virtual link in ToR(incoming_virtual_links):
 * - Assign the virtual link to the path with the least number of assigned virtual links.
 * - Update the number of assigned virtual links for the assigned path (on each edge).
 * This can be thought as maximal matching in bipartite graphs.
 */
public class McvlcRoutingStrategy extends CentralizedRoutingStrategy {

    private final Map<Integer, Set<Connection>> uplinkTorConnections = new HashMap<>();
    private final Map<Integer, Set<Connection>> downlinkTorConnections = new HashMap<>();

    public McvlcRoutingStrategy(Simulator simulator, Topology topology) {
        super(simulator, topology);
    }

    public void addSrcDst(Connection connection) {
        int srcId = connection.getSrcNodeId();
        int dstId = connection.getDstNodeId();
        uplinkTorConnections.computeIfAbsent(topologyDetails.getTorIdOfServer(srcId), k -> new HashSet<>()).add(connection);
        downlinkTorConnections.computeIfAbsent(topologyDetails.getTorIdOfServer(dstId), k -> new HashSet<>()).add(connection);
    }

    public void clearResources(Connection connection) {
        super.clearResources(connection);
        int srcId = connection.getSrcNodeId();
        int dstId = connection.getDstNodeId();
        uplinkTorConnections.get(topologyDetails.getTorIdOfServer(srcId)).remove(connection);
        downlinkTorConnections.get(topologyDetails.getTorIdOfServer(dstId)).remove(connection);
    }

    public void determinePathAssignments() {
        if (uplinkTorConnections.isEmpty() && downlinkTorConnections.isEmpty()) {
            return;
        }

        Set<Connection> assignedConnections = new HashSet<>();
        Map<Link, Integer> linkAssignmentsCounter = new HashMap<>();
        List<Set<Connection>> torConnections = sortTorConnections();
        long start = System.currentTimeMillis();
        List<Integer> coreIds = getCoreIds();
        torConnections.forEach(connections -> {
            connections.removeAll(assignedConnections); // Remove already assigned connections
            connections.forEach(connection -> assignPath(connection, linkAssignmentsCounter, coreIds));
            assignedConnections.addAll(connections);
        });
        durations.add(System.currentTimeMillis() - start);
    }

    private void assignPath(
            Connection connection,
            Map<Link, Integer> linkAssignmentsCounter,
            List<Integer> coreIds
    ) {
        AcyclicPath path = RoutingUtility.determinePath(connection, linkAssignmentsCounter, network, coreIds);
        if (activeConnections.contains(connection.getConnectionId())) {
            RoutingUtility.resetPath(simulator, connection, path);
        }
        Job job = simulator.getJobs().get(connection.getJobId());
        ImmutablePair<Integer, Integer> commodity = ImmutablePair.of(connection.getSrcNodeId(), connection.getDstNodeId());
        job.getCommoditiesPathMap().put(commodity, path);
    }


    private List<Set<Connection>> sortTorConnections() {
        TreeMap<String, Set<Connection>> torLinksSrcDstMap = new TreeMap<>();
        topologyDetails.getTorNodeIds().forEach(torId -> {
            Optional.ofNullable(uplinkTorConnections.get(torId))
                    .ifPresent(uplinkCommodities -> torLinksSrcDstMap.put("a_" + torId, uplinkCommodities));
            Optional.ofNullable(downlinkTorConnections.get(torId))
                    .ifPresent(downlinkCommodities -> torLinksSrcDstMap.put("b_" + torId, downlinkCommodities));
        });

        // Sorted map
        Map<String, Set<Connection>> sortedMap = torLinksSrcDstMap.entrySet().stream()
                .sorted(Comparator.<Map.Entry<String, Set<Connection>>>comparingInt(e -> e.getValue().size()).reversed()
                        .thenComparing(Map.Entry.comparingByKey()))
                .collect(Collectors.toMap(
                        Map.Entry::getKey,
                        Map.Entry::getValue,
                        (oldValue, newValue) -> oldValue, LinkedHashMap::new));

        return new ArrayList<>(sortedMap.values());
    }
}
