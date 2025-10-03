param(
    [Parameter(Mandatory=$true)]
    [string]$Email,
    
    [Parameter(Mandatory=$true)]
    [string]$FirstName,
    
    [Parameter(Mandatory=$true)]
    [string]$LastName,
    
    [Parameter(Mandatory=$true)]
    [string]$Department
)

try {
    Connect-ExchangeOnline -UserPrincipalName $env:O365_ADMIN_USER -ShowProgress $false
    
    $DisplayName = "$FirstName $LastName"
    $Alias = $Email.Split('@')[0]
    
    Enable-Mailbox -Identity $Email -Alias $Alias
    
    Set-Mailbox -Identity $Email -DisplayName $DisplayName -PrimarySmtpAddress $Email
    
    Set-Mailbox -Identity $Email -CustomAttribute1 $Department
    
    Write-Host "Successfully created mailbox for: $Email"
    Write-Host "Display Name: $DisplayName"
    Write-Host "Alias: $Alias"
    Write-Host "Department: $Department"
    
    Disconnect-ExchangeOnline -Confirm:$false
    
    exit 0
    
} catch {
    Write-Error "Error creating O365 mailbox: $($_.Exception.Message)"
    Disconnect-ExchangeOnline -Confirm:$false
    exit 1
}
