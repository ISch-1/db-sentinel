output "slo_table" {
  description = "DynamoDB table holding SLO definitions"
  value       = aws_dynamodb_table.slo_definitions.name
}

output "incidents_table" {
  description = "DynamoDB table holding incidents"
  value       = aws_dynamodb_table.incidents.name
}

output "alarms" {
  description = "CloudWatch alarms provisioned"
  value = [
    aws_cloudwatch_metric_alarm.high_connections.alarm_name,
    aws_cloudwatch_metric_alarm.replica_lag.alarm_name,
  ]
}
