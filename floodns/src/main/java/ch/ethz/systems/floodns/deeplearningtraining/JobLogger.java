package ch.ethz.systems.floodns.deeplearningtraining;

import ch.ethz.systems.floodns.core.Connection;
import ch.ethz.systems.floodns.core.Simulator;

import java.util.HashMap;
import java.util.Map;
import java.util.Set;

public abstract class JobLogger {

    // Simulator handle
    protected final Simulator simulator;

    // Properties
    protected final int jobId;
    private final Job job;
    // Change track variables
    private boolean isInfoSavingEnabled;

    protected JobLogger(Simulator simulator, Job job) {
        this.simulator = simulator;

        // Properties
        this.jobId = job.getJobId();
        this.job = job;
        this.isInfoSavingEnabled = true;
    }

    /**
     * Enable/disable logging the info of flows.
     *
     * @param enabled True iff logging enabled
     */
    public void setInfoSavingEnabled(boolean enabled) {
        this.isInfoSavingEnabled = enabled;
    }

    /**
     * Final flush of logged state.
     */
    public final void finalFlush(long runtime) {
        if (isInfoSavingEnabled) {
            JobEpoch lastEpoch = job.getCurrentEpoch();
            Map<Integer, Long> stageEndTime = lastEpoch.getStageEndTime();
            Map<Integer, Long> stageDuration = new HashMap<>();
            lastEpoch.getStageConnections().keySet().forEach(stageIndex -> {
                if (stageEndTime.get(stageIndex) == -1) {
                    stageEndTime.put(stageIndex, simulator.getCurrentTime());
                    stageDuration.put(stageIndex, simulator.getCurrentTime() - lastEpoch.getStartTime());
                } else {
                    stageDuration.put(stageIndex, stageEndTime.get(stageIndex) - lastEpoch.getStartTime());
                }
            });
            saveInfo(
                    jobId,
                    job.getEpochs().indexOf(lastEpoch),
                    lastEpoch.getStartTime(),
                    stageEndTime,
                    stageDuration,
                    lastEpoch.getFlowSize(),
                    lastEpoch.getStageConnections(),
                    runtime
            );
        }
    }

    /**
     * Save the final flow info.
     *
     * @param jobId            Job identifier
     * @param epoch            Epoch number
     * @param startTime        Start time
     * @param stageEndTime     End time of each stage
     * @param stageDuration    Duration of each stage
     * @param flowSize         Size of the flow in bytes
     * @param stageConnections Stage connections map (stage index -> connections)
     * @param runtime          Runtime of the simulation
     */
    protected abstract void saveInfo(int jobId, int epoch, long startTime, Map<Integer, Long> stageEndTime, Map<Integer, Long> stageDuration, double flowSize, Map<Integer, Set<Connection>> stageConnections, long runtime);
}
