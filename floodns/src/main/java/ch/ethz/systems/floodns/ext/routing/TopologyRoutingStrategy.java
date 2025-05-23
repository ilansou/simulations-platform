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

import ch.ethz.systems.floodns.core.AcyclicPath;
import ch.ethz.systems.floodns.core.Connection;
import ch.ethz.systems.floodns.core.Network;
import ch.ethz.systems.floodns.core.Simulator;
import ch.ethz.systems.floodns.ext.basicsim.topology.Topology;
import ch.ethz.systems.floodns.ext.basicsim.topology.TopologyDetails;

public abstract class TopologyRoutingStrategy extends RoutingStrategy {

    protected final Topology topology;
    protected final Network network;
    protected final TopologyDetails topologyDetails;

    /**
     * Routing strategy.
     *
     * @param simulator Simulator instance
     */
    public TopologyRoutingStrategy(Simulator simulator, Topology topology) {
        super(simulator);
        this.topology = topology;
        this.network = topology.getNetwork();
        this.topologyDetails = topology.getDetails();
    }

    /**
     * Add a set of flows to a connection via {@link Simulator#addFlowToConnection(Connection, AcyclicPath)}.
     *
     * @param connection User connection
     */
    public final void assignStartFlows(Connection connection) {
        if (topology.getDetails().isInvalidEndpoint(connection.getSrcNodeId()) || topology.getDetails().isInvalidEndpoint(connection.getDstNodeId())) {
            throw new IllegalArgumentException("Connection " + connection + " has endpoints which are not all valid according to the topology");
        }
        assignStartFlowsInTopology(connection);
    }

    /**
     * Add a set of flows to a connection via {@link Simulator#addFlowToConnection(Connection, AcyclicPath)}.
     *
     * @param connection User flow
     */
    protected abstract void assignStartFlowsInTopology(Connection connection);

    /**
     * Get the topology details.
     *
     * @return Topology details
     */
    public TopologyDetails getTopologyDetails() {
        return topologyDetails;
    }

}
