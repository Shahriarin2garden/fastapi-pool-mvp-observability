resource "aws_cloudwatch_metric_alarm" "monthly_spend" {
  alarm_name          = "${var.project}-billing-${var.billing_alarm_usd}-usd"
  alarm_description   = "Alert when estimated monthly charges exceed $${var.billing_alarm_usd}."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  alarm_actions       = [aws_sns_topic.cost_alerts.arn]
  ok_actions          = [aws_sns_topic.cost_alerts.arn]
  treat_missing_data  = "notBreaching"

  metric_name = "EstimatedCharges"
  namespace   = "AWS/Billing"
  period      = 21600
  statistic   = "Maximum"
  threshold   = var.billing_alarm_usd
  dimensions = {
    Currency = "USD"
  }
}

resource "aws_sns_topic" "cost_alerts" {
  name = "${var.project}-cost-alerts"
  tags = { Project = var.project }
}

resource "aws_sns_topic_subscription" "cost_alerts_email" {
  topic_arn = aws_sns_topic.cost_alerts.arn
  protocol  = "email"
  endpoint  = var.budget_email
}

resource "aws_budgets_budget" "monthly" {
  name         = "${var.project}-monthly"
  budget_type  = "COST"
  limit_amount = var.budget_monthly_usd
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.budget_email]
  }
}
