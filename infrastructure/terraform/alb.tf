resource "aws_lb" "main" {
  name               = "${var.project_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = false
  tags = { Name = "${var.project_name}-alb" }
}

resource "aws_lb_target_group" "service" {
  for_each    = var.services
  name        = "${substr(each.key, 0, 25)}-tg"
  port        = each.value.port
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip" # required for Fargate

  health_check {
    path                = each.value.health_check_path
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 15
    matcher             = "200"
  }

  deregistration_delay = 15

  tags = { Name = "${var.project_name}-${each.key}-tg" }
}

# HTTP listener - default action goes to the api-gateway service.
# (Point a real ACM cert at 443 and redirect 80->443 once you have a domain.)
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port               = 80
  protocol           = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.service["api-gateway"].arn
  }
}

# Path-based rules so each microservice is also reachable directly
# (handy for the Task 2/8 API-testing evidence with Postman/Swagger).
resource "aws_lb_listener_rule" "service_routing" {
  for_each     = { for k, v in var.services : k => v if k != "api-gateway" }
  listener_arn = aws_lb_listener.http.arn
  priority     = 100 + index(keys(var.services), each.key)

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.service[each.key].arn
  }

  condition {
    path_pattern {
      values = [each.value.path_prefix]
    }
  }
}

output "alb_dns_name" {
  value = aws_lb.main.dns_name
}
