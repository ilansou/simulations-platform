package ch.ethz.systems.floodns.ext.basicsim.schedule;

import ch.ethz.systems.floodns.core.Event;
import ch.ethz.systems.floodns.core.Simulator;
import ch.ethz.systems.floodns.ext.basicsim.topology.Topology;
import ch.ethz.systems.floodns.ext.routing.RoutingStrategy;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class NodeFailureSchedule {

    private final List<NodeFailureScheduleEntry> entries;
    private final Topology topology;

    public NodeFailureSchedule(long numFailedNodes, Topology topology, long simulationEndTimeNs) {
        this.entries = new ArrayList<>();
        this.topology = topology;
        List<Integer> coreIds = new ArrayList<>(topology.getDetails().getCoreNodeIds());
        Collections.reverse(coreIds);
        for (int i = 0; i < numFailedNodes; i++) {
            int nodeId = coreIds.get(i);
            entries.add(new NodeFailureScheduleEntry(topology.getNetwork(), nodeId, 0, simulationEndTimeNs));
        }
    }

    public List<NodeFailureScheduleEntry> getEntries() {
        return entries;
    }

    public List<Event> getEvents(Simulator simulator, RoutingStrategy routingStrategy) {
        TrafficSchedule trafficSchedule = new TrafficSchedule(simulator, topology.getNetwork(), routingStrategy);
        for (NodeFailureScheduleEntry entry : entries) {
            trafficSchedule.addNodeEvent(entry);
        }
        return trafficSchedule.getEvents();
    }
}
