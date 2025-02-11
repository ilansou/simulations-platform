package ch.ethz.systems.floodns.ext.basicsim.schedule;

import ch.ethz.systems.floodns.core.Link;
import ch.ethz.systems.floodns.core.Network;

public class LinkFailureScheduleEntry {

    private final Link link;
    private final long failureTimeNs;
    private final long recoveryTimeNs;

    public LinkFailureScheduleEntry(Network network, int from, int to, long failureTimeNs, long recoveryTimeNs) {
        this.link = network.getPresentLinksBetween(from, to).get(0);
        this.failureTimeNs = failureTimeNs;
        this.recoveryTimeNs = recoveryTimeNs;
    }

    public Link getLink() {
        return link;
    }

    public long getFailureTimeNs() {
        return failureTimeNs;
    }

    public long getRecoveryTimeNs() {
        return recoveryTimeNs;
    }
}
