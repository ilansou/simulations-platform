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

package ch.ethz.systems.floodns.ext.logger.empty;

import ch.ethz.systems.floodns.core.*;
import ch.ethz.systems.floodns.deeplearningtraining.AssignmentsDurationLogger;
import ch.ethz.systems.floodns.deeplearningtraining.Job;
import ch.ethz.systems.floodns.deeplearningtraining.JobLogger;
import ch.ethz.systems.floodns.ext.routing.CentralizedRoutingStrategy;

public class VoidLoggerFactory extends LoggerFactory {

    public VoidLoggerFactory(Simulator simulator) {
        super(simulator);
    }

    @Override
    public NodeLogger createNodeLogger(Node node) {
        return new VoidNodeLogger(simulator, node);
    }

    @Override
    public LinkLogger createLinkLogger(Link link) {
        return new VoidLinkLogger(simulator, link);
    }

    @Override
    public FlowLogger createFlowLogger(Flow flow) {
        return new VoidFlowLogger(simulator, flow);
    }

    @Override
    public JobLogger createJobLogger(Job job) {
        return new VoidJobLogger(simulator, job);
    }

    @Override
    public AssignmentsDurationLogger createAssignmentsDurationLogger(CentralizedRoutingStrategy strategy) {
        return new VoidAssignmentsDurationLogger(simulator, strategy);
    }

    @Override
    public ConnectionLogger createConnectionLogger(Connection connection) {
        return new VoidConnectionLogger(simulator, connection);
    }

    @Override
    public void close() {
        // Intentionally does nothing
    }

}
