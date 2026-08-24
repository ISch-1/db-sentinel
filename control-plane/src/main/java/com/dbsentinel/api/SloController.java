package com.dbsentinel.api;

import java.util.List;

import com.dbsentinel.slo.SloService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * Reliability API. {@code GET /api/v1/slo} returns every SLO with its current
 * error budget and burn rate — the single pane of glass for platform health.
 */
@RestController
@RequestMapping("/api/v1/slo")
@RequiredArgsConstructor
public class SloController {

    private final SloService slos;

    @GetMapping
    public List<SloService.SloStatus> all() {
        return slos.allStatuses();
    }
}
