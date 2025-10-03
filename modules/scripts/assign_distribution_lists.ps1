param(
    [Parameter(Mandatory=$true)]
    [string]$Email,
    
    [Parameter(Mandatory=$true)]
    [string]$DistributionLists
)

try {
    Connect-ExchangeOnline -UserPrincipalName $env:O365_ADMIN_USER -ShowProgress $false
    
    $ListArray = $DistributionLists -split ','
    
    foreach ($List in $ListArray) {
        $List = $List.Trim()
        
        try {
            Add-DistributionGroupMember -Identity $List -Member $Email
            
            Write-Host "Successfully added $Email to distribution list: $List"
        } catch {
            Write-Warning "Could not add $Email to $List: $($_.Exception.Message)"
        }
    }
    
    Write-Host "Distribution list assignment completed for $Email"
    
    Disconnect-ExchangeOnline -Confirm:$false
    
    exit 0
    
} catch {
    Write-Error "Error assigning distribution lists: $($_.Exception.Message)"
    Disconnect-ExchangeOnline -Confirm:$false
    exit 1
}
