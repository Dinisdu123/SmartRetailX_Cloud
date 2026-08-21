# Alarm 1: ALB target 5xx errors
aws cloudwatch put-metric-alarm `
  --alarm-name "SmartRetailX-ALB-High5xxRate" `
  --alarm-description "Triggers when target 5xx errors exceed 5 in a 5-minute window" `
  --namespace "AWS/ApplicationELB" `
  --metric-name "HTTPCode_Target_5XX_Count" `
  --dimensions Name=LoadBalancer,Value=app/smartretailx-alb/9af1658388e41719 `
  --statistic Sum `
  --period 300 `
  --threshold 5 `
  --comparison-operator GreaterThanThreshold `
  --evaluation-periods 1 `
  --treat-missing-data notBreaching `
  --region ap-south-1

# Alarm 2: order-processing-service CPU high
aws cloudwatch put-metric-alarm `
  --alarm-name "SmartRetailX-OrderProcessing-HighCPU" `
  --alarm-description "Triggers when order-processing-service CPU exceeds 80 percent for 5 minutes" `
  --namespace "AWS/ECS" `
  --metric-name "CPUUtilization" `
  --dimensions Name=ServiceName,Value=order-processing-service Name=ClusterName,Value=smartretailx-cluster `
  --statistic Average `
  --period 300 `
  --threshold 80 `
  --comparison-operator GreaterThanThreshold `
  --evaluation-periods 1 `
  --treat-missing-data notBreaching `
  --region ap-south-1

# Alarm 3: user-management-service CPU high (relevant given the bcrypt findings)
aws cloudwatch put-metric-alarm `
  --alarm-name "SmartRetailX-UserManagement-HighCPU" `
  --alarm-description "Triggers when user-management-service CPU exceeds 80 percent for 5 minutes" `
  --namespace "AWS/ECS" `
  --metric-name "CPUUtilization" `
  --dimensions Name=ServiceName,Value=user-management-service Name=ClusterName,Value=smartretailx-cluster `
  --statistic Average `
  --period 300 `
  --threshold 80 `
  --comparison-operator GreaterThanThreshold `
  --evaluation-periods 1 `
  --treat-missing-data notBreaching `
  --region ap-south-1

# Alarm 4: RDS CPU high
aws cloudwatch put-metric-alarm `
  --alarm-name "SmartRetailX-RDS-HighCPU" `
  --alarm-description "Triggers when RDS CPU exceeds 80 percent for 5 minutes" `
  --namespace "AWS/RDS" `
  --metric-name "CPUUtilization" `
  --dimensions Name=DBInstanceIdentifier,Value=smartretailx-postgres `
  --statistic Average `
  --period 300 `
  --threshold 80 `
  --comparison-operator GreaterThanThreshold `
  --evaluation-periods 1 `
  --treat-missing-data notBreaching `
  --region ap-south-1

Write-Host "All 4 alarms created."
