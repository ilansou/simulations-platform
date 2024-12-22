package ch.ethz.systems.floodns.ext.routing;

import ch.ethz.systems.floodns.core.AcyclicPath;
import ch.ethz.systems.floodns.core.Connection;
import ch.ethz.systems.floodns.core.Node;
import ch.ethz.systems.floodns.core.Simulator;
import ch.ethz.systems.floodns.deeplearningtraining.AssignmentsDurationLogger;
import ch.ethz.systems.floodns.deeplearningtraining.Job;
import ch.ethz.systems.floodns.ext.basicsim.topology.Topology;
import ch.ethz.systems.floodns.ext.graphutils.YenTopKspAlgorithmWrapper;
import org.apache.commons.lang3.tuple.ImmutablePair;

import java.util.*;
import java.util.stream.Collectors;

public abstract class CentralizedRoutingStrategy extends SinglePathRoutingStrategy {

    protected final Set<Integer> activeConnections;
    protected final List<Long> durations = new ArrayList<>();
    protected YenTopKspAlgorithmWrapper yenTopKsp;
    protected AssignmentsDurationLogger logger;

    public CentralizedRoutingStrategy(Simulator simulator, Topology topology) {
        super(simulator, topology);
        this.activeConnections = new HashSet<>();
        this.yenTopKsp = new YenTopKspAlgorithmWrapper(network);
        this.logger = simulator.getLoggerFactory().internalCreateAssignmentsDurationLogger(this);
    }

    @Override
    public AcyclicPath assignSinglePath(Connection connection) {
        activeConnections.add(connection.getConnectionId());
        Job job = simulator.getJobs().get(connection.getJobId());
        ImmutablePair<Integer, Integer> commodity = ImmutablePair.of(connection.getSrcNodeId(), connection.getDstNodeId());
        return job.getCommoditiesPathMap().get(commodity);
    }

    public abstract void addSrcDst(Connection connection);

    public void clearResources(Connection connection) {
        activeConnections.remove(connection.getConnectionId());
    }

    public abstract void determinePathAssignments();

    public AssignmentsDurationLogger getLogger() {
        return logger;
    }

    public double getAverageDuration() {
        return durations.stream().mapToLong(Long::longValue).average().orElse(0);
    }

    public int getNumAssignedConnections() {
        Collection<Job> jobs = simulator.getJobs().values();
        return jobs.stream().mapToInt(job -> job.getCommoditiesPathMap().size()).sum();
    }

    public List<Integer> getCoreIds() {
        List<Integer> coreIds = new ArrayList<>(topologyDetails.getCoreNodeIds());
        if (!network.getFailedLinks().isEmpty()) {
            Set<Integer> failedCoreIds = network.getFailedNodes().stream().map(Node::getNodeId).collect(Collectors.toSet());
            coreIds.removeAll(failedCoreIds);
        }
        return coreIds;
    }
}
