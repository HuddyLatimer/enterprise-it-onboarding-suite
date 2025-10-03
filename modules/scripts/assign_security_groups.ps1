param(
    [Parameter(Mandatory=$true)]
    [string]$EmployeeID,
    
    [Parameter(Mandatory=$true)]
    [string]$Groups
)

try {
    Import-Module ActiveDirectory -ErrorAction Stop
    
    $SamAccountName = $EmployeeID.ToLower()
    $GroupList = $Groups -split ','
    
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
    
    Write-Host "Security group assignment completed for $SamAccountName"
    exit 0
    
} catch {
    Write-Error "Error assigning security groups: $($_.Exception.Message)"
    exit 1
}
