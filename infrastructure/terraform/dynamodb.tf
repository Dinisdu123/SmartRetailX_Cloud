resource "aws_dynamodb_table" "products" {
  name         = "${var.project_name}-products"
  billing_mode = "PAY_PER_REQUEST" # scales automatically, no capacity planning needed
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = { Name = "${var.project_name}-products" }
}

resource "aws_dynamodb_table" "inventory" {
  name         = "${var.project_name}-inventory"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "product_id"

  attribute {
    name = "product_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  # DynamoDB Streams -> feeds the Lambda event processor for real-time
  # stock-level fan-out (see lambda.tf)
  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  tags = { Name = "${var.project_name}-inventory" }
}

output "dynamodb_tables" {
  value = {
    products  = aws_dynamodb_table.products.name
    inventory = aws_dynamodb_table.inventory.name
  }
}
