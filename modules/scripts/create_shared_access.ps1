param(
    [Parameter(Mandatory=$true)]
    [string]$EmployeeID,
    
    [Parameter(Mandatory=$true)]
    [string]$Drives
)

try {
    Import-Module ActiveDirectory -ErrorAction Stop
    
    $SamAccountName = $EmployeeID.ToLower()
    $DriveList = $Drives -split ','
    
    foreach ($Drive in $DriveList) {
        $Drive = $Drive.Trim()
        
        try {
            $DrivePath = $Drive.Replace('\\', '\\')
            
            $ACL = Get-Acl $DrivePath -ErrorAction Stop
            
            $AccessRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
                $SamAccountName,
                "FullControl",
                "ContainerInherit,ObjectInherit",
                "None",
                "Allow"
            )
            
            $ACL.SetAccessRule($AccessRule)
            Set-Acl -Path $DrivePath -AclObject $ACL
            
            Write-Host "Successfully granted access to $Drive for $SamAccountName"
        } catch {
            Write-Warning "Could not set permissions for $Drive: $($_.Exception.Message)"
        }
    }
    
    Write-Host "Shared drive access configuration completed for $SamAccountName"
    exit 0
    
} catch {
    Write-Error "Error configuring shared drive access: $($_.Exception.Message)"
    exit 1
}
