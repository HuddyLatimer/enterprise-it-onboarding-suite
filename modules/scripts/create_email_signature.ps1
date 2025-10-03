param(
    [Parameter(Mandatory=$true)]
    [string]$Email,
    
    [Parameter(Mandatory=$true)]
    [string]$FirstName,
    
    [Parameter(Mandatory=$true)]
    [string]$LastName,
    
    [Parameter(Mandatory=$true)]
    [string]$Department,
    
    [Parameter(Mandatory=$true)]
    [string]$Position,
    
    [Parameter(Mandatory=$true)]
    [string]$Phone
)

try {
    Connect-ExchangeOnline -UserPrincipalName $env:O365_ADMIN_USER -ShowProgress $false
    
    $SignatureHTML = @"
<div style="font-family: Arial, sans-serif; font-size: 12px; color: #333333;">
    <br>
    <strong>$FirstName $LastName</strong><br>
    $Position<br>
    $Department Department<br>
    <br>
    Email: $Email<br>
    Phone: $Phone<br>
    <br>
    <em>This email and any attachments are confidential and may be legally privileged. If you are not the intended recipient, please notify the sender immediately and delete this email.</em>
</div>
"@
    
    Set-MailboxMessageConfiguration -Identity $Email -SignatureHTML $SignatureHTML -AutoAddSignature $true
    
    Write-Host "Successfully created email signature for $Email"
    
    Disconnect-ExchangeOnline -Confirm:$false
    
    exit 0
    
} catch {
    Write-Error "Error creating email signature: $($_.Exception.Message)"
    Disconnect-ExchangeOnline -Confirm:$false
    exit 1
}
