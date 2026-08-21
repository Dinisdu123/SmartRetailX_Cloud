$taskDef = Get-Content taskdef-user-cpu.json | ConvertFrom-Json

# Bump from 256/512 (0.25 vCPU) to 512/1024 (0.5 vCPU)
$taskDef.cpu = "512"
$taskDef.memory = "1024"

# Clean fields that can't be re-submitted
$fieldsToRemove = @('taskDefinitionArn','revision','status','requiresAttributes','compatibilities','registeredAt','registeredBy')
foreach ($f in $fieldsToRemove) {
    $taskDef.PSObject.Properties.Remove($f)
}

$taskDef | ConvertTo-Json -Depth 20 | Set-Content taskdef-user-cpu-final.json

Write-Host "Done. Wrote taskdef-user-cpu-final.json"
