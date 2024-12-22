package ch.ethz.systems.floodns.ext.basicsim.schedule;

import ch.ethz.systems.floodns.core.Event;
import ch.ethz.systems.floodns.core.Simulator;
import ch.ethz.systems.floodns.ext.basicsim.topology.Topology;
import ch.ethz.systems.floodns.ext.routing.TopologyRoutingStrategy;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public class LinkFailureSchedule {

    private final List<LinkFailureScheduleEntry> entries;
    private final Topology topology;

    public LinkFailureSchedule(String failedLinksFilename, Topology topology, long simulationEndTimeNs) {
        this.entries = new ArrayList<>();
        this.topology = topology;

        try {
            FileReader input = new FileReader(failedLinksFilename);
            BufferedReader br = new BufferedReader(input);

            // Go over lines one-by-one
            String line;
            while ((line = br.readLine()) != null) {
                line = line.trim();
                String[] spl = line.split(" ", -1);

                // Columns are src node ID, dst node ID, failure time (ns), recovery time (ns) separated by space
                if (spl.length != 4) {
                    throw new IllegalArgumentException("File contains line which is not 2 columns: " + line);
                }

                int u = Integer.parseInt(spl[0]);
                int v = Integer.parseInt(spl[1]);
                entries.add(new LinkFailureScheduleEntry(topology.getNetwork(), u, v, 0, simulationEndTimeNs));
                entries.add(new LinkFailureScheduleEntry(topology.getNetwork(), v, u, 0, simulationEndTimeNs));
            }

            // Close file stream
            br.close();
        } catch (IOException e) {
            System.out.println("Could not read schedule: " + failedLinksFilename);
            e.printStackTrace();
        }
    }

    public List<LinkFailureScheduleEntry> getEntries() {
        return entries;
    }

    public List<Event> getEvents(Simulator simulator, TopologyRoutingStrategy topologyRoutingStrategy) {
        TrafficSchedule trafficSchedule = new TrafficSchedule(simulator, topology.getNetwork(), topologyRoutingStrategy);
        for (LinkFailureScheduleEntry entry : entries) {
            trafficSchedule.addLinkEvent(entry);
        }
        return trafficSchedule.getEvents();
    }

}
