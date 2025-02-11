package ch.ethz.systems.floodns.deeplearningtraining;

import ch.ethz.systems.floodns.core.AcyclicPath;
import ch.ethz.systems.floodns.core.Connection;
import ch.ethz.systems.floodns.core.Network;
import ch.ethz.systems.floodns.core.Simulator;
import ch.ethz.systems.floodns.ext.basicsim.schedule.JobEpochScheduleEntry;
import ch.ethz.systems.floodns.ext.routing.RoutingStrategy;
import org.apache.commons.lang3.tuple.ImmutablePair;

import java.util.*;

public class Job {

    private final int jobId;
    private final String modelName;
    private final String parallelizationType;
    private final List<JobEpoch> epochs;
    private final Map<ImmutablePair<Integer, Integer>, List<Connection>> commoditiesConnectionMap;
    private final Map<ImmutablePair<Integer, Integer>, AcyclicPath> commoditiesPathMap;
    private final long startTime;
    private final int numMiniBatches;
    private final int microBatchSize;
    private final Map<Integer, Set<ImmutablePair<Integer, Integer>>> stageCommoditiesMap;
    private final double flowSize;  // in bits
    private final long computeTime;
    private final Simulator simulator;
    private final Network network;
    private final RoutingStrategy routingStrategy;
    private final JobLogger logger;
    private int currentEpoch;
    private DataParallelism dataParallelism;
    private PipelineParallelism pipelineParallelism;
    private HybridParallelism hybridParallelism;
    private boolean computeMode; // whether the job is in forward and backpropagation mode or in allreduce mode

    public Job(Simulator simulator, Network network, RoutingStrategy routingStrategy, JobEpochScheduleEntry entry) {
        this.simulator = simulator;
        this.network = network;
        this.routingStrategy = routingStrategy;
        this.jobId = entry.getJobId();
        this.modelName = entry.getModelName();
        this.parallelizationType = entry.getParallelizationType();
        this.flowSize = entry.getFlowSize();
        this.computeTime = entry.getComputeTimeNs();
        this.startTime = entry.getStartTimeNs();
        this.numMiniBatches = entry.getNumMiniBatches();
        this.microBatchSize = entry.getMicroBatchSize();
        this.currentEpoch = 0;
        this.computeMode = true;
        this.epochs = new ArrayList<>();
        this.commoditiesConnectionMap = new HashMap<>();
        this.commoditiesPathMap = new HashMap<>();
        this.stageCommoditiesMap = new HashMap<>();
        this.logger = simulator.getLoggerFactory().internalCreateJobLogger(this);
    }

    public void initWrapper() {
        switch (parallelizationType) {
            case "data_parallelism":
                initializeDataParallelismWrapper();
                break;
            case "pipeline_parallelism":
                initializePipelineParallelismWrapper(numMiniBatches);
                break;
            case "hybrid_parallelism":
                initializeHybridParallelism(numMiniBatches);
                break;
            default:
                throw new IllegalStateException("Unknown parallelization type: " + parallelizationType);
        }
    }

    private void initializeDataParallelismWrapper() {
        this.dataParallelism = new DataParallelism(stageCommoditiesMap);
    }

    private void initializePipelineParallelismWrapper(int microBatchSize) {
        this.pipelineParallelism = new PipelineParallelism(stageCommoditiesMap.get(-1), microBatchSize);
    }

    private void initializeHybridParallelism(int microBatchSize) {
        this.hybridParallelism = new HybridParallelism(stageCommoditiesMap, microBatchSize);
    }

    public void initializeEpoch(long startTime, Map<Integer, Set<Connection>> connections) {
        JobEpoch jobEpoch = new JobEpoch(startTime, flowSize, connections);
        epochs.add(jobEpoch);
        currentEpoch = epochs.size() - 1;
        computeMode = false;
    }

    public void update(Connection connection) {
        if (isFinished()) {
            return;
        }
        int stageIndex;
        switch (parallelizationType) {
            case "data_parallelism":
                stageIndex = dataParallelism.update(this, connection);
                break;
            case "pipeline_parallelism":
                stageIndex = pipelineParallelism.update(this, connection);
                break;
            case "hybrid_parallelism":
                stageIndex = hybridParallelism.update(this, connection);
                break;
            default:
                throw new IllegalStateException("Unknown parallelization type: " + parallelizationType);
        }
        epochs.get(currentEpoch).getStageConnections().get(stageIndex).add(connection);
    }

    public int getJobId() {
        return jobId;
    }

    public List<JobEpoch> getEpochs() {
        return epochs;
    }

    public JobEpoch getCurrentEpoch() {
        return epochs.get(currentEpoch);
    }

    public Map<ImmutablePair<Integer, Integer>, List<Connection>> getCommoditiesConnectionMap() {
        return commoditiesConnectionMap;
    }

    public Map<ImmutablePair<Integer, Integer>, AcyclicPath> getCommoditiesPathMap() {
        return commoditiesPathMap;
    }

    public Map<Integer, Set<ImmutablePair<Integer, Integer>>> getStageCommoditiesMap() {
        return stageCommoditiesMap;
    }

    public long getStartTime() {
        return startTime;
    }

    public long getComputeTime() {
        return computeTime;
    }

    public Simulator getSimulator() {
        return simulator;
    }

    public Network getNetwork() {
        return network;
    }

    public RoutingStrategy getRoutingStrategy() {
        return routingStrategy;
    }

    public JobLogger getLogger() {
        return logger;
    }

    public boolean isFinished() {
        return currentEpoch > 10;
    }

    public double getFlowSize() {
        return flowSize;
    }

    public boolean isComputeMode() {
        return computeMode;
    }

    public void setComputeMode(boolean computeMode) {
        this.computeMode = computeMode;
    }

    @Override
    public String toString() {
        String result = "Job#" + jobId + ", " + modelName +
                " [epochs=" + epochs +
                ", computeTime=" + computeTime +
                ", numMiniBatches=" + numMiniBatches +
                ", ";
        switch (parallelizationType) {
            case "pipeline_parallelism":
                result += pipelineParallelism.toString();
                break;
            case "data_parallelism":
                result += dataParallelism.toString();
                break;
            case "hybrid_parallelism":
                result += hybridParallelism.toString();
                break;
            default:
                throw new IllegalStateException("Unknown parallelization type: " + parallelizationType);
        }
        result += "]";
        return result;
    }

}
