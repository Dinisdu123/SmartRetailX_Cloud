$taskDef = Get-Content taskdef-gateway-cors.json | ConvertFrom-Json

# Update image tag to the CORS fix build
$taskDef.containerDefinitions[0].image = "029223413210.dkr.ecr.ap-south-1.amazonaws.com/smartretailx/api-gateway:fix-cors-01"

# Clean fields that can't be re-submitted
$fieldsToRemove = @('taskDefinitionArn','revision','status','requiresAttributes','compatibilities','registeredAt','registeredBy')
foreach ($f in $fieldsToRemove) {
    $taskDef.PSObject.Properties.Remove($f)
}

$taskDef | ConvertTo-Json -Depth 20 | Set-Content taskdef-gateway-cors-final.json

Write-Host "Done. Wrote taskdef-gateway-cors-final.json"
