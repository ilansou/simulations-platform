package ch.ethz.systems.floodns.deeplearningtraining;

import ch.ethz.systems.floodns.core.Simulator;
import ch.ethz.systems.floodns.ext.routing.CentralizedRoutingStrategy;

public abstract class AssignmentsDurationLogger {

    // Simulator handle
    protected final Simulator simulator;

    // Change track variables
    private final CentralizedRoutingStrategy routingStrategy;
    private boolean isInfoSavingEnabled;

    protected AssignmentsDurationLogger(Simulator simulator, CentralizedRoutingStrategy routingStrategy) {
        this.simulator = simulator;
        // Properties
        this.routingStrategy = routingStrategy;
        this.isInfoSavingEnabled = true;
    }

    /**
     * Enable/disable logging the info of flows.
     *
     * @param enabled True iff logging enabled
     */
    public void setInfoSavingEnabled(boolean enabled) {
        this.isInfoSavingEnabled = enabled;
    }

    /**
     * Final flush of logged state.
     */
    public final void finalFlush() {
        if (isInfoSavingEnabled) {
            double averageDuration = routingStrategy.getAverageDuration();
            int numConnections = routingStrategy.getNumAssignedConnections();
            saveInfo(averageDuration, numConnections);
        }
    }

    /**
     * Save the final flow info.
     *
     * @param averageDuration Average duration
     * @param numConnections  Number of connections
     */
    public abstract void saveInfo(double averageDuration, int numConnections);
}
