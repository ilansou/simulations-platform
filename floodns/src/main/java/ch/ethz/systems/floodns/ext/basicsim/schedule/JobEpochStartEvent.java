package ch.ethz.systems.floodns.ext.basicsim.schedule;

import ch.ethz.systems.floodns.core.Connection;
import ch.ethz.systems.floodns.core.Event;
import ch.ethz.systems.floodns.core.Simulator;
import ch.ethz.systems.floodns.deeplearningtraining.Job;
import ch.ethz.systems.floodns.ext.routing.CentralizedRoutingStrategy;
import ch.ethz.systems.floodns.ext.routing.RoutingStrategy;

import java.util.Map;
import java.util.Set;

public class JobEpochStartEvent extends Event {

    private final int jobId;
    private final long startTime;
    private final Map<Integer, Set<Connection>> stageConnections;
    private final RoutingStrategy routingStrategy;

    /**
     * Create event which will happen the given amount of time later.
     *
     * @param simulator        Simulator instance to which this event belongs
     * @param timeFromNow      Time it will take before happening from now (in nanoseconds)
     * @param stageConnections Map of connections per stage
     * @param routingStrategy  Routing strategy
     * @param jobId            Job ID
     */
    public JobEpochStartEvent(Simulator simulator, long timeFromNow, Map<Integer, Set<Connection>> stageConnections, RoutingStrategy routingStrategy, int jobId) {
        super(simulator, 0, timeFromNow);
        this.jobId = jobId;
        this.startTime = simulator.getCurrentTime() + timeFromNow;
        this.stageConnections = stageConnections;
        this.routingStrategy = routingStrategy;
    }

    @Override
    protected void trigger() {
        // TODO: This works for Data Parallelism, need to extend for Pipeline Parallelism and Hybrid Parallelism
        Job job = simulator.getJob(jobId);
        job.initializeEpoch(startTime, stageConnections);
        if (routingStrategy instanceof CentralizedRoutingStrategy) {
            CentralizedRoutingStrategy centralizedRoutingStrategy = (CentralizedRoutingStrategy) routingStrategy;
            stageConnections.values().forEach(stageCommodities -> stageCommodities.forEach(centralizedRoutingStrategy::addSrcDst));
            centralizedRoutingStrategy.determinePathAssignments();
            centralizedRoutingStrategy.getLogger().saveInfo(
                    centralizedRoutingStrategy.getAverageDuration(),
                    centralizedRoutingStrategy.getNumAssignedConnections()
            );
        }

        stageConnections.values().forEach(connections -> {
            connections.forEach(connection -> {
                ConnectionStartEvent event = new ConnectionStartEvent(simulator, 1, connection, routingStrategy);
                simulator.insertEvents(event);
            });
        });
    }

    @Override
    public String toString() {
        return "JobEpochStartEvent#" + jobId + "[stageConnections=" + stageConnections + "]";
    }
}
