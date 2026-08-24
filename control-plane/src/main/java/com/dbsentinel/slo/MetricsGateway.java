package com.dbsentinel.slo;

/** Source of the event counts used to compute error budgets. */
public interface MetricsGateway {
    /** Total and failed events for the given SLO over its window. */
    WindowStats statsFor(Slo slo);
}
