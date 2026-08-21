$taskDef = Get-Content taskdef-inventory-sqs.json | ConvertFrom-Json

# Update image tag to the build with the new SQS consumer
$taskDef.containerDefinitions[0].image = "029223413210.dkr.ecr.ap-south-1.amazonaws.com/smartretailx/inventory-management-service:add-sqs-consumer-01"

# Clean fields that can't be re-submitted
$fieldsToRemove = @('taskDefinitionArn','revision','status','requiresAttributes','compatibilities','registeredAt','registeredBy')
foreach ($f in $fieldsToRemove) {
    $taskDef.PSObject.Properties.Remove($f)
}

$taskDef | ConvertTo-Json -Depth 20 | Set-Content taskdef-inventory-sqs-final.json

Write-Host "Done. Wrote taskdef-inventory-sqs-final.json"
