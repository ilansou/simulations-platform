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

public class LinkFailureEvent extends Event {

    private final Link link;

    /**
     * Create link failure event which causes the link to fail the given amount of time later.
     *
     * @param simulator   Simulator to which this event belongs to
     * @param timeFromNow Time it will take before happening from now
     */
    public LinkFailureEvent(Simulator simulator, long timeFromNow, Link link) {
        super(simulator, 0, timeFromNow);
        this.link = link;
    }

    @Override
    protected void trigger() {
        // When a link failure occurs, all traversing flows through that link
        // need to be rerouted. This is done by removing the link in
        // the network, and then calling the path assignment algorithm
        // for all flows that traverse the link.
        simulator.getNetwork().getFailedLinks().add(link);
    }
}
