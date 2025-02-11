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

package ch.ethz.systems.floodns.ext.routing;

import ch.ethz.systems.floodns.core.*;
import ch.ethz.systems.floodns.ext.basicsim.topology.Topology;
import ch.ethz.systems.floodns.ext.basicsim.topology.TopologyDetails;
import ch.ethz.systems.floodns.ext.graphutils.FloydWarshallAlgorithm;
import ch.ethz.systems.floodns.ext.graphutils.YenTopKspAlgorithmWrapper;
import org.apache.commons.lang3.tuple.ImmutablePair;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import java.util.*;

public class RoutingUtility {

    // Class logger
    private static final Logger logger = LogManager.getLogger(RoutingUtility.class);

    private RoutingUtility() {
        // Cannot be instantiated
    }

    /**
     * Convert the potentially cyclic path to an acyclic variant.
     * <p>
     * E.g.
     * 0 &rarr; 1 &rarr; 2 &rarr; 3 &rarr; 1 &rarr; 4
     * becomes
     * 0 &rarr; 1 &rarr; 4
     *
     * @param potentialCyclicPath Potentially acyclic path
     * @return Acyclic path
     */
    public static AcyclicPath convertToAcyclic(List<Link> potentialCyclicPath) {

        // Iterate over acyclic path, reducing cycles to nothing
        Map<Integer, Integer> visitToIndex = new HashMap<>();
        List<Link> currentLinks = new ArrayList<>();
        visitToIndex.put(potentialCyclicPath.get(0).getFrom(), -1);
        for (Link link : potentialCyclicPath) {

            // Cycle detected
            if (visitToIndex.containsKey(link.getTo())) {

                // Indices of links that are still valid
                int untilIdxValid = visitToIndex.get(link.getTo());

                // Remove all links which are creating the cycle
                for (int i = currentLinks.size() - 1; i > untilIdxValid; i--) {
                    Link l = currentLinks.get(i);
                    currentLinks.remove(i);
                    visitToIndex.remove(l.getTo());
                }

                // No cycle detected
            } else {
                currentLinks.add(link);
                visitToIndex.put(link.getTo(), currentLinks.size() - 1);
            }

        }

        // Finally create acyclic path
        AcyclicPath path = new AcyclicPath();
        path.addAll(currentLinks);
        return path;

    }

    /**
     * Determine the next-hop routing state for ECMP purposes.
     * It ONLY sets the next hops for all switches towards the ToRs.
     * It will have zero entries towards server or non-ToR switch nodes.
     *
     * @param topology        Topology instance
     * @param onlyTowardsToRs True iff you only want switches to have state towards ToRs,
     *                        if false, then it will have state towards all switches
     * @return Next-hop possibilities for every (current, destination) node-pair
     */
    public static Map<ImmutablePair<Integer, Integer>, List<Link>> determineEcmpRoutingStateSwitches(Topology topology, boolean onlyTowardsToRs) {

        // Topology parts
        Network network = topology.getNetwork();
        TopologyDetails details = topology.getDetails();
        Map<ImmutablePair<Integer, Integer>, List<Link>> nextHopPossibilities = new HashMap<>();

        // Shortest path length
        logger.info("ECMP ROUTING CALCULATION");
        logger.info("  > Calculating Floyd-Warshall");
        int[][] shortestPathLen = new FloydWarshallAlgorithm(network).calculateShortestPaths();
        logger.info("  > Setting next hops for each switch towards each ToR\n");
        Set<Integer> switches = new HashSet<>(details.getSwitchNodeIds()); // Only for switches
        Set<Integer> towardsIds;
        if (onlyTowardsToRs) {
            towardsIds = new HashSet<>(details.getTorNodeIds()); // ... only towards ToRs
        } else {
            towardsIds = new HashSet<>(details.getSwitchNodeIds()); // ... towards all switches
        }
        for (Integer i : switches) {
            for (Integer j : towardsIds) {
                if (!i.equals(j)) {

                    // For every outgoing edge (i, v) check if it is on a shortest path to j
                    Set<Integer> adjacent = network.getNode(i).getOutgoingConnectedToNodes();
                    List<Link> possibilities = new ArrayList<>();
                    for (Integer v : adjacent) {
                        if (shortestPathLen[i][j] == shortestPathLen[v][j] + 1) {
                            possibilities.addAll(network.getPresentLinksBetween(i, v));
                        }
                    }
                    nextHopPossibilities.put(ImmutablePair.of(i, j), possibilities);

                }
            }
        }

        return nextHopPossibilities;
    }

    /**
     * Uses Robert Jenkins' 32 bit integer hash function
     * Source: http://burtleburtle.net/bob/hash/integer.html
     * <p>
     * Thomas Wang, Jan 1997
     * last update Mar 2007
     * Version 3.1
     *
     * @param a Input value
     * @return Hash value
     */
    public static int hash(int a) {
        a = (a + 0x7ed55d16) + (a << 12);
        a = (a ^ 0xc761c23c) ^ (a >> 19);
        a = (a + 0x165667b1) + (a << 5);
        a = (a + 0xd3a2646c) ^ (a << 9);
        a = (a + 0xfd7046c5) + (a << 3);
        a = (a ^ 0xb55a4f09) ^ (a >> 16);
        a = absolute(a);
        return a;
    }

    /**
     * Forcefully convert integer to absolute.
     * Takes care of the special case when the integer is the minimum integer,
     * which Math.abs() cannot convert to an absolute value and returns a negative value.
     *
     * @param x Integer value
     * @return |x|
     */
    public static int absolute(int x) {
        if (x == Integer.MIN_VALUE) {
            return Integer.MAX_VALUE;
        } else {
            return Math.abs(x);
        }
    }

    public static int getNonSequentialHash(int srcNodeId, int dstNodeId) {
        return absolute(hash(srcNodeId + hash(dstNodeId)));
    }

    /**
     * Determine the K-shortest paths between the ToRs using Yen's K-shortest paths algorithm.
     * It ONLY calculates the K-shortest paths between ToRs.
     * It will have zero entries between servers/non-ToR switches.
     *
     * @param k       K in k-shortest paths
     * @param details Topology details
     * @param network Network
     * @return Mapping of (src, dst)-ToR pair to its K-shortest paths
     */
    public static Map<ImmutablePair<Integer, Integer>, List<AcyclicPath>> determineKspRoutingStateBetweenToRs(int k, TopologyDetails details, Network network) {
        Map<ImmutablePair<Integer, Integer>, List<AcyclicPath>> kShortestPaths = new HashMap<>();
        Set<Integer> torNodes = details.getTorNodeIds();
        YenTopKspAlgorithmWrapper yenTopKsp = new YenTopKspAlgorithmWrapper(network);
        logger.info("K-SHORTEST PATH ROUTING CALCULATION (K=" + k + ")");
        logger.info("  > Calculating Yen's top-K shortest paths for each ToR pair");
        for (Integer i : torNodes) {
            for (Integer j : torNodes) {
                if (!i.equals(j)) {
                    kShortestPaths.put(new ImmutablePair<>(i, j), yenTopKsp.getShortestPaths(i, j, k));
                }
            }
            if (torNodes.size() > 10 && ((i + 1) % Math.ceil((torNodes.size() / 100.0))) == 0) {
                logger.info("  > Progress: " + (((double) i + 1) / (torNodes.size()) * 100) + "%");
            }
        }
        logger.info("");
        return kShortestPaths;

    }

    public static AcyclicPath determinePath(
            Connection connection,
            Map<Link, Integer> linkAssignmentsCounter,
            Network network,
            List<Integer> coreIds
    ) {
        int selectedCoreId = coreIds.get(0);
        int srcTorId = connection.getSrcNode().getOutgoingConnectedToNodes().iterator().next();
        Link srcTorCoreLink = network.getPresentLinksBetween(srcTorId, selectedCoreId).iterator().next();
        int srcTorCoreLinkCount = linkAssignmentsCounter.getOrDefault(srcTorCoreLink, 0);

        int dstTorId = connection.getDstNode().getIncomingConnectedToNodes().iterator().next();
        Link dstTorCoreLink = network.getPresentLinksBetween(selectedCoreId, dstTorId).iterator().next();
        int dstTorCoreLinkCount = linkAssignmentsCounter.getOrDefault(dstTorCoreLink, 0);

        int torCoreLinkCount = Math.max(srcTorCoreLinkCount, dstTorCoreLinkCount);
        for (int coreId : coreIds) {
            Link srcCoreLink = network.getPresentLinksBetween(srcTorId, coreId).iterator().next();
            Link dstCoreLink = network.getPresentLinksBetween(coreId, dstTorId).iterator().next();
            int srcCoreLinkCount = linkAssignmentsCounter.getOrDefault(srcCoreLink, 0);
            int dstCoreLinkCount = linkAssignmentsCounter.getOrDefault(dstCoreLink, 0);
            int linkCount = Math.max(srcCoreLinkCount, dstCoreLinkCount);
            if (linkCount < torCoreLinkCount) {
                selectedCoreId = coreId;
                torCoreLinkCount = linkCount;
            }
        }
        AcyclicPath path = constructPath(network, connection, selectedCoreId);
        updateDirectedLinkCount(path, linkAssignmentsCounter, 1);
        return path;
    }

    public static void updateDirectedLinkCount(AcyclicPath path, Map<Link, Integer> linkAssignmentsCounter, int value) {
        path.subList(1, path.size() - 1).forEach(link -> linkAssignmentsCounter.put(link, Math.max(linkAssignmentsCounter.getOrDefault(link, 0) + value, 0)));
    }

    public static void resetPath(Simulator simulator, Connection connection, AcyclicPath path) {
        assert connection.getActiveFlows().size() == 1;
        Flow flow = connection.getActiveFlows().iterator().next();
        if (flow.getPath() != null && !Objects.equals(flow.getPath(), path)) {
            simulator.endFlow(flow);
            simulator.addFlowToConnection(connection, path);
        }
    }

    public static Map<Integer, Integer> calculateLinkUtilization(Set<AcyclicPath> paths) {
        Map<Integer, Integer> linkUtilization = new HashMap<>();
        paths.forEach(path -> {
            path.forEach(link -> {
                int linkId = link.getLinkId();
                linkUtilization.put(linkId, linkUtilization.getOrDefault(linkId, 0) + 1);
            });
        });
        return linkUtilization;
    }

    public static AcyclicPath constructPath(Network network, Connection connection, int coreId) {
        AcyclicPath path = new AcyclicPath();
        int srcTorId = connection.getSrcNode().getOutgoingConnectedToNodes().iterator().next();
        int dstTorId = connection.getDstNode().getIncomingConnectedToNodes().iterator().next();

        path.add(network.getPresentLinksBetween(connection.getSrcNodeId(), srcTorId).get(0));
        if (srcTorId == dstTorId) {
            path.add(network.getPresentLinksBetween(dstTorId, connection.getDstNodeId()).get(0));
            return path;
        }

        path.add(network.getPresentLinksBetween(srcTorId, coreId).get(0));
        path.add(network.getPresentLinksBetween(coreId, dstTorId).get(0));
        path.add(network.getPresentLinksBetween(dstTorId, connection.getDstNodeId()).get(0));
        return path;
    }
}
