param(
    [Parameter(Mandatory=$true)]
    [string]$EmployeeID,
    
    [Parameter(Mandatory=$true)]
    [string]$DriveMappings
)

try {
    $SamAccountName = $EmployeeID.ToLower()
    $MappingList = $DriveMappings -split ','
    
    foreach ($Mapping in $MappingList) {
        $Mapping = $Mapping.Trim()
        $DriveLetter = $Mapping.Split(':')[0]
        $Path = $Mapping.Split(':')[1]
        
        try {
            New-PSDrive -Name $DriveLetter -PSProvider FileSystem -Root $Path -Persist -ErrorAction Stop
            
            Write-Host "Successfully mapped drive $DriveLetter to $Path"
        } catch {
            Write-Warning "Could not map drive $DriveLetter to $Path: $($_.Exception.Message)"
        }
    }
    
    Write-Host "Drive mapping configuration completed for $SamAccountName"
    exit 0
    
} catch {
    Write-Error "Error setting up drive mappings: $($_.Exception.Message)"
    exit 1
}
