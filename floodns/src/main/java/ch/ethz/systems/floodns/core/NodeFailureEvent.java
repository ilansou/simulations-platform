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

package ch.ethz.systems.floodns.core;

public class NodeFailureEvent extends Event {

    private final Node failedNode;

    /**
     * Create connection finish event which will happen the given amount of time later.
     *
     * @param simulator   Simulator to which this event belongs to
     * @param timeFromNow Time it will take before happening from now
     */
    public NodeFailureEvent(Simulator simulator, long timeFromNow, Node failedNode) {
        super(simulator, 0, timeFromNow);
        this.failedNode = failedNode;
    }

    @Override
    protected void trigger() {
        // When a node failure occurs, all traversing flows through that node
        // need to be rerouted. This is done by removing the node in
        // the network, and then calling the path assignment algorithm
        // for all flows that traverse the node.
        failedNode.getOutgoingLinks().forEach(link -> simulator.getNetwork().getFailedLinks().add(link));
        failedNode.getIncomingLinks().forEach(link -> simulator.getNetwork().getFailedLinks().add(link));
        simulator.getNetwork().getFailedNodes().add(failedNode);
    }
}
