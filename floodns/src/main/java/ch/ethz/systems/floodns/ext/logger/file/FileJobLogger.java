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

package ch.ethz.systems.floodns.ext.logger.file;

import ch.ethz.systems.floodns.core.Connection;
import ch.ethz.systems.floodns.core.Simulator;
import ch.ethz.systems.floodns.deeplearningtraining.Job;
import ch.ethz.systems.floodns.deeplearningtraining.JobLogger;

import java.io.IOException;
import java.io.Writer;
import java.util.Map;
import java.util.Set;

public class FileJobLogger extends JobLogger {

    private final Writer writerJobInfoFile;

    public FileJobLogger(Simulator simulator, Job job, Writer writerJobInfoFile) {
        super(simulator, job);
        this.writerJobInfoFile = writerJobInfoFile;
    }

    /**
     * Save the general (statistical) information of the flow.
     * Values are comma-separated, lines are new-line-separated.
     * <p>
     * File format (9 columns):
     * [jobId],[epochNumber],[stageIndex],[startTime],[endTime],[duration],[finished],[flowSize],[childConnections ; sep.,[extra info]
     * <p>
     */
    @Override
    protected void saveInfo(int jobId, int epoch, long startTime, Map<Integer, Long> stageEndTime, Map<Integer, Long> stageDuration, double flowSize, Map<Integer, Set<Connection>> stageConnections, long runtime) {
        stageConnections.forEach((stageIndex, connections) -> {
            boolean isFinished = stageEndTime.containsKey(stageIndex) && stageEndTime.get(stageIndex) != runtime;
            try {
                writerJobInfoFile.write(
                        jobId + "," +
                                epoch + "," +
                                stageIndex + "," +
                                startTime + "," +
                                stageEndTime.get(stageIndex) + "," +
                                stageDuration.get(stageIndex) + "," +
                                (isFinished ? "Y" : "N") + "," +
                                connections.size() + "," +
                                flowSize + "," +
                                ConnectionIdsToString(connections) + "," +
                                "\r\n"
                );
                writerJobInfoFile.flush();
            } catch (IOException e) {
                throw new FatalLogFileException(e);
            }
        });
    }

    /**
     * Convert a list of identifiers into a ;-separated string.
     *
     * @param connections Flow identifiers (e.g. [3, 4, 5])
     * @return ;-separated list string (e.g. "3;4;5")
     */
    private String ConnectionIdsToString(Set<Connection> connections) {
        StringBuilder s = new StringBuilder();
        for (Connection connection : connections) {
            s.append(connection.getConnectionId());
            s.append(";");
        }
        return s.substring(0, s.length() > 1 ? s.length() - 1 : s.length());
    }

}
