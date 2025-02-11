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

public class NodeRecoveryEvent extends Event {

    private final Node node;

    /**
     * Create connection finish event which will happen the given amount of time later.
     *
     * @param simulator   Simulator to which this event belongs to
     * @param timeFromNow Time it will take before happening from now
     */
    public NodeRecoveryEvent(Simulator simulator, long timeFromNow, Node node) {
        super(simulator, 0, timeFromNow);
        this.node = node;
    }

    @Override
    protected void trigger() {
        // Does not trigger anything, because before every active event, the
        // amount of data a flow transmitted is updated. The insertion of this
        // event has that purpose.
        node.getOutgoingLinks().forEach(link -> simulator.getNetwork().getFailedLinks().remove(link));
        node.getIncomingLinks().forEach(link -> simulator.getNetwork().getFailedLinks().remove(link));
        simulator.getNetwork().getFailedNodes().remove(node);
    }
}
