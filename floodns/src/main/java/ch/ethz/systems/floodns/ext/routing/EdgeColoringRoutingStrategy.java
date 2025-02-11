package ch.ethz.systems.floodns.ext.routing;

import ch.ethz.systems.floodns.core.AcyclicPath;
import ch.ethz.systems.floodns.core.Connection;
import ch.ethz.systems.floodns.core.Simulator;
import ch.ethz.systems.floodns.deeplearningtraining.Job;
import ch.ethz.systems.floodns.ext.basicsim.topology.Topology;
import ch.ethz.systems.floodns.ext.utils.EdgeColoring;
import com.google.gson.Gson;
import org.apache.commons.lang3.tuple.ImmutablePair;

import java.util.*;

public class EdgeColoringRoutingStrategy extends CentralizedRoutingStrategy {

    private final Map<Integer, Connection> connections = new HashMap<>();
    private final Map<Integer, ImmutablePair<Integer, Integer>> torCommodities = new HashMap<>();
    private final Set<Integer> activeTors = new HashSet<>();
    private final String runDirectory;
    private final String sharedMemoryPythonPath;
    private final String sharedMemoryJavaPath;

    public EdgeColoringRoutingStrategy(Simulator simulator, Topology topology, String runDirectory) {
        super(simulator, topology);
        this.runDirectory = runDirectory;
        this.sharedMemoryJavaPath = runDirectory + "/shared_memory_java.json";
        this.sharedMemoryPythonPath = runDirectory + "/shared_memory_python.json";
    }

    @Override
    public void addSrcDst(Connection connection) {
        int srcId = connection.getSrcNodeId();
        int srcTorId = topologyDetails.getTorIdOfServer(srcId);
        int dstId = connection.getDstNodeId();
        int dstTorId = topologyDetails.getTorIdOfServer(dstId);
        connections.put(connection.getConnectionId(), connection);
        torCommodities.put(connection.getConnectionId(), ImmutablePair.of(srcTorId, dstTorId));
        activeTors.add(srcTorId);
        activeTors.add(dstTorId);
    }

    @Override
    public void clearResources(Connection connection) {
        super.clearResources(connection);
        connections.remove(connection.getConnectionId());
        torCommodities.remove(connection.getConnectionId());
    }

    @Override
    public void determinePathAssignments() {
        if (connections.isEmpty()) {
            return;
        }

        List<Integer> coreIds = getCoreIds();
        long start = System.currentTimeMillis();
        Map<Integer, Integer> assignments = EdgeColoring.colorEdges(torCommodities);
//        Map<Integer, Integer> assignments = SharedMemory.receivePathAssignmentsFromController(
//                sharedMemoryJavaPath, sharedMemoryPythonPath, getJsonRequest(), runDirectory, false
//        );
        for (int connId : assignments.keySet()) {
            Connection connection = connections.get(connId);
            int coreId = coreIds.get(assignments.get(connId) % coreIds.size());
            AcyclicPath path = RoutingUtility.constructPath(network, connection, coreId);
            if (activeConnections.contains(connId)) {
                RoutingUtility.resetPath(simulator, connections.get(connId), path);
            }
            Job job = simulator.getJobs().get(connections.get(connId).getJobId());
            ImmutablePair<Integer, Integer> commodity = ImmutablePair.of(connections.get(connId).getSrcNodeId(), connections.get(connId).getDstNodeId());
            job.getCommoditiesPathMap().put(commodity, path);
        }
        durations.add(System.currentTimeMillis() - start);
    }

    private String getJsonRequest() {
        Map<String, String> map = new HashMap<>();
        map.put("commodities", torCommodities.toString());
        map.put("output_folder", runDirectory);
        Gson gson = new Gson();
        return gson.toJson(map);
    }
}
