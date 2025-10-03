param(
    [Parameter(Mandatory=$true)]
    [string]$EmployeeID,
    
    [Parameter(Mandatory=$true)]
    [string]$Groups,
    
    [Parameter(Mandatory=$true)]
    [string]$Permissions,
    
    [Parameter(Mandatory=$true)]
    [string]$SharedDrives
)

try {
    Import-Module ActiveDirectory -ErrorAction Stop
    
    $SamAccountName = $EmployeeID.ToLower()
    $GroupList = $Groups -split ','
    $PermissionList = $Permissions -split ','
    $DriveList = $SharedDrives -split ','
    
    foreach ($Group in $GroupList) {
        $Group = $Group.Trim()
        
        try {
            $ADGroup = Get-ADGroup -Identity $Group -ErrorAction Stop
            
            Add-ADGroupMember -Identity $Group -Members $SamAccountName
            
            Write-Host "Successfully added $SamAccountName to group: $Group"
        } catch {
            Write-Warning "Group $Group not found or user already member: $($_.Exception.Message)"
        }
    }
    
    foreach ($Drive in $DriveList) {
        $Drive = $Drive.Trim()
        
        try {
            $DrivePath = $Drive.Replace('\\', '\\')
            
            $ACL = Get-Acl $DrivePath -ErrorAction Stop
            
            foreach ($Permission in $PermissionList) {
                $Permission = $Permission.Trim()
                
                $AccessRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
                    $SamAccountName,
                    $Permission,
                    "ContainerInherit,ObjectInherit",
                    "None",
                    "Allow"
                )
                
                $ACL.SetAccessRule($AccessRule)
            }
            
            Set-Acl -Path $DrivePath -AclObject $ACL
            
            Write-Host "Successfully granted access to $Drive for $SamAccountName"
        } catch {
            Write-Warning "Could not set permissions for $Drive: $($_.Exception.Message)"
        }
    }
    
    Write-Host "Security group assignment completed for $SamAccountName"
    exit 0
    
} catch {
    Write-Error "Error assigning security groups: $($_.Exception.Message)"
    exit 1
}
