param(
    [Parameter(Mandatory=$true)]
    [string]$EmployeeID,
    
    [Parameter(Mandatory=$true)]
    [string]$Printers
)

try {
    $SamAccountName = $EmployeeID.ToLower()
    $PrinterList = $Printers -split ','
    
    foreach ($Printer in $PrinterList) {
        $Printer = $Printer.Trim()
        
        try {
            Add-Printer -ConnectionName "\\\\printserver\\$Printer" -ErrorAction Stop
            
            Write-Host "Successfully added printer: $Printer"
        } catch {
            Write-Warning "Could not add printer $Printer: $($_.Exception.Message)"
        }
    }
    
    Write-Host "Printer configuration completed for $SamAccountName"
    exit 0
    
} catch {
    Write-Error "Error configuring printers: $($_.Exception.Message)"
    exit 1
}
