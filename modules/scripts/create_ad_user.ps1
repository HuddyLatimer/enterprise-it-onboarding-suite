param(
    [Parameter(Mandatory=$true)]
    [string]$EmployeeID,
    
    [Parameter(Mandatory=$true)]
    [string]$FirstName,
    
    [Parameter(Mandatory=$true)]
    [string]$LastName,
    
    [Parameter(Mandatory=$true)]
    [string]$Email,
    
    [Parameter(Mandatory=$true)]
    [string]$Department,
    
    [Parameter(Mandatory=$true)]
    [string]$Password,
    
    [Parameter(Mandatory=$true)]
    [string]$OU
)

try {
    Import-Module ActiveDirectory -ErrorAction Stop
    
    $SamAccountName = $EmployeeID.ToLower()
    $DisplayName = "$FirstName $LastName"
    $UserPrincipalName = $Email
    
    $UserParams = @{
        SamAccountName = $SamAccountName
        Name = $DisplayName
        DisplayName = $DisplayName
        GivenName = $FirstName
        Surname = $LastName
        EmailAddress = $Email
        UserPrincipalName = $UserPrincipalName
        Path = $OU
        AccountPassword = (ConvertTo-SecureString $Password -AsPlainText -Force)
        Enabled = $true
        ChangePasswordAtLogon = $true
        Description = "Auto-created user for $Department department"
    }
    
    $NewUser = New-ADUser @UserParams
    
    if ($NewUser) {
        Write-Host "Successfully created AD user: $SamAccountName"
        Write-Host "User DN: $($NewUser.DistinguishedName)"
        
        Set-ADUser -Identity $SamAccountName -Add @{
            'department' = $Department
            'title' = "Employee"
            'company' = "Your Company Name"
        }
        
        Write-Host "User attributes updated successfully"
        exit 0
    } else {
        Write-Error "Failed to create AD user"
        exit 1
    }
    
} catch {
    Write-Error "Error creating AD user: $($_.Exception.Message)"
    exit 1
}
