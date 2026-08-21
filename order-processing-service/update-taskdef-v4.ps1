$taskDef = Get-Content taskdef4.json | ConvertFrom-Json

# Update image tag to the SQS endpoint fix build
$taskDef.containerDefinitions[0].image = "029223413210.dkr.ecr.ap-south-1.amazonaws.com/smartretailx/order-processing-service:fix-sqs-endpoint-01"

# Clean fields that can't be re-submitted
$fieldsToRemove = @('taskDefinitionArn','revision','status','requiresAttributes','compatibilities','registeredAt','registeredBy')
foreach ($f in $fieldsToRemove) {
    $taskDef.PSObject.Properties.Remove($f)
}

$taskDef | ConvertTo-Json -Depth 20 | Set-Content taskdef4-final.json

Write-Host "Done. Wrote taskdef4-final.json"
