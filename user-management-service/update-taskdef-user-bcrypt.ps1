$taskDef = Get-Content taskdef-user-bcrypt.json | ConvertFrom-Json

# Update image tag to the async bcrypt fix build
$taskDef.containerDefinitions[0].image = "029223413210.dkr.ecr.ap-south-1.amazonaws.com/smartretailx/user-management-service:fix-bcrypt-async-01"

# Clean fields that can't be re-submitted
$fieldsToRemove = @('taskDefinitionArn','revision','status','requiresAttributes','compatibilities','registeredAt','registeredBy')
foreach ($f in $fieldsToRemove) {
    $taskDef.PSObject.Properties.Remove($f)
}

$taskDef | ConvertTo-Json -Depth 20 | Set-Content taskdef-user-bcrypt-final.json

Write-Host "Done. Wrote taskdef-user-bcrypt-final.json"
