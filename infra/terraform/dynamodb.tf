# State stores for the platform, provisioned as code.
#
# In a real deployment these would be the managed databases the SRE team owns
# (DynamoDB tables holding operational state). Here they hold the SLO
# definitions the control-plane reads and the incidents the sentinel writes.

resource "aws_dynamodb_table" "slo_definitions" {
  name         = "dbs-slo-definitions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "slo_id"

  attribute {
    name = "slo_id"
    type = "S"
  }

  tags = local.tags
}

resource "aws_dynamodb_table" "incidents" {
  name         = "dbs-incidents"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "incident_id"
  range_key    = "opened_at"

  attribute {
    name = "incident_id"
    type = "S"
  }

  attribute {
    name = "opened_at"
    type = "S"
  }

  # Query "all incidents for a target, newest first" without a full scan.
  global_secondary_index {
    name            = "by_target"
    hash_key        = "target"
    range_key       = "opened_at"
    projection_type = "ALL"
  }

  attribute {
    name = "target"
    type = "S"
  }

  tags = local.tags
}

# Seed the availability + latency SLOs the control-plane evaluates against.
resource "aws_dynamodb_table_item" "slo_availability" {
  table_name = aws_dynamodb_table.slo_definitions.name
  hash_key   = aws_dynamodb_table.slo_definitions.hash_key

  item = jsonencode({
    slo_id      = { S = "availability" }
    description = { S = "Fraction of successful health probes over a rolling 30-day window" }
    target      = { N = tostring(var.slo_availability_target) }
    window_days = { N = "30" }
    kind        = { S = "availability" }
  })
}

resource "aws_dynamodb_table_item" "slo_latency" {
  table_name = aws_dynamodb_table.slo_definitions.name
  hash_key   = aws_dynamodb_table.slo_definitions.hash_key

  item = jsonencode({
    slo_id       = { S = "latency_p99" }
    description  = { S = "Fraction of queries under the latency threshold" }
    target       = { N = tostring(var.slo_availability_target) }
    window_days  = { N = "30" }
    kind         = { S = "latency" }
    threshold_ms = { N = tostring(var.latency_slo_ms) }
  })
}
