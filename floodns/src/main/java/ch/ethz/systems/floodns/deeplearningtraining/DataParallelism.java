package ch.ethz.systems.floodns.deeplearningtraining;

import ch.ethz.systems.floodns.core.Connection;
import ch.ethz.systems.floodns.core.Node;
import ch.ethz.systems.floodns.ext.basicsim.schedule.JobEpochStartEvent;
import ch.ethz.systems.floodns.ext.routing.CentralizedRoutingStrategy;
import org.apache.commons.lang3.tuple.ImmutablePair;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

public class DataParallelism {

    private final Map<Integer, Set<ImmutablePair<Integer, Integer>>> stageCommodities;
    private final Map<ImmutablePair<Integer, Integer>, Integer> commoditiesToStage;
    private final Map<Integer, Integer> stageTotalFlows;
    private final Map<Integer, Integer> stageFinishedFlows;
    private final Map<Integer, Integer> stageRingSize;
    private final Map<Integer, Boolean> stageAllReduceFinished;

    public DataParallelism(Map<Integer, Set<ImmutablePair<Integer, Integer>>> stageCommodities) {
        this.stageCommodities = new HashMap<>(stageCommodities);
        this.commoditiesToStage = new HashMap<>();
        this.stageTotalFlows = new HashMap<>();
        this.stageFinishedFlows = new HashMap<>();
        this.stageRingSize = new HashMap<>();
        this.stageAllReduceFinished = new HashMap<>();
        for (Map.Entry<Integer, Set<ImmutablePair<Integer, Integer>>> entry : stageCommodities.entrySet()) {
            int stage = entry.getKey();
            Set<ImmutablePair<Integer, Integer>> commodities = entry.getValue();
            int nodeTotalAllReduceFlows = 2 * (commodities.size() - 1);
            this.stageTotalFlows.put(stage, commodities.size() * nodeTotalAllReduceFlows);
            this.stageFinishedFlows.put(stage, 0);
            this.stageRingSize.put(stage, commodities.size());
            this.stageAllReduceFinished.put(stage, false);
            for (ImmutablePair<Integer, Integer> commodity : commodities) {
                commoditiesToStage.put(commodity, stage);
            }
        }
    }

    public int update(Job job, Connection connection) {
        int stageIndex = commoditiesToStage.get(ImmutablePair.of(connection.getSrcNodeId(), connection.getDstNodeId()));
        stageFinishedFlows.put(stageIndex, stageFinishedFlows.get(stageIndex) + 1);
        int numFinishedFlows = stageFinishedFlows.get(stageIndex);
        int totalFlows = stageTotalFlows.get(stageIndex);
        if (numFinishedFlows % stageRingSize.get(stageIndex) == 0) {
            boolean isStageAllReduceFinished = numFinishedFlows >= totalFlows;
            stageAllReduceFinished.put(stageIndex, isStageAllReduceFinished);
            boolean isAllReduceFinished = stageAllReduceFinished.values().stream().allMatch(Boolean::booleanValue);
            if (!isStageAllReduceFinished) {
                stageCommodities.get(stageIndex).forEach(commodity -> ParallelismUtils.triggerNewFlow(job, stageIndex, commodity, 1));
            } else {
                job.getCurrentEpoch().setEndTime(stageIndex, job.getSimulator().getCurrentTime());
            }

            if (isAllReduceFinished) {
                closeEpoch(job);
                triggerNewEpoch(job);
            }
        }
        return stageIndex;
    }

    private void closeEpoch(Job job) {
        stageFinishedFlows.replaceAll((stage, finishedFlows) -> 0);
        stageAllReduceFinished.replaceAll((stage, allReduceFinished) -> false);
        if (job.getRoutingStrategy() instanceof CentralizedRoutingStrategy) {
            int numActiveJobs = job.getSimulator().getActiveJobs().size();
            if (numActiveJobs > 1) {
                CentralizedRoutingStrategy centralizedRoutingStrategy = (CentralizedRoutingStrategy) job.getRoutingStrategy();
                centralizedRoutingStrategy.determinePathAssignments();
                centralizedRoutingStrategy.getLogger().saveInfo(
                        centralizedRoutingStrategy.getAverageDuration(),
                        centralizedRoutingStrategy.getNumAssignedConnections()
                );
            }
        }
        JobEpoch epoch = job.getCurrentEpoch();
        Map<Integer, Long> stageDuration = new HashMap<>();
        epoch.getStageEndTime().forEach((stageIndex, endTime) -> {
            stageDuration.put(stageIndex, endTime - epoch.getStartTime());
        });
        job.getLogger().saveInfo(
                job.getJobId(),
                job.getEpochs().indexOf(epoch),
                epoch.getStartTime(),
                epoch.getStageEndTime(),
                stageDuration,
                job.getFlowSize(),
                epoch.getStageConnections(),
                -1
        );
    }

    private void triggerNewEpoch(Job job) {
        Map<Integer, Set<Connection>> stageConnections = new HashMap<>();
        job.getStageCommoditiesMap().forEach((stage, commodities) -> {
            stageConnections.putIfAbsent(stage, new HashSet<>());
            commodities.forEach(commodity -> {
                Node srcNode = job.getNetwork().getNode(commodity.getLeft());
                Node dstNode = job.getNetwork().getNode(commodity.getRight());
                Connection connection = new Connection(job.getSimulator(), srcNode, dstNode, job.getFlowSize(), job.getJobId());
                stageConnections.get(stage).add(connection);
            });
        });
        JobEpochStartEvent jobEpochStartEvent = new JobEpochStartEvent(job.getSimulator(), job.getComputeTime(), stageConnections, job.getRoutingStrategy(), job.getJobId());
        job.getSimulator().insertEvents(jobEpochStartEvent);
        job.setComputeMode(true);
    }

    @Override
    public String toString() {
        return "DataParallelism[" +
                "stageCommodities=" + stageCommodities +
                ", commoditiesToStage=" + commoditiesToStage +
                ", stageTotalFlows=" + stageTotalFlows +
                ", stageFinishedFlows=" + stageFinishedFlows +
                ", stageRingSize=" + stageRingSize +
                ", stageAllReduceFinished=" + stageAllReduceFinished +
                ']';
    }
}
