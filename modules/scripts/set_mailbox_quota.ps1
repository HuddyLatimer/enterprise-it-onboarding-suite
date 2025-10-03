param(
    [Parameter(Mandatory=$true)]
    [string]$Email,
    
    [Parameter(Mandatory=$true)]
    [string]$QuotaSize
)

try {
    Connect-ExchangeOnline -UserPrincipalName $env:O365_ADMIN_USER -ShowProgress $false
    
    Set-Mailbox -Identity $Email -ProhibitSendQuota $QuotaSize -ProhibitSendReceiveQuota $QuotaSize -IssueWarningQuota $QuotaSize
    
    Write-Host "Successfully set mailbox quota for $Email to $QuotaSize"
    
    Disconnect-ExchangeOnline -Confirm:$false
    
    exit 0
    
} catch {
    Write-Error "Error setting mailbox quota: $($_.Exception.Message)"
    Disconnect-ExchangeOnline -Confirm:$false
    exit 1
}
