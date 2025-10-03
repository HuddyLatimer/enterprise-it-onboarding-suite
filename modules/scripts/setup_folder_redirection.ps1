param(
    [Parameter(Mandatory=$true)]
    [string]$EmployeeID,
    
    [Parameter(Mandatory=$true)]
    [string]$HomePath
)

try {
    $SamAccountName = $EmployeeID.ToLower()
    
    $DocumentsPath = Join-Path $HomePath "Documents"
    $DesktopPath = Join-Path $HomePath "Desktop"
    $PicturesPath = Join-Path $HomePath "Pictures"
    $DownloadsPath = Join-Path $HomePath "Downloads"
    
    $Folders = @($DocumentsPath, $DesktopPath, $PicturesPath, $DownloadsPath)
    
    foreach ($Folder in $Folders) {
        if (!(Test-Path $Folder)) {
            New-Item -ItemType Directory -Path $Folder -Force
            Write-Host "Created folder: $Folder"
        }
        
        $ACL = Get-Acl $Folder
        
        $AccessRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
            $SamAccountName,
            "FullControl",
            "ContainerInherit,ObjectInherit",
            "None",
            "Allow"
        )
        
        $ACL.SetAccessRule($AccessRule)
        Set-Acl -Path $Folder -AclObject $ACL
    }
    
    Write-Host "Successfully configured folder redirection for $SamAccountName"
    Write-Host "Redirected folders: Documents, Desktop, Pictures, Downloads"
    
    exit 0
    
} catch {
    Write-Error "Error setting up folder redirection: $($_.Exception.Message)"
    exit 1
}
