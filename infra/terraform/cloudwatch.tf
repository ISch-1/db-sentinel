# CloudWatch alarms as code. LocalStack emulates the CloudWatch API, so these
# apply cleanly with no account. In real AWS they page on-call when the fleet
# breaches a threshold.

resource "aws_cloudwatch_metric_alarm" "high_connections" {
  alarm_name          = "dbs-high-connection-usage"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "DatabaseConnections"
  namespace           = "DbSentinel"
  period              = 60
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Connection usage above 80% of max_connections for 2 minutes"
  treat_missing_data  = "notBreaching"
  tags                = local.tags
}

resource "aws_cloudwatch_metric_alarm" "replica_lag" {
  alarm_name          = "dbs-replica-lag"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "ReplicaLagSeconds"
  namespace           = "DbSentinel"
  period              = 60
  statistic           = "Maximum"
  threshold           = 10
  alarm_description   = "Replica lag above 10s for 3 minutes"
  treat_missing_data  = "notBreaching"
  tags                = local.tags
}
