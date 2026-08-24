package com.dbsentinel.slo;

/**
 * A computed error budget for an SLO over its window.
 *
 * <p>The error budget is the amount of failure an SLO permits. If the target is
 * 99.9%, the budget is 0.1% of events. "Consumed" is how much of that budget the
 * bad events have already used; "burn rate" is how fast — a burn rate above 1.0
 * means you're spending budget faster than the window allows and will breach if
 * it continues.
 */
public record ErrorBudget(
        String sloId,
        long totalEvents,
        long badEvents,
        double target,
        double observed,        // actual success ratio
        double budgetTotal,     // allowed failure fraction (1 - target)
        double budgetConsumed,  // fraction of the budget already used (0..1+)
        double budgetRemaining, // 1 - budgetConsumed (can go negative once breached)
        double burnRate,        // observed failure rate / allowed failure rate
        boolean healthy         // true while budget remains
) {

    /**
     * Compute an error budget from raw counts.
     *
     * @param sloId  the SLO this budget belongs to
     * @param total  total events in the window
     * @param bad    failed events in the window
     * @param target target success fraction (e.g. 0.999)
     */
    public static ErrorBudget compute(String sloId, long total, long bad, double target) {
        if (total <= 0) {
            // No traffic yet: budget fully intact by definition.
            double budgetTotalEmpty = 1.0 - target;
            return new ErrorBudget(sloId, 0, 0, target, 1.0,
                    budgetTotalEmpty, 0.0, 1.0, 0.0, true);
        }
        double observedFailure = (double) bad / total;
        double observedSuccess = 1.0 - observedFailure;
        double allowedFailure = 1.0 - target;          // the budget, as a rate

        double budgetConsumed = allowedFailure == 0.0
                ? (bad > 0 ? Double.POSITIVE_INFINITY : 0.0)
                : observedFailure / allowedFailure;
        double budgetRemaining = 1.0 - budgetConsumed;
        double burnRate = allowedFailure == 0.0
                ? (observedFailure > 0 ? Double.POSITIVE_INFINITY : 0.0)
                : observedFailure / allowedFailure;

        boolean healthy = budgetRemaining > 0.0;

        return new ErrorBudget(sloId, total, bad, target, observedSuccess,
                allowedFailure, budgetConsumed, budgetRemaining, burnRate, healthy);
    }
}
