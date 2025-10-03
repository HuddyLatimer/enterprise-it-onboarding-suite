import os
import subprocess
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

def deploy_software_packages(employee):
    """
    Deploy software packages based on department requirements
    """
    try:
        department_software = {
            'IT': [
                'microsoft-office365business',
                'microsoft-teams',
                'visual-studio-code',
                'git',
                'docker-desktop',
                'postman',
                'notepadplusplus',
                '7zip'
            ],
            'HR': [
                'microsoft-office365business',
                'microsoft-teams',
                'adobe-acrobat-reader',
                'google-chrome',
                'firefox',
                'vlc'
            ],
            'Finance': [
                'microsoft-office365business',
                'microsoft-teams',
                'adobe-acrobat-reader',
                'quickbooks',
                'google-chrome',
                '7zip'
            ],
            'Sales': [
                'microsoft-office365business',
                'microsoft-teams',
                'salesforce',
                'hubspot',
                'google-chrome',
                'zoom'
            ],
            'Marketing': [
                'microsoft-office365business',
                'microsoft-teams',
                'adobe-creative-cloud',
                'canva',
                'google-chrome',
                'firefox',
                'vlc'
            ]
        }
        
        software_list = department_software.get(employee.department, [
            'microsoft-office365business',
            'microsoft-teams',
            'google-chrome',
            '7zip'
        ])
        
        results = []
        
        for software in software_list:
            result = install_software_package(software)
            results.append({
                'package': software,
                'success': result['success'],
                'message': result['message']
            })
            
            if result['success']:
                logger.info(f"Successfully installed {software} for {employee.employee_id}")
            else:
                logger.error(f"Failed to install {software} for {employee.employee_id}: {result['message']}")
        
        success_count = sum(1 for r in results if r['success'])
        total_count = len(results)
        
        return {
            'success': success_count > 0,
            'message': f'Installed {success_count}/{total_count} software packages',
            'results': results,
            'success_count': success_count,
            'total_count': total_count
        }
        
    except Exception as e:
        logger.error(f"Error deploying software packages: {str(e)}")
        return {
            'success': False,
            'message': 'Error deploying software packages',
            'error': str(e)
        }

def install_software_package(package_name):
    """
    Install a single software package using Chocolatey or Winget
    """
    try:
        chocolatey_path = os.getenv('CHOCOLATEY_PATH', 'C:\\ProgramData\\chocolatey\\bin\\choco.exe')
        
        if os.path.exists(chocolatey_path):
            return install_with_chocolatey(package_name, chocolatey_path)
        else:
            return install_with_winget(package_name)
            
    except Exception as e:
        logger.error(f"Error installing package {package_name}: {str(e)}")
        return {
            'success': False,
            'message': f'Error installing {package_name}',
            'error': str(e)
        }

def install_with_chocolatey(package_name, chocolatey_path):
    """
    Install software using Chocolatey
    """
    try:
        cmd = [
            chocolatey_path,
            'install',
            package_name,
            '--yes',
            '--no-progress'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            return {
                'success': True,
                'message': f'Successfully installed {package_name} via Chocolatey',
                'method': 'chocolatey',
                'output': result.stdout
            }
        else:
            return {
                'success': False,
                'message': f'Failed to install {package_name} via Chocolatey',
                'method': 'chocolatey',
                'error': result.stderr
            }
            
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'message': f'Timeout installing {package_name} via Chocolatey',
            'method': 'chocolatey',
            'error': 'Timeout'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error installing {package_name} via Chocolatey',
            'method': 'chocolatey',
            'error': str(e)
        }

def install_with_winget(package_name):
    """
    Install software using Winget
    """
    try:
        cmd = [
            'winget',
            'install',
            package_name,
            '--accept-package-agreements',
            '--accept-source-agreements',
            '--silent'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            return {
                'success': True,
                'message': f'Successfully installed {package_name} via Winget',
                'method': 'winget',
                'output': result.stdout
            }
        else:
            return {
                'success': False,
                'message': f'Failed to install {package_name} via Winget',
                'method': 'winget',
                'error': result.stderr
            }
            
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'message': f'Timeout installing {package_name} via Winget',
            'method': 'winget',
            'error': 'Timeout'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error installing {package_name} via Winget',
            'method': 'winget',
            'error': str(e)
        }

def create_software_deployment_script(employee):
    """
    Create a PowerShell script for software deployment
    """
    try:
        script_content = f"""
# Software Deployment Script for {employee.first_name} {employee.last_name}
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Write-Host "Starting software deployment for {employee.employee_id}" -ForegroundColor Green

# Check if Chocolatey is installed
$chocolateyPath = "{os.getenv('CHOCOLATEY_PATH', 'C:\\ProgramData\\chocolatey\\bin\\choco.exe')}"
$useChocolatey = Test-Path $chocolateyPath

if ($useChocolatey) {{
    Write-Host "Using Chocolatey for software installation" -ForegroundColor Yellow
}} else {{
    Write-Host "Using Winget for software installation" -ForegroundColor Yellow
}}

# Software packages to install
$packages = @(
    "microsoft-office365business",
    "microsoft-teams",
    "google-chrome",
    "7zip"
)

# Department-specific packages
$departmentPackages = @{{
    "IT" = @("visual-studio-code", "git", "docker-desktop", "postman", "notepadplusplus")
    "HR" = @("adobe-acrobat-reader", "firefox", "vlc")
    "Finance" = @("adobe-acrobat-reader", "quickbooks")
    "Sales" = @("salesforce", "hubspot", "zoom")
    "Marketing" = @("adobe-creative-cloud", "canva", "firefox", "vlc")
}}

# Add department-specific packages
$deptPackages = $departmentPackages["{employee.department}"]
if ($deptPackages) {{
    $packages += $deptPackages
}}

# Install packages
foreach ($package in $packages) {{
    Write-Host "Installing $package..." -ForegroundColor Cyan
    
    if ($useChocolatey) {{
        & $chocolateyPath install $package --yes --no-progress
    }} else {{
        winget install $package --accept-package-agreements --accept-source-agreements --silent
    }}
    
    if ($LASTEXITCODE -eq 0) {{
        Write-Host "Successfully installed $package" -ForegroundColor Green
    }} else {{
        Write-Host "Failed to install $package" -ForegroundColor Red
    }}
}}

Write-Host "Software deployment completed for {employee.employee_id}" -ForegroundColor Green
"""
        
        script_path = os.path.join(os.path.dirname(__file__), 'scripts', f'deploy_software_{employee.employee_id}.ps1')
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        logger.info(f"Created software deployment script for {employee.employee_id}")
        return {
            'success': True,
            'message': 'Software deployment script created',
            'script_path': script_path
        }
        
    except Exception as e:
        logger.error(f"Error creating software deployment script: {str(e)}")
        return {
            'success': False,
            'message': 'Error creating software deployment script',
            'error': str(e)
        }

def execute_software_deployment_script(employee):
    """
    Execute the software deployment script
    """
    try:
        script_path = os.path.join(os.path.dirname(__file__), 'scripts', f'deploy_software_{employee.employee_id}.ps1')
        
        if not os.path.exists(script_path):
            create_result = create_software_deployment_script(employee)
            if not create_result['success']:
                return create_result
        
        cmd = [
            'powershell.exe',
            '-ExecutionPolicy', 'Bypass',
            '-File', script_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            logger.info(f"Successfully executed software deployment for {employee.employee_id}")
            return {
                'success': True,
                'message': 'Software deployment completed successfully',
                'output': result.stdout
            }
        else:
            logger.error(f"Failed to execute software deployment: {result.stderr}")
            return {
                'success': False,
                'message': 'Failed to execute software deployment',
                'error': result.stderr
            }
            
    except subprocess.TimeoutExpired:
        logger.error("Software deployment timed out")
        return {
            'success': False,
            'message': 'Software deployment timed out',
            'error': 'Timeout'
        }
    except Exception as e:
        logger.error(f"Error executing software deployment: {str(e)}")
        return {
            'success': False,
            'message': 'Error executing software deployment',
            'error': str(e)
        }

def get_installed_software(employee):
    """
    Get list of installed software for verification
    """
    try:
        cmd = [
            'powershell.exe',
            '-Command',
            'Get-WmiObject -Class Win32_Product | Select-Object Name, Version | ConvertTo-Json'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            try:
                software_list = json.loads(result.stdout)
                logger.info(f"Retrieved installed software list for {employee.employee_id}")
                return {
                    'success': True,
                    'message': 'Retrieved installed software list',
                    'software': software_list
                }
            except json.JSONDecodeError:
                return {
                    'success': False,
                    'message': 'Failed to parse software list',
                    'error': 'JSON decode error'
                }
        else:
            logger.error(f"Failed to get installed software: {result.stderr}")
            return {
                'success': False,
                'message': 'Failed to get installed software',
                'error': result.stderr
            }
            
    except Exception as e:
        logger.error(f"Error getting installed software: {str(e)}")
        return {
            'success': False,
            'message': 'Error getting installed software',
            'error': str(e)
        }
