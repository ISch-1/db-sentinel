package com.dbsentinel;

import com.dbsentinel.slo.ErrorBudget;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.within;

@DisplayName("ErrorBudget.compute")
class ErrorBudgetTest {

    @Test
    void noTrafficMeansFullBudget() {
        ErrorBudget b = ErrorBudget.compute("availability", 0, 0, 0.999);
        assertThat(b.healthy()).isTrue();
        assertThat(b.budgetRemaining()).isEqualTo(1.0);
        assertThat(b.burnRate()).isEqualTo(0.0);
    }

    @Test
    void perfectServiceConsumesNoBudget() {
        ErrorBudget b = ErrorBudget.compute("availability", 10_000, 0, 0.999);
        assertThat(b.observed()).isEqualTo(1.0);
        assertThat(b.budgetConsumed()).isEqualTo(0.0);
        assertThat(b.healthy()).isTrue();
    }

    @Test
    void failuresExactlyAtTargetConsumeFullBudget() {
        // 99.9% target over 1000 events allows 1 failure. Exactly 1 failure =>
        // budget fully consumed, burn rate 1.0.
        ErrorBudget b = ErrorBudget.compute("availability", 1000, 1, 0.999);
        assertThat(b.burnRate()).isCloseTo(1.0, within(0.001));
        assertThat(b.budgetConsumed()).isCloseTo(1.0, within(0.001));
    }

    @Test
    void exceedingBudgetIsUnhealthyWithNegativeRemaining() {
        // 5 failures over 1000 with a 0.999 target: allowed 0.001, observed 0.005
        // => burn rate 5x, budget over-consumed.
        ErrorBudget b = ErrorBudget.compute("availability", 1000, 5, 0.999);
        assertThat(b.burnRate()).isCloseTo(5.0, within(0.01));
        assertThat(b.budgetRemaining()).isNegative();
        assertThat(b.healthy()).isFalse();
    }

    @Test
    void observedSuccessRatioIsCorrect() {
        ErrorBudget b = ErrorBudget.compute("availability", 200, 4, 0.99);
        assertThat(b.observed()).isCloseTo(0.98, within(0.0001));
    }
}
