package ch.ethz.systems.floodns.ext.routing;

import ch.ethz.systems.floodns.core.AcyclicPath;
import ch.ethz.systems.floodns.core.Connection;
import ch.ethz.systems.floodns.core.Link;
import ch.ethz.systems.floodns.core.Simulator;
import ch.ethz.systems.floodns.deeplearningtraining.Job;
import ch.ethz.systems.floodns.ext.basicsim.topology.Topology;
import ch.ethz.systems.floodns.ext.sysutils.Command;
import ch.ethz.systems.floodns.ext.sysutils.SharedMemory;
import com.google.gson.Gson;
import org.apache.commons.lang3.StringUtils;
import org.apache.commons.lang3.tuple.ImmutablePair;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.*;

/**
 * Routing strategy that uses an LP problem to determine the path assignments.
 * <p>
 * ILP formulation:
 * <p>
 * \min \alpha
 * <p>
 * Subject to \sum_{p \in P_l} x_p^l = 1 \forall l \in L
 * <p>
 * \sum_{l \in L} \sum_{p \in P_l : e \in p} x_p^l \leq x_e \forall e \in E
 * <p>
 * x_e \leq \alpha \forall e \in E
 * <p>
 * x_p^l = 0 \forall l \in L, p \in P_l : e \in p \land e \in F
 * <p>
 * x_p^l \in \{0,1\} \forall p \in P_l, l \in L
 * <p>
 * x_e \in \mathbb{N}^+ \forall e \in E
 * <p>
 * \alpha \in \mathbb{N}^+
 */
public class IlpSolverRoutingStrategy extends CentralizedRoutingStrategy {

    private final Map<Integer, ImmutablePair<Integer, Integer>> commodities = new HashMap<>();
    private final Map<Integer, Connection> connections = new HashMap<>();
    private final Map<Integer, Integer> connIdToJobId = new HashMap<>();
    private final String runDirectory;
    private final String sharedMemoryPythonPath;
    private final String sharedMemoryJavaPath;

    public IlpSolverRoutingStrategy(Simulator simulator, Topology topology, String runDirectory) {
        super(simulator, topology);
        this.runDirectory = runDirectory;
        this.sharedMemoryJavaPath = runDirectory + "/shared_memory_java.json";
        this.sharedMemoryPythonPath = runDirectory + "/shared_memory_python.json";
    }

    @Override
    public void addSrcDst(Connection connection) {
        int srcId = connection.getSrcNodeId();
        int dstId = connection.getDstNodeId();
        int connId = connection.getConnectionId();
        commodities.put(connId, ImmutablePair.of(srcId, dstId));
        connIdToJobId.put(connId, connection.getJobId());
        connections.put(connId, connection);
    }

    @Override
    public void clearResources(Connection connection) {
        super.clearResources(connection);
        commodities.remove(connection.getConnectionId());
        connIdToJobId.remove(connection.getConnectionId());
        connections.remove(connection.getConnectionId());
    }

    @Override
    public void determinePathAssignments() {
        if (commodities.isEmpty()) {
            return;
        }

        long start = System.currentTimeMillis();
        List<Integer> coreIds = getCoreIds();

//        writeLpFile();
//        solveProblem();
//        Map<Integer, Integer> assignedPaths = readSolution();
        Map<Integer, Integer> assignedPaths = SharedMemory.receivePathAssignmentsFromController(
                sharedMemoryJavaPath, sharedMemoryPythonPath, getJsonRequest(), runDirectory, true
        );
        for (int connId : assignedPaths.keySet()) {
            Connection connection = connections.get(connId);
            int coreId = coreIds.get(assignedPaths.get(connId) % coreIds.size());
            AcyclicPath path = RoutingUtility.constructPath(network, connection, coreId);
            Job job = simulator.getJobs().get(connIdToJobId.get(connId));
            ImmutablePair<Integer, Integer> commodity = commodities.get(connId);
            job.getCommoditiesPathMap().put(commodity, path);
            if (activeConnections.contains(connId)) {
                RoutingUtility.resetPath(simulator, simulator.getActiveConnection(connId), path);
            }
        }
        durations.add(System.currentTimeMillis() - start);
    }


    private String getJsonRequest() {
        Set<Link> failedLinks = new HashSet<>(network.getFailedLinks());
        Set<ImmutablePair<Integer, Integer>> failedLinkPairs = new HashSet<>();
        failedLinks.forEach(link -> failedLinkPairs.add(ImmutablePair.of(link.getFrom(), link.getTo())));
        failedLinks.forEach(link -> failedLinkPairs.add(ImmutablePair.of(link.getTo(), link.getFrom())));

        Map<String, String> map = new HashMap<>();
        map.put("commodities", commodities.toString());
        map.put("failed_links", failedLinkPairs.toString());
        map.put("failed_cores", network.getFailedNodes().toString());
        map.put("num_tors", String.valueOf(topology.getDetails().getNumTors()));
        Gson gson = new Gson();
        return gson.toJson(map);
    }

    private void writeLpFile() {
        String fileName = runDirectory + "/model.lp";
        try {
            PrintWriter writer = new PrintWriter(fileName, "UTF-8");
            writer.println("Minimize");
            writer.println("OBJ: alpha");
            writer.println("Subject To");

            List<Integer> coreIds = getCoreIds();
            int constraintId = 0;
            for (int connId : commodities.keySet()) {
                writer.print("c" + constraintId + ": ");
                for (int i = 0; i < coreIds.size(); i++) {
                    writer.print("x_p_l_" + connId + "_" + i);
                    if (i < coreIds.size() - 1) {
                        writer.print(" + ");
                    }
                }
                writer.println(" = 1");
                constraintId++;
            }

            for (int coreId : coreIds) {
                for (int torId : topologyDetails.getTorNodeIds()) {
                    writer.print("c" + constraintId + ": ");
                    writer.println("- x_e_" + torId + "," + coreId + "_ <= 0");

                    constraintId++;
                    writer.print("c" + constraintId + ": ");
                    writer.println("- x_e_" + coreId + "," + torId + "_ <= 0");

                    constraintId++;
                    writer.print("c" + constraintId + ": ");
                    writer.println("- alpha + x_e_" + torId + "," + coreId + "_ <= 0");

                    constraintId++;
                    writer.print("c" + constraintId + ": ");
                    writer.println("- alpha + x_e_" + coreId + "," + torId + "_ <= 0");
                }
            }

            writer.println("Bounds");
            writer.println("0 <= alpha");
            for (int coreId : coreIds) {
                for (int torId : topologyDetails.getTorNodeIds()) {
                    writer.println("0 <= x_e_" + torId + "," + coreId + "_");
                    writer.println("0 <= x_e_" + coreId + "," + torId + "_");
                }
            }

            writer.println("Generals");
            writer.println("alpha");
            for (int coreId : coreIds) {
                for (int torId : topologyDetails.getTorNodeIds()) {
                    writer.println("x_e_" + torId + "," + coreId + "_");
                    writer.println("x_e_" + coreId + "," + torId + "_");
                }
            }

            for (int connId : commodities.keySet()) {
                for (int i = 0; i < coreIds.size(); i++) {
                    writer.println("x_p_l_" + connId + "_" + i);
                }
            }

            writer.println("End");
            writer.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private void solveProblem() {
        String[] cmdArray = new String[]{
                "scip",
                "-f",
                runDirectory + "/model.lp",
        };
        Command.runCommandWriteOutput(cmdArray, runDirectory + "/solution.txt", false);
    }

    private Map<Integer, Integer> readSolution() {
        Map<Integer, Integer> assignedPaths = new HashMap<>();
        String fileName = runDirectory + "/solution.txt";
        try {
            BufferedReader reader = new BufferedReader(new FileReader(fileName));

            String line;
            boolean start = false;
            while ((line = reader.readLine()) != null) {
                if (StringUtils.containsIgnoreCase(line, "objective value:")) {
                    start = true;
                }
                if (start && line.startsWith("x_p_")) {
                    String[] parts = line.split(" ")[0].split("_");
                    int connId = Integer.parseInt(parts[3]);
                    int pathId = Integer.parseInt(parts[4]);
                    assignedPaths.put(connId, pathId);
                    if (assignedPaths.size() == commodities.size()) {
                        break;
                    }
                }
            }
            reader.close();
        } catch (IOException e) {
            e.printStackTrace();
        }

        return assignedPaths;
    }
}
