package ch.ethz.systems.floodns.deeplearningtraining;

import ch.ethz.systems.floodns.core.Connection;
import org.apache.commons.lang3.tuple.ImmutablePair;

import java.util.*;

public class PipelineParallelism {

    private final Map<String, Integer> commodityMicroBatchCountMap;
    private final List<ImmutablePair<Integer, Integer>> forwardPipelineCommodities;
    private final List<ImmutablePair<Integer, Integer>> backpropPipelineCommodities;
    private final int totalFlows;
    private final int microBatchSize;
    private boolean forwardStep;


    public PipelineParallelism(Set<ImmutablePair<Integer, Integer>> commodities, int microBatchSize) {
        this.commodityMicroBatchCountMap = new HashMap<>();
        this.backpropPipelineCommodities = new ArrayList<>();
        this.forwardStep = true;
        this.totalFlows = 2 * commodities.size();
        this.microBatchSize = microBatchSize;

        this.forwardPipelineCommodities = new ArrayList<>(commodities);

        while (!commodities.isEmpty()) {
            ImmutablePair<Integer, Integer> commodity = commodities.iterator().next();
            backpropPipelineCommodities.add(new ImmutablePair<>(commodity.getRight(), commodity.getLeft()));
            String forward = commodity.getLeft() + "->" + commodity.getRight();
            String backprop = commodity.getRight() + "->" + commodity.getLeft();
            commodityMicroBatchCountMap.putIfAbsent(forward, 0);
            commodityMicroBatchCountMap.putIfAbsent(backprop, 0);
            commodities.remove(commodity);
        }
    }

    public void increaseSrcDstMicroBatchCount(int srcId, int targetId) {
        String key = srcId + "->" + targetId;
        int currentValue = commodityMicroBatchCountMap.get(key);
        commodityMicroBatchCountMap.put(key, currentValue + 1);
    }

    public void resetSrcDstMicroBatchCount() {
        commodityMicroBatchCountMap.replaceAll((k, v) -> 0);
    }

    public void toggleForwardStep() {
        forwardStep = !forwardStep;
    }

    public int getTotalFlows() {
        return totalFlows;
    }

    public int update(Job job, Connection connection) {
        int srcId = connection.getSrcNodeId(), targetId = connection.getDstNodeId();
        String key = srcId + "->" + targetId;
        increaseSrcDstMicroBatchCount(srcId, targetId);
        int srcDstMicroBatchCount = commodityMicroBatchCountMap.get(key);
        ImmutablePair<Integer, Integer> currentStage = new ImmutablePair<>(srcId, targetId);
        List<ImmutablePair<Integer, Integer>> tmpCommodities = forwardStep ? forwardPipelineCommodities : backpropPipelineCommodities;
        int currentStageIndex = tmpCommodities.indexOf(currentStage);
        long nextStartTime = job.getComputeTime();
        if (ParallelismUtils.isNotFinishedAllLayers(job, tmpCommodities, currentStageIndex, srcDstMicroBatchCount, microBatchSize, nextStartTime)) {
            return currentStageIndex;
        }

        if (forwardStep && currentStageIndex == tmpCommodities.size() - 1) {
            triggerFlows(job, currentStageIndex, backpropPipelineCommodities.get(0));
        } else if (!forwardStep && currentStageIndex == tmpCommodities.size() - 1) {
            Map<Integer, Set<Connection>> connections = new HashMap<>();
            connections.put(0, triggerFlows(job, currentStageIndex, forwardPipelineCommodities.get(0)));
            // TODO: This works for Data Parallelism, need to extend for Pipeline Parallelism and Hybrid Parallelism
//            job.newEpoch(connections);
        }
        return currentStageIndex;
    }

    private Set<Connection> triggerFlows(Job job, int stageIndex, ImmutablePair<Integer, Integer> stage) {
        Set<Connection> connections = new HashSet<>();
        toggleForwardStep();
        resetSrcDstMicroBatchCount();
        for (int i = 0; i < microBatchSize; i++) {
            long nextStartTime = job.getComputeTime() + i * job.getComputeTime();
            Connection connection = ParallelismUtils.triggerNewFlow(job, stageIndex, stage, nextStartTime);
            connections.add(connection);
        }
        return connections;
    }

    @Override
    public String toString() {
        return "PipelineParallelism[" +
                "srcDstMicroBatchCount=" + commodityMicroBatchCountMap +
                ", forwardStep=" + forwardStep +
                ", totalFlows=" + totalFlows +
                ']';
    }
}
