$taskDef = Get-Content taskdef-gateway.json | ConvertFrom-Json

# Update image tag to the duplicate FastAPI() fix build
$taskDef.containerDefinitions[0].image = "029223413210.dkr.ecr.ap-south-1.amazonaws.com/smartretailx/api-gateway:fix-duplicate-app-01"

# Clean fields that can't be re-submitted
$fieldsToRemove = @('taskDefinitionArn','revision','status','requiresAttributes','compatibilities','registeredAt','registeredBy')
foreach ($f in $fieldsToRemove) {
    $taskDef.PSObject.Properties.Remove($f)
}

$taskDef | ConvertTo-Json -Depth 20 | Set-Content taskdef-gateway-final.json

Write-Host "Done. Wrote taskdef-gateway-final.json"
