package com.dbsentinel.slo;

/** Raw event counts over an SLO window, sourced from Prometheus. */
public record WindowStats(long total, long bad) {}
