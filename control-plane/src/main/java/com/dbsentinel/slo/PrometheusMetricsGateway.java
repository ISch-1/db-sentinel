package com.dbsentinel.slo;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * Reads event counts from Prometheus via its HTTP query API. The sentinel
 * exports {@code dbs_probes_total} and {@code dbs_probes_failed_total}; those
 * are the raw material for the availability error budget.
 *
 * <p>Kept deliberately dependency-light: a plain JDK HttpClient plus a small
 * regex to pull the scalar out of the Prometheus JSON, so there's no JSON lib
 * to manage for two numbers.
 */
@Component
@Slf4j
public class PrometheusMetricsGateway implements MetricsGateway {

    private static final Pattern VALUE = Pattern.compile("\\[\\s*[0-9.]+\\s*,\\s*\"([0-9.eE+-]+)\"\\s*]");

    private final HttpClient http = HttpClient.newHttpClient();
    private final String promUrl;

    public PrometheusMetricsGateway(@Value("${dbsentinel.prometheus-url:http://prometheus:9090}") String promUrl) {
        this.promUrl = promUrl;
    }

    @Override
    public WindowStats statsFor(Slo slo) {
        // For the demo we read lifetime counters. In production you'd scope the
        // query with the SLO window, e.g. increase(dbs_probes_total[30d]).
        long total = query("dbs_probes_total");
        long bad = query("dbs_probes_failed_total");
        return new WindowStats(total, bad);
    }

    private long query(String promql) {
        try {
            String url = promUrl + "/api/v1/query?query="
                    + URLEncoder.encode(promql, StandardCharsets.UTF_8);
            HttpRequest req = HttpRequest.newBuilder(URI.create(url)).GET().build();
            HttpResponse<String> resp = http.send(req, HttpResponse.BodyHandlers.ofString());
            if (resp.statusCode() != 200) {
                return 0L;
            }
            Matcher m = VALUE.matcher(resp.body());
            if (m.find()) {
                return (long) Double.parseDouble(m.group(1));
            }
            return 0L;
        } catch (Exception e) {
            log.warn("Prometheus query '{}' failed: {}", promql, e.getMessage());
            return 0L;
        }
    }
}
