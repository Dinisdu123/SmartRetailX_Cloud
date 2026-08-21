$taskDef = Get-Content taskdef-user-cors.json | ConvertFrom-Json

$corsValue = "http://localhost:5173,http://localhost:5174,http://smartretailx-frontend-029223413210.s3-website.ap-south-1.amazonaws.com"

# Add or update CORS_ORIGINS in environment
$existingEnv = @($taskDef.containerDefinitions[0].environment | Where-Object { $_.name -ne "CORS_ORIGINS" })
$existingEnv += [PSCustomObject]@{ name = "CORS_ORIGINS"; value = $corsValue }
$taskDef.containerDefinitions[0].environment = $existingEnv

# Clean fields that can't be re-submitted
$fieldsToRemove = @('taskDefinitionArn','revision','status','requiresAttributes','compatibilities','registeredAt','registeredBy')
foreach ($f in $fieldsToRemove) {
    $taskDef.PSObject.Properties.Remove($f)
}

$taskDef | ConvertTo-Json -Depth 20 | Set-Content taskdef-user-cors-final.json

Write-Host "Done. Wrote taskdef-user-cors-final.json"
