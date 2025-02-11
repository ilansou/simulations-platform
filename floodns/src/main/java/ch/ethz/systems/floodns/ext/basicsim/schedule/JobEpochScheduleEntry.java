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

import org.apache.commons.lang3.tuple.ImmutablePair;

import java.util.HashMap;
import java.util.Map;
import java.util.Set;

public class JobEpochScheduleEntry {

    private final int jobId;
    private final String modelName;
    private final String parallelizationType;
    private final Map<Integer, Set<ImmutablePair<Integer, Integer>>> stageCommodities;
    private final double flowSize;
    private final long startTimeNs;
    private final long computeTimeNs;
    private final int numMiniBatches;
    private final int microBatchSize;


    public JobEpochScheduleEntry(int jobId, String modelName, String parallelizationType, double flowSize, long startTimeNs, long computeTimeNs, int numMiniBatches, int microBatchSize) {
        this.jobId = jobId;
        this.modelName = modelName;
        this.parallelizationType = parallelizationType;
        this.flowSize = flowSize;
        this.startTimeNs = startTimeNs;
        this.computeTimeNs = computeTimeNs;
        this.numMiniBatches = numMiniBatches;
        this.microBatchSize = microBatchSize;
        this.stageCommodities = new HashMap<>();

    }

    public int getJobId() {
        return jobId;
    }

    public String getModelName() {
        return modelName;
    }

    public String getParallelizationType() {
        return parallelizationType;
    }

    public Map<Integer, Set<ImmutablePair<Integer, Integer>>> getStageCommodities() {
        return stageCommodities;
    }

    public double getFlowSize() {
        return flowSize;
    }

    public long getStartTimeNs() {
        return startTimeNs;
    }

    public long getComputeTimeNs() {
        return computeTimeNs;
    }

    public int getNumMiniBatches() {
        return numMiniBatches;
    }

    public int getMicroBatchSize() {
        return microBatchSize;
    }
}
