# --- Dead-letter queues first, so the main queues can reference them ---
resource "aws_sqs_queue" "orders_dlq" {
  name                      = "${var.project_name}-orders-dlq"
  message_retention_seconds = 1209600 # 14 days
}

resource "aws_sqs_queue" "notifications_dlq" {
  name                      = "${var.project_name}-notifications-dlq"
  message_retention_seconds = 1209600
}

# --- Main queues ---
resource "aws_sqs_queue" "orders" {
  name                       = "${var.project_name}-orders-queue"
  visibility_timeout_seconds = 30
  message_retention_seconds  = 345600 # 4 days

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.orders_dlq.arn
    maxReceiveCount     = 5
  })
}

resource "aws_sqs_queue" "notifications" {
  name                       = "${var.project_name}-notification-queue"
  visibility_timeout_seconds = 30
  message_retention_seconds  = 345600

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.notifications_dlq.arn
    maxReceiveCount     = 5
  })
}

# --- SNS topics for fan-out (pub/sub) events ---
resource "aws_sns_topic" "order_events" {
  name = "${var.project_name}-order-events"
}

resource "aws_sns_topic" "inventory_events" {
  name = "${var.project_name}-inventory-events"
}

# order-processing publishes to SNS -> fans out to notification queue
# and (optionally) an analytics queue later without touching order code.
resource "aws_sns_topic_subscription" "order_events_to_notifications" {
  topic_arn = aws_sns_topic.order_events.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.notifications.arn
}

resource "aws_sqs_queue_policy" "notifications_allow_sns" {
  queue_url = aws_sqs_queue.notifications.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "sns.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.notifications.arn
      Condition = { ArnEquals = { "aws:SourceArn" = aws_sns_topic.order_events.arn } }
    }]
  })
}

# --- EventBridge bus for real-time pricing/promotion + delivery events ---
resource "aws_cloudwatch_event_bus" "realtime" {
  name = "${var.project_name}-realtime-bus"
}

output "queue_urls" {
  value = {
    orders        = aws_sqs_queue.orders.url
    notifications = aws_sqs_queue.notifications.url
  }
}

output "sns_topic_arns" {
  value = {
    order_events     = aws_sns_topic.order_events.arn
    inventory_events = aws_sns_topic.inventory_events.arn
  }
}
