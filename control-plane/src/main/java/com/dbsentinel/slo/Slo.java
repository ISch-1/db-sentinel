package com.dbsentinel.slo;

/**
 * A Service Level Objective definition, as stored in DynamoDB and provisioned
 * by Terraform.
 *
 * @param id         stable identifier, e.g. "availability"
 * @param description human-readable description
 * @param target     target as a fraction, e.g. 0.999 for 99.9%
 * @param windowDays rolling window the objective is measured over
 * @param kind       "availability" or "latency"
 */
public record Slo(
        String id,
        String description,
        double target,
        int windowDays,
        String kind
) {}
