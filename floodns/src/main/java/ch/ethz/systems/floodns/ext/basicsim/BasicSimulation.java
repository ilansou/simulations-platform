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

package ch.ethz.systems.floodns.ext.basicsim;

import ch.ethz.systems.floodns.core.Aftermath;
import ch.ethz.systems.floodns.core.Network;
import ch.ethz.systems.floodns.core.Simulator;
import ch.ethz.systems.floodns.ext.allocator.SimpleMmfAllocator;
import ch.ethz.systems.floodns.ext.basicsim.schedule.JobEpochSchedule;
import ch.ethz.systems.floodns.ext.basicsim.schedule.LinkFailureSchedule;
import ch.ethz.systems.floodns.ext.basicsim.schedule.NodeFailureSchedule;
import ch.ethz.systems.floodns.ext.basicsim.topology.FileToTopologyConverter;
import ch.ethz.systems.floodns.ext.basicsim.topology.Topology;
import ch.ethz.systems.floodns.ext.logger.file.FileLoggerFactory;
import ch.ethz.systems.floodns.ext.routing.*;
import org.apache.commons.io.output.TeeOutputStream;

import java.io.*;
import java.util.Random;

public class BasicSimulation {

    public static void main(String[] args) {
        if (args.length != 1) {
            throw new IllegalArgumentException("Usage: java -jar floodns-basic-sim.jar [run directory]");
        }
        System.out.println("Starting simulation with run directory: " + args[0]);
        BasicSimulation.simulate(args[0]);
    }

    private static void simulate(String runDirectory) {

        try {

            // Check run directory exists
            File f = new File(runDirectory);
            if (!f.exists() || !f.isDirectory()) {
                throw new IllegalArgumentException("Run directory does not exist: " + runDirectory);
            }
            String logFolderPath = runDirectory + "/logs_floodns";
            new File(logFolderPath).mkdirs();
            FileOutputStream fosOut = new FileOutputStream(logFolderPath + "/stdout.log");
            FileOutputStream fosErr = new FileOutputStream(logFolderPath + "/stderr.log");
            TeeOutputStream customOut = new TeeOutputStream(System.out, fosOut);
            TeeOutputStream customErr = new TeeOutputStream(System.err, fosErr);
            System.setOut(new PrintStream(customOut));
            System.setErr(new PrintStream(customErr));

            // Config
            String configPath = runDirectory + "/config_floodns.properties";
            File configFile = new File(configPath);
            if (!configFile.exists()) {
                configPath = runDirectory + "/config.properties";
                configFile = new File(configPath);
                if (!configFile.exists()) {
                    throw new IllegalArgumentException("Config file does not exist: " + configPath);
                }
            }
            FileInputStream fileInputStream = new FileInputStream(configPath);
            NoDuplicatesProperties config = new NoDuplicatesProperties();
            config.load(fileInputStream);
            fileInputStream.close();
            config.validate(new String[]{
                    "filename_topology", "filename_schedule",
                    "simulation_end_time_ns", "simulation_seed",
                    "job_base_dir_schedule", "routing_strategy",
                    "num_failed_nodes"
            });

            // Base simulation properties
            long simulationEndTimeNs = config.getPositiveLongOrFail("simulation_end_time_ns");
            long simulationSeed = config.getPositiveLongOrFail("simulation_seed");
            Random simulationRandom = new Random(simulationSeed);

            // Topology
            Topology topology = FileToTopologyConverter.convert(
                    runDirectory + "/" + config.getStringOrFail("filename_topology")
            );
            Network network = topology.getNetwork();

            // Initialize simulator
            Simulator simulator = new Simulator();
            FileLoggerFactory loggerFactory = new FileLoggerFactory(simulator, logFolderPath);
            Aftermath aftermath = new SimpleMmfAllocator(simulator, network);
            simulator.setup(network, aftermath, loggerFactory);

            // Jobs Schedule
            String jobsBaseDir = config.getStringOrFail("job_base_dir_schedule");
            JobEpochSchedule jobEpochSchedule = new JobEpochSchedule(jobsBaseDir, topology, simulationEndTimeNs);

            // Create link failure events / node failure events
            long numFailedNodes = config.getPositiveLongOrFail("num_failed_nodes");

            // Routing Strategy
            switch (config.getStringOrFail("routing_strategy")) {
                case "ecmp":
                    EcmpRoutingStrategy ecmpRoutingStrategy = new EcmpRoutingStrategy(simulator, topology, new Random(simulationRandom.nextLong()));
                    simulator.insertEvents(jobEpochSchedule.getEvents(simulator, ecmpRoutingStrategy));
                    createNodeFailureEvents(numFailedNodes, simulator, topology, ecmpRoutingStrategy, simulationEndTimeNs);
                    simulator.setRoutingStrategy(ecmpRoutingStrategy);
                    break;
                case "mcvlc":
                    McvlcRoutingStrategy mcvlcRoutingStrategy = new McvlcRoutingStrategy(simulator, topology);
                    simulator.insertEvents(jobEpochSchedule.getEvents(simulator, mcvlcRoutingStrategy));
                    createNodeFailureEvents(numFailedNodes, simulator, topology, mcvlcRoutingStrategy, simulationEndTimeNs);
                    simulator.setRoutingStrategy(mcvlcRoutingStrategy);
                    break;
                case "edge_coloring":
                    EdgeColoringRoutingStrategy edgeColoringRoutingStrategy = new EdgeColoringRoutingStrategy(simulator, topology, runDirectory);
                    simulator.insertEvents(jobEpochSchedule.getEvents(simulator, edgeColoringRoutingStrategy));
                    createNodeFailureEvents(numFailedNodes, simulator, topology, edgeColoringRoutingStrategy, simulationEndTimeNs);
                    simulator.setRoutingStrategy(edgeColoringRoutingStrategy);
                    break;
                case "ilp_solver":
                    IlpSolverRoutingStrategy ilpSolverRoutingStrategy = new IlpSolverRoutingStrategy(simulator, topology, runDirectory);
                    simulator.insertEvents(jobEpochSchedule.getEvents(simulator, ilpSolverRoutingStrategy));
                    createNodeFailureEvents(numFailedNodes, simulator, topology, ilpSolverRoutingStrategy, simulationEndTimeNs);
                    simulator.setRoutingStrategy(ilpSolverRoutingStrategy);
                    break;
                case "simulated_annealing":
                    SimulatedAnnealingRoutingStrategy simulatedAnnealingRoutingStrategy = new SimulatedAnnealingRoutingStrategy(simulator, topology, new Random(simulationRandom.nextLong()));
                    simulator.insertEvents(jobEpochSchedule.getEvents(simulator, simulatedAnnealingRoutingStrategy));
                    createNodeFailureEvents(numFailedNodes, simulator, topology, simulatedAnnealingRoutingStrategy, simulationEndTimeNs);
                    simulator.setRoutingStrategy(simulatedAnnealingRoutingStrategy);
                    break;
                default:
                    throw new IllegalArgumentException("Unknown routing strategy: " + config.getStringOrFail("routing_strategy"));
            }

            // Run
            simulator.run(simulationEndTimeNs);

        } catch (IOException e) {
            throw new IllegalArgumentException(e);
        }

    }

    private static void createLinkFailureEvents(double linkFailureRate, String jobsBaseDir, Simulator simulator, Topology topology, TopologyRoutingStrategy topologyRoutingStrategy, long simulationEndTimeNs) {
        if (linkFailureRate > 0.0) {
            String failedLinksFilename = jobsBaseDir + "/failed_links_" + linkFailureRate + ".txt";
            LinkFailureSchedule linkFailureSchedule = new LinkFailureSchedule(failedLinksFilename, topology, simulationEndTimeNs);
            simulator.insertEvents(linkFailureSchedule.getEvents(simulator, topologyRoutingStrategy));
        }
    }

    private static void createNodeFailureEvents(long numFailedNodes, Simulator simulator, Topology topology, RoutingStrategy routingStrategy, long simulationEndTimeNs) {
        if (numFailedNodes > 0) {
            NodeFailureSchedule nodeFailureSchedule = new NodeFailureSchedule(numFailedNodes, topology, simulationEndTimeNs);
            simulator.insertEvents(nodeFailureSchedule.getEvents(simulator, routingStrategy));
        }
    }

}
