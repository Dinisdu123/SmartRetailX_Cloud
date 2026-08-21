$taskDef = Get-Content taskdef2.json | ConvertFrom-Json

# Fix / add plain environment variables
$taskDef.containerDefinitions[0].environment = $taskDef.containerDefinitions[0].environment | Where-Object { $_.name -ne "SQS_ORDERS_QUEUE_URL" }

$newEnvVars = @(
    [PSCustomObject]@{ name = "SQS_QUEUE_URL"; value = "https://sqs.ap-south-1.amazonaws.com/029223413210/smartretailx-orders-queue" },
    [PSCustomObject]@{ name = "PRODUCT_SERVICE_URL"; value = "http://product-catalogue-service.smartretailx.local:8002" }
)

$taskDef.containerDefinitions[0].environment = @($taskDef.containerDefinitions[0].environment) + $newEnvVars

# Add secrets block for sensitive values
$secretsBlock = @(
    [PSCustomObject]@{ name = "DATABASE_URL"; valueFrom = "arn:aws:ssm:ap-south-1:029223413210:parameter/smartretailx/order-processing-service/DATABASE_URL" },
    [PSCustomObject]@{ name = "JWT_SECRET_KEY"; valueFrom = "arn:aws:ssm:ap-south-1:029223413210:parameter/smartretailx/order-processing-service/JWT_SECRET_KEY" }
)

$taskDef.containerDefinitions[0] | Add-Member -NotePropertyName secrets -NotePropertyValue $secretsBlock -Force

# Update image tag to our fixed build
$taskDef.containerDefinitions[0].image = "029223413210.dkr.ecr.ap-south-1.amazonaws.com/smartretailx/order-processing-service:fix-requests-01"

# Clean fields that can't be re-submitted
$fieldsToRemove = @('taskDefinitionArn','revision','status','requiresAttributes','compatibilities','registeredAt','registeredBy')
foreach ($f in $fieldsToRemove) {
    $taskDef.PSObject.Properties.Remove($f)
}

$taskDef | ConvertTo-Json -Depth 20 | Set-Content taskdef3.json

Write-Host "Done. Wrote taskdef3.json"
