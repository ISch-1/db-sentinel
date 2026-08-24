package com.dbsentinel.slo;

import java.util.List;

/** Source of SLO definitions. Backed by DynamoDB in production. */
public interface SloRepository {
    List<Slo> findAll();
}
