package ch.ethz.systems.floodns.deeplearningtraining;

import ch.ethz.systems.floodns.core.Connection;
import ch.ethz.systems.floodns.ext.basicsim.schedule.ConnectionStartEvent;
import ch.ethz.systems.floodns.ext.routing.CentralizedRoutingStrategy;
import ch.ethz.systems.floodns.ext.routing.RoutingStrategy;
import org.apache.commons.lang3.tuple.ImmutablePair;

import java.util.List;

public class ParallelismUtils {

    public static Connection triggerNewFlow(Job job, int stageIndex, ImmutablePair<Integer, Integer> commodity, long nextStartTime) {
        int srcNodeId = commodity.getLeft();
        int dstNodeId = commodity.getRight();
        List<Connection> commodityConnections = job.getCommoditiesConnectionMap().get(commodity);
        double connSize = commodityConnections.get(commodityConnections.size() - 1).getTotalSize();
        Connection newConnection = new Connection(job.getSimulator(), job.getNetwork().getNode(srcNodeId), job.getNetwork().getNode(dstNodeId), connSize, job.getJobId());
        ConnectionStartEvent event = new ConnectionStartEvent(job.getSimulator(), nextStartTime, newConnection, job.getRoutingStrategy());
        job.getSimulator().insertEvents(event);
        RoutingStrategy routingStrategy = job.getRoutingStrategy();
        if (routingStrategy instanceof CentralizedRoutingStrategy) {
            ((CentralizedRoutingStrategy) routingStrategy).addSrcDst(newConnection);
        }
        job.getCommoditiesConnectionMap().get(commodity).add(newConnection);
        job.getCurrentEpoch().getStageConnections().get(stageIndex).add(newConnection);
        return newConnection;
    }

    public static boolean isNotFinishedAllLayers(Job job, List<ImmutablePair<Integer, Integer>> commodities, int currentStageIndex, int srcDstMicroBatchCount, int microBatchSize, long nextStartTime) {
        if (currentStageIndex < commodities.size() - 1 && srcDstMicroBatchCount <= microBatchSize) {
            int nextStageSrcId = commodities.get(currentStageIndex + 1 % commodities.size()).getLeft();
            int nextStageTargetId = commodities.get(currentStageIndex + 1 % commodities.size()).getRight();
            triggerNewFlow(job, currentStageIndex, ImmutablePair.of(nextStageSrcId, nextStageTargetId), nextStartTime);
            return true;
        }
        return srcDstMicroBatchCount < microBatchSize;
    }
}
