package ch.ethz.systems.floodns.deeplearningtraining;

import ch.ethz.systems.floodns.core.Connection;
import org.apache.commons.lang3.tuple.ImmutablePair;

import java.util.*;

public class HybridParallelism {

    private final Map<String, Integer> srcDstMicroBatchCountMap; // srcId -> targetId -> micro batch count (for pipelines parallelism)
    private final Map<Integer, Integer> acceleratorPipelineIndexMap;  // determine the pipelines index of an accelerator (host)
    private final Map<Integer, Integer> acceleratorPipelineLayerIndexMap; // determine the layer index of an accelerator (host)
    private final Map<Integer, List<Integer>> pipelineLayerToAcceleratorMap; // pipelines layer index -> accelerator (host) ids

    private final Map<Integer, List<ImmutablePair<Integer, Integer>>> forwardPipelineCommodities; // Pipeline index -> src dst pairs
    private final Map<Integer, List<ImmutablePair<Integer, Integer>>> backpropPipelineCommodities; // Pipeline index -> src dst pairs
    private final Map<Integer, List<ImmutablePair<Integer, Integer>>> dataParallelCommodities;  // Layer index -> src dst pairs

    private final Map<Integer, Boolean> pipelineForwardStepMap; // Pipeline index -> forward step
    private final Map<Integer, Boolean> dataParallelStepMap; // Layer index -> data parallel step
    private final int pipelineTotalFlows;
    private final int microBatchSize;
    private final Map<Integer, Integer> dataParallelFinishedFlowsMap;
    private final Map<Integer, Boolean> dataParallelFinishedStepMap;
    private int finishedPipelines = 0;
    private int dataParallelLayerTotalFlows = 0;
    private int dataParallelLayerRingSize = 0;

    public HybridParallelism(Map<Integer, Set<ImmutablePair<Integer, Integer>>> forwardPipelineCommodities, int microBatchSize) {
        this.srcDstMicroBatchCountMap = new HashMap<>();
        this.acceleratorPipelineIndexMap = new HashMap<>();
        this.acceleratorPipelineLayerIndexMap = new HashMap<>();
        this.pipelineLayerToAcceleratorMap = new HashMap<>();

        Map<Integer, List<ImmutablePair<Integer, Integer>>> forwardPipelineCommoditiesListMap = new HashMap<>();
        for (Map.Entry<Integer, Set<ImmutablePair<Integer, Integer>>> entry : forwardPipelineCommodities.entrySet()) {
            forwardPipelineCommoditiesListMap.put(entry.getKey(), new ArrayList<>(entry.getValue()));
        }
        this.forwardPipelineCommodities = new HashMap<>(forwardPipelineCommoditiesListMap);
        this.backpropPipelineCommodities = new HashMap<>();
        this.dataParallelCommodities = new HashMap<>();

        this.pipelineForwardStepMap = new HashMap<>();
        this.dataParallelStepMap = new HashMap<>();

        this.dataParallelFinishedFlowsMap = new HashMap<>();
        this.dataParallelFinishedStepMap = new HashMap<>();

        this.pipelineTotalFlows = 2 * this.forwardPipelineCommodities.get(0).size();
        this.microBatchSize = microBatchSize;

        forwardPipelineCommodities.forEach((ringId, commodities) -> {
            backpropPipelineCommodities.put(ringId, new ArrayList<>());
            pipelineForwardStepMap.put(ringId, true);

            List<ImmutablePair<Integer, Integer>> listCommodities = new ArrayList<>(commodities);
            for (int i = 0; i < listCommodities.size(); i++) {
                ImmutablePair<Integer, Integer> commodity = listCommodities.get(i);
                acceleratorPipelineIndexMap.put(commodity.getLeft(), ringId);
                acceleratorPipelineIndexMap.put(commodity.getRight(), ringId);

                acceleratorPipelineLayerIndexMap.put(commodity.getLeft(), 2 * i);
                acceleratorPipelineLayerIndexMap.put(commodity.getRight(), 2 * i + 1);

                pipelineLayerToAcceleratorMap.putIfAbsent(2 * i, new ArrayList<>());
                pipelineLayerToAcceleratorMap.putIfAbsent(2 * i + 1, new ArrayList<>());
                pipelineLayerToAcceleratorMap.get(2 * i).add(commodity.getLeft());
                pipelineLayerToAcceleratorMap.get(2 * i + 1).add(commodity.getRight());

                String forwardKey = "{" + commodity.getLeft() + "," + commodity.getRight() + "}";
                String backpropKey = "{" + commodity.getRight() + "," + commodity.getLeft() + "}";
                srcDstMicroBatchCountMap.put(forwardKey, 0);
                srcDstMicroBatchCountMap.put(backpropKey, 0);
            }

            for (int i = listCommodities.size() - 1; i >= 0; i--) {
                ImmutablePair<Integer, Integer> commodity = listCommodities.get(i);
                ImmutablePair<Integer, Integer> reverseCommodity = new ImmutablePair<>(commodity.getRight(), commodity.getLeft());
                backpropPipelineCommodities.get(ringId).add(reverseCommodity);
            }
        });
        initializeDataParallelCommodities();
    }

    private void initializeDataParallelCommodities() {
        for (int layer : pipelineLayerToAcceleratorMap.keySet()) {
            dataParallelCommodities.put(layer, new ArrayList<>());
            dataParallelFinishedFlowsMap.put(layer, 0);
            dataParallelFinishedStepMap.put(layer, false);
            List<Integer> accelerators = pipelineLayerToAcceleratorMap.get(layer);
            for (int i = 0; i < accelerators.size(); i++) {
                int j = (i + 1) % accelerators.size();
                int src = accelerators.get(i);
                int dst = accelerators.get(j);
                ImmutablePair<Integer, Integer> dataParallelCommodity = new ImmutablePair<>(src, dst);
                dataParallelCommodities.get(layer).add(dataParallelCommodity);
            }
        }
        dataParallelLayerRingSize = dataParallelCommodities.get(0).size();
        dataParallelLayerTotalFlows = 2 * dataParallelLayerRingSize * (dataParallelLayerRingSize - 1);
    }

    public void increaseSrcDstMicroBatchCount(int srcId, int targetId) {
        String key = "{" + srcId + "," + targetId + "}";
        int currentValue = srcDstMicroBatchCountMap.get(key);
        srcDstMicroBatchCountMap.put(key, currentValue + 1);
    }

    public void increaseDataParallelFinishedFlows(int layer) {
        int currentValue = dataParallelFinishedFlowsMap.get(layer);
        dataParallelFinishedFlowsMap.put(layer, currentValue + 1);
    }

    public void resetSrcDstMicroBatchCount() {
        srcDstMicroBatchCountMap.replaceAll((k, v) -> 0);
    }

    public void toggleForwardStep(int pipelineIndex) {
        pipelineForwardStepMap.put(pipelineIndex, !pipelineForwardStepMap.get(pipelineIndex));
    }

    public void toggleDataParallelStep(int layer) {
        dataParallelStepMap.put(layer, !dataParallelStepMap.get(layer));
    }

    public int getTotalFlows() {
        return pipelineTotalFlows + dataParallelLayerTotalFlows;
    }

    /**
     * Update the state of the hybrid parallelism.
     * This method is called when a flow finishes.
     * If the flow is part of a pipelines, the next flow is triggered.
     * If the flow is part of a data parallel step, wait until all flows of the current ring are finished.
     * Otherwise, trigger the next epoch.
     *
     * @param job      the Job instance to update
     * @param srcId    the source ID to use for the update
     * @param targetId the target ID to use for the update
     */
    public int update(Job job, Connection connection) {
        int srcId = connection.getSrcNodeId(), targetId = connection.getDstNodeId();
        int srcLayer = acceleratorPipelineLayerIndexMap.get(srcId);
        int dstLayer = acceleratorPipelineLayerIndexMap.get(targetId);
        int pipelineIndex = acceleratorPipelineIndexMap.get(srcId);
        boolean isDataParallelFlow = srcLayer == dstLayer;
        boolean isFinishedDataParallelStep = dataParallelFinishedStepMap.values().stream().allMatch(Boolean::booleanValue);
        if (isDataParallelFlow) {
            triggerDataParallel(job, srcLayer);
            return pipelineIndex;
        } else if (isFinishedDataParallelStep) {
            triggerNewEpoch(job);
            return pipelineIndex;
        }
        triggerPipeline(job, srcId, targetId, pipelineIndex);
        return pipelineIndex;
    }

    private void triggerNewEpoch(Job job) {
        Map<Integer, Set<Connection>> connections = new HashMap<>();
        forwardPipelineCommodities.keySet().forEach(pipelineIndex -> {
            Set<Connection> pipelineConnections = triggerPipelineFlows(job, forwardPipelineCommodities.get(pipelineIndex).get(0), pipelineIndex);
            connections.put(pipelineIndex, pipelineConnections);
        });
        dataParallelCommodities.keySet().forEach(this::toggleDataParallelStep);
        // TODO: This works for Data Parallelism, need to extend for Pipeline Parallelism and Hybrid Parallelism
//        job.newEpoch(connections);
    }

    private void triggerPipeline(Job job, int srcId, int targetId, int pipelineIndex) {
        String key = "{" + srcId + "," + targetId + "}";
        boolean isForwardStep = pipelineForwardStepMap.get(pipelineIndex);
        increaseSrcDstMicroBatchCount(srcId, targetId);
        int srcDstMicroBatchCount = srcDstMicroBatchCountMap.get(key);
        ImmutablePair<Integer, Integer> currentStage = new ImmutablePair<>(srcId, targetId);
        List<ImmutablePair<Integer, Integer>> tmpCommodities = isForwardStep ?
                forwardPipelineCommodities.get(pipelineIndex) : backpropPipelineCommodities.get(pipelineIndex);
        int currentStageIndex = tmpCommodities.indexOf(currentStage);
        long nextStartTime = job.getComputeTime();
        if (ParallelismUtils.isNotFinishedAllLayers(job, tmpCommodities, currentStageIndex, srcDstMicroBatchCount, microBatchSize, nextStartTime)) {
            return;
        }

        if (isForwardStep && currentStageIndex == tmpCommodities.size() - 1) {
            triggerPipelineFlows(job, backpropPipelineCommodities.get(pipelineIndex).get(0), pipelineIndex);
        } else if (!isForwardStep && currentStageIndex == tmpCommodities.size() - 1) {
            finishedPipelines++;
            if (finishedPipelines % forwardPipelineCommodities.size() == 0) {
                triggerDataParallelFlows(job);
            }
        }
    }

    private void triggerDataParallel(Job job, int layer) {
        increaseDataParallelFinishedFlows(layer);
        int currentFinishedFlows = dataParallelFinishedFlowsMap.get(layer);
        if (currentFinishedFlows % dataParallelLayerRingSize == 0) {
            boolean isAllReduceFinished = currentFinishedFlows == dataParallelLayerTotalFlows;
            long nextStartTime = isAllReduceFinished ? job.getComputeTime() : 1;
            dataParallelCommodities.get(layer).forEach(commodity -> {
                ParallelismUtils.triggerNewFlow(job, layer, commodity, nextStartTime);
            });
            dataParallelFinishedStepMap.put(layer, isAllReduceFinished);
        }
    }

    private Set<Connection> triggerPipelineFlows(Job job, ImmutablePair<Integer, Integer> stage, int pipelineIndex) {
        toggleForwardStep(pipelineIndex);
        resetSrcDstMicroBatchCount();
        Set<Connection> connections = new HashSet<>();
        for (int i = 0; i < microBatchSize; i++) {
            long nextStartTime = job.getComputeTime() + i * job.getComputeTime();
            Connection connection = ParallelismUtils.triggerNewFlow(job, pipelineIndex, stage, nextStartTime);
            connections.add(connection);
        }
        return connections;
    }

    /*
     * Loop through all pipelines and create all reduce flows between same layers in different pipelines.
     */
    private void triggerDataParallelFlows(Job job) {
        finishedPipelines = 0;
        dataParallelCommodities.forEach((layerIndex, commodities) -> {
            commodities.forEach(commodity -> {
                ParallelismUtils.triggerNewFlow(job, layerIndex, commodity, 1);
            });
        });
    }

    @Override
    public String toString() {
        return "HybridParallelism[" +
                "srcDstMicroBatchCountMap=" + srcDstMicroBatchCountMap +
                ", acceleratorPipelineIndexMap=" + acceleratorPipelineIndexMap +
                ", acceleratorPipelineLayerIndexMap=" + acceleratorPipelineLayerIndexMap +
                ", pipelineForwardStepMap=" + pipelineForwardStepMap +
                ", dataParallelStepMap=" + dataParallelStepMap +
                ", dataParallelFinishedFlowsMap=" + dataParallelFinishedFlowsMap +
                ", dataParallelFinishedStepMap=" + dataParallelFinishedStepMap +
                ", pipelineTotalFlows=" + pipelineTotalFlows +
                ", dataParallelLayerTotalFlows=" + dataParallelLayerTotalFlows +
                ", dataParallelLayerRingSize=" + dataParallelLayerRingSize +
                ']';
    }
}
