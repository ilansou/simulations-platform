/*
 * The MIT License (MIT)
 *
 * Copyright (c) 2019 snkas
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

package ch.ethz.systems.floodns.ext.basicsim.schedule;

import ch.ethz.systems.floodns.core.Event;
import ch.ethz.systems.floodns.core.Simulator;
import ch.ethz.systems.floodns.ext.basicsim.topology.Topology;
import ch.ethz.systems.floodns.ext.routing.TopologyRoutingStrategy;
import org.apache.commons.lang3.tuple.ImmutablePair;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.*;
import java.util.function.Predicate;
import java.util.stream.Collectors;

public class JobEpochSchedule {

    private final List<JobEpochScheduleEntry> entries;
    private final Topology topology;

    public JobEpochSchedule(String baseDir, Topology topology, long simulationDurationNs) {
        this.entries = new ArrayList<>();
        this.topology = topology;

        File baseDirFile = new File(baseDir);
        if (!baseDirFile.exists() || !baseDirFile.isDirectory()) {
            throw new IllegalArgumentException("Base directory does not exist: " + baseDir);
        }
        File[] files = baseDirFile.listFiles();
        if (files == null) {
            throw new IllegalArgumentException("Could not list files in directory: " + baseDir);
        }

        Predicate<File> fileFilter = File::isFile;
        for (File file : Arrays.stream(files).filter(fileFilter).collect(Collectors.toList())) {
            try {
                createEntry(file, simulationDurationNs);
            } catch (IOException e) {
                System.out.println("Could not read schedule: " + file.getName());
                e.printStackTrace();
            }
        }
    }

    public List<JobEpochScheduleEntry> getEntries() {
        return entries;
    }

    public List<Event> getEvents(Simulator simulator, TopologyRoutingStrategy topologyRoutingStrategy) {
        TrafficSchedule trafficSchedule = new TrafficSchedule(simulator, topology.getNetwork(), topologyRoutingStrategy);
        for (JobEpochScheduleEntry entry : entries) {
            trafficSchedule.addJobEpochStartEvent(entry);
        }
        return trafficSchedule.getEvents();
    }


    private void createEntry(File file, long simulationDurationNs) throws IOException {
        // Open file stream
        String[] parts = file.getName().split("-");
        assert parts.length == 2;
        String modelName = parts[1].replace(".txt", "");
        FileReader input = new FileReader(file.getAbsolutePath());
        BufferedReader br = new BufferedReader(input);

        int jobId = Integer.parseInt(parts[0].split("_")[1]);

        long startTimeNs = 0;
        double flowSize = 0;    // in bits
        int numMiniBatches = 1;
        int microBatchSize = 8;
        long computeTimeNs = 0;
        int stageIndex;

        Set<Integer> tors = new HashSet<>();
        Map<Integer, Set<ImmutablePair<Integer, Integer>>> stageCommodities = new HashMap<>();

        // Go over lines one-by-one
        String line;
        while ((line = br.readLine()) != null) {
            line = line.trim();
            if (line.startsWith("#")) {
                continue;
            }
            String[] spl = line.split(" ", -1);

            // All 10 must be there
            if (spl.length != 8) {
                throw new IllegalArgumentException("File contains line which is not 7 columns: " + line);
            }

            int srcTorId = Integer.parseInt(spl[2]);
            int dstTorId = Integer.parseInt(spl[3]);
            tors.add(srcTorId);
            tors.add(dstTorId);

            int srcId = Integer.parseInt(spl[0]);
            int dstId = Integer.parseInt(spl[1]);
            stageIndex = Integer.parseInt(spl[7]);
            stageCommodities.putIfAbsent(stageIndex, new HashSet<>());
            stageCommodities.get(stageIndex).add(ImmutablePair.of(srcId, dstId));

            startTimeNs = Long.parseLong(spl[4]);
            flowSize = Long.parseLong(spl[5]) * 8;
            computeTimeNs = Long.parseLong(spl[6]);

            // Check node IDs
            if (topology.getDetails().isInvalidEndpoint(srcId)) {
                throw new IllegalArgumentException("Invalid from node ID: " + srcId);
            }
            if (topology.getDetails().isInvalidEndpoint(dstId)) {
                throw new IllegalArgumentException("Invalid to node ID: " + dstId);
            }
            if (srcId == dstId) {
                throw new IllegalArgumentException("Connection to itself at node ID: " + srcId);
            }

            // Check start time
            if (startTimeNs >= simulationDurationNs || startTimeNs + computeTimeNs >= simulationDurationNs) {
                throw new IllegalArgumentException("Job " + jobId + " has invalid start time " + startTimeNs + " >= " + simulationDurationNs);
            }
        }

        // Close file stream
        br.close();

        if (tors.size() < 2) {
            return;
        }

        // Add Job start event (this will throw all IllegalArgumentException if any of the inputs is invalid)
        JobEpochScheduleEntry entry = new JobEpochScheduleEntry(jobId, modelName, "data_parallelism", flowSize, startTimeNs, computeTimeNs, numMiniBatches, microBatchSize);
        entry.getStageCommodities().putAll(stageCommodities);
        entries.add(entry);
    }
}
