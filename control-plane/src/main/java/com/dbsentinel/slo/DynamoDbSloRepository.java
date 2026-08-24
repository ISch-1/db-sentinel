package com.dbsentinel.slo;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Repository;
import software.amazon.awssdk.services.dynamodb.DynamoDbClient;
import software.amazon.awssdk.services.dynamodb.model.AttributeValue;
import software.amazon.awssdk.services.dynamodb.model.ScanRequest;

/**
 * Reads SLO definitions from the DynamoDB table Terraform provisions
 * ({@code dbs-slo-definitions}). Never creates the table — that boundary
 * belongs to Terraform (infra as code).
 */
@Repository
@Slf4j
public class DynamoDbSloRepository implements SloRepository {

    private final DynamoDbClient dynamo;
    private final String tableName;

    public DynamoDbSloRepository(DynamoDbClient dynamo,
                                 org.springframework.core.env.Environment env) {
        this.dynamo = dynamo;
        this.tableName = env.getProperty("dbsentinel.slo-table", "dbs-slo-definitions");
    }

    @Override
    public List<Slo> findAll() {
        List<Slo> slos = new ArrayList<>();
        try {
            var resp = dynamo.scan(ScanRequest.builder().tableName(tableName).build());
            for (Map<String, AttributeValue> item : resp.items()) {
                slos.add(toSlo(item));
            }
        } catch (Exception e) {
            log.warn("Could not read SLO definitions from DynamoDB ({}): {}. "
                    + "Has `terraform apply` run?", tableName, e.getMessage());
        }
        return slos;
    }

    private Slo toSlo(Map<String, AttributeValue> item) {
        return new Slo(
                s(item, "slo_id"),
                s(item, "description"),
                d(item, "target", 0.999),
                (int) d(item, "window_days", 30),
                s(item, "kind"));
    }

    private static String s(Map<String, AttributeValue> item, String key) {
        AttributeValue v = item.get(key);
        return v == null ? "" : v.s();
    }

    private static double d(Map<String, AttributeValue> item, String key, double dflt) {
        AttributeValue v = item.get(key);
        if (v == null || v.n() == null) return dflt;
        try {
            return Double.parseDouble(v.n());
        } catch (NumberFormatException e) {
            return dflt;
        }
    }
}
