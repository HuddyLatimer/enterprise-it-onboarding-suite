param(
    [Parameter(Mandatory=$true)]
    [string]$EmployeeID,
    
    [Parameter(Mandatory=$true)]
    [string]$HomePath
)

try {
    $SamAccountName = $EmployeeID.ToLower()
    
    if (!(Test-Path $HomePath)) {
        New-Item -ItemType Directory -Path $HomePath -Force
        Write-Host "Created home directory: $HomePath"
    }
    
    $ACL = Get-Acl $HomePath
    
    $AccessRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
        $SamAccountName,
        "FullControl",
        "ContainerInherit,ObjectInherit",
        "None",
        "Allow"
    )
    
    $ACL.SetAccessRule($AccessRule)
    Set-Acl -Path $HomePath -AclObject $ACL
    
    Write-Host "Successfully configured home directory permissions for $SamAccountName"
    Write-Host "Home directory: $HomePath"
    
    exit 0
    
} catch {
    Write-Error "Error creating home directory: $($_.Exception.Message)"
    exit 1
}
