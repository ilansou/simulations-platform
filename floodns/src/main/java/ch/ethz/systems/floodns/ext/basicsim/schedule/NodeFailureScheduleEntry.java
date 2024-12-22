package ch.ethz.systems.floodns.ext.basicsim.schedule;

import ch.ethz.systems.floodns.core.Network;
import ch.ethz.systems.floodns.core.Node;

public class NodeFailureScheduleEntry {

    private final Node node;
    private final long failureTimeNs;
    private final long recoveryTimeNs;

    public NodeFailureScheduleEntry(Network network, int nodeId, long failureTimeNs, long recoveryTimeNs) {
        this.node = network.getNode(nodeId);
        this.failureTimeNs = failureTimeNs;
        this.recoveryTimeNs = recoveryTimeNs;
    }

    public Node getNode() {
        return node;
    }

    public long getFailureTimeNs() {
        return failureTimeNs;
    }

    public long getRecoveryTimeNs() {
        return recoveryTimeNs;
    }
}
