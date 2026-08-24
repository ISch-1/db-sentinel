package com.dbsentinel.slo;

import java.util.List;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

/**
 * Combines SLO definitions (from DynamoDB) with live event counts (from
 * Prometheus) to produce error budgets. This is the reliability roadmap made
 * queryable: every SLO, its budget, and whether it's healthy.
 */
@Service
@RequiredArgsConstructor
public class SloService {

    private final SloRepository slos;
    private final MetricsGateway metrics;

    /** Fallback SLOs if DynamoDB hasn't been provisioned yet, so the API still works. */
    private static final List<Slo> DEFAULTS = List.of(
            new Slo("availability", "Successful health probes over the window", 0.999, 30, "availability")
    );

    public List<SloStatus> allStatuses() {
        List<Slo> defs = slos.findAll();
        if (defs.isEmpty()) {
            defs = DEFAULTS;
        }
        return defs.stream().map(this::statusFor).toList();
    }

    public SloStatus statusFor(Slo slo) {
        WindowStats stats = metrics.statsFor(slo);
        ErrorBudget budget = ErrorBudget.compute(slo.id(), stats.total(), stats.bad(), slo.target());
        return new SloStatus(slo, budget);
    }

    public record SloStatus(Slo slo, ErrorBudget budget) {}
}
