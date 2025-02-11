package ch.ethz.systems.floodns.deeplearningtraining;

import ch.ethz.systems.floodns.core.Connection;

import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

public class JobEpoch {

    private final long startTime;
    private final double flowSize;
    private final Map<Integer, Set<Connection>> stageConnections;
    private final Map<Integer, Long> stageEndTime;

    public JobEpoch(long startTime, double flowSize, Map<Integer, Set<Connection>> connections) {
        this.startTime = startTime;
        this.flowSize = flowSize;
        this.stageConnections = new HashMap<>(connections);
        this.stageEndTime = new HashMap<>();
        connections.keySet().forEach(stage -> stageEndTime.put(stage, -1L));
    }

    public JobEpoch(long startTime, JobEpoch other, Map<Integer, Set<Connection>> connections) {
        this.startTime = startTime;
        this.flowSize = other.getFlowSize();
        this.stageConnections = new HashMap<>(connections);
        this.stageEndTime = new HashMap<>();
        connections.keySet().forEach(stage -> stageEndTime.put(stage, -1L));
    }

    public long getStartTime() {
        return startTime;
    }

    public Map<Integer, Long> getStageEndTime() {
        return stageEndTime;
    }

    public void setEndTime(int stage, long endTime) {
        stageEndTime.put(stage, endTime);
    }

    public double getFlowSize() {
        return flowSize;
    }

    public Map<Integer, Set<Connection>> getStageConnections() {
        return stageConnections;
    }

    public int getConnectionStage(Connection connection) {
        for (Map.Entry<Integer, Set<Connection>> entry : stageConnections.entrySet()) {
            if (entry.getValue().contains(connection)) {
                return entry.getKey();
            }
        }
        throw new IllegalArgumentException("Connection " + connection.getConnectionId() + " not found in any stage of epoch " + this);
    }

    @Override
    public String toString() {
        StringBuilder result = new StringBuilder("Epoch[");
        result.append("startTime=")
                .append(startTime);
        for (Map.Entry<Integer, Long> entry : stageEndTime.entrySet()) {
            result.append(", stage=[")
                    .append(entry.getKey())
                    .append(", endTime=")
                    .append(entry.getValue())
                    .append(", connections=")
                    .append(stageConnections.get(entry.getKey()).stream().map(Connection::getConnectionId).collect(Collectors.toList()))
                    .append("]");
        }
        result.append(", flowSize=")
                .append(flowSize)
                .append("]");
        return result.toString();
    }
}
