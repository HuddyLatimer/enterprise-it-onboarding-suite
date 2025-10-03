import os
import subprocess
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def create_ad_user(employee, temp_password):
    """
    Create Active Directory user account using PowerShell
    """
    try:
        script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'create_ad_user.ps1')
        
        cmd = [
            'powershell.exe',
            '-ExecutionPolicy', 'Bypass',
            '-File', script_path,
            '-EmployeeID', employee.employee_id,
            '-FirstName', employee.first_name,
            '-LastName', employee.last_name,
            '-Email', employee.email,
            '-Department', employee.department,
            '-Password', temp_password,
            '-OU', f"OU={employee.department},OU=Users,{os.getenv('AD_BASE_DN')}"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            logger.info(f"Successfully created AD user for {employee.employee_id}")
            return {
                'success': True,
                'message': 'AD user created successfully',
                'output': result.stdout
            }
        else:
            logger.error(f"Failed to create AD user: {result.stderr}")
            return {
                'success': False,
                'message': 'Failed to create AD user',
                'error': result.stderr
            }
            
    except subprocess.TimeoutExpired:
        logger.error("AD user creation timed out")
        return {
            'success': False,
            'message': 'AD user creation timed out',
            'error': 'Timeout'
        }
    except Exception as e:
        logger.error(f"Error creating AD user: {str(e)}")
        return {
            'success': False,
            'message': 'Error creating AD user',
            'error': str(e)
        }

def assign_security_groups(employee):
    """
    Assign security groups based on department
    """
    try:
        script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'assign_security_groups.ps1')
        
        department_groups = {
            'IT': ['IT-Department', 'IT-Admins', 'Server-Access'],
            'HR': ['HR-Department', 'HR-Managers', 'Employee-Data-Access'],
            'Finance': ['Finance-Department', 'Financial-Systems', 'Budget-Access'],
            'Sales': ['Sales-Department', 'CRM-Access', 'Sales-Tools'],
            'Marketing': ['Marketing-Department', 'Marketing-Tools', 'Social-Media-Access']
        }
        
        groups = department_groups.get(employee.department, ['General-Users'])
        
        cmd = [
            'powershell.exe',
            '-ExecutionPolicy', 'Bypass',
            '-File', script_path,
            '-EmployeeID', employee.employee_id,
            '-Groups', ','.join(groups)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            logger.info(f"Successfully assigned security groups for {employee.employee_id}")
            return {
                'success': True,
                'message': 'Security groups assigned successfully',
                'groups': groups,
                'output': result.stdout
            }
        else:
            logger.error(f"Failed to assign security groups: {result.stderr}")
            return {
                'success': False,
                'message': 'Failed to assign security groups',
                'error': result.stderr
            }
            
    except Exception as e:
        logger.error(f"Error assigning security groups: {str(e)}")
        return {
            'success': False,
            'message': 'Error assigning security groups',
            'error': str(e)
        }

def create_shared_drive_access(employee):
    """
    Create shared drive access based on department
    """
    try:
        script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'create_shared_access.ps1')
        
        department_drives = {
            'IT': ['\\\\server\\IT$', '\\\\server\\Software$'],
            'HR': ['\\\\server\\HR$', '\\\\server\\Employee-Files$'],
            'Finance': ['\\\\server\\Finance$', '\\\\server\\Accounting$'],
            'Sales': ['\\\\server\\Sales$', '\\\\server\\CRM-Data$'],
            'Marketing': ['\\\\server\\Marketing$', '\\\\server\\Assets$']
        }
        
        drives = department_drives.get(employee.department, ['\\\\server\\General$'])
        
        cmd = [
            'powershell.exe',
            '-ExecutionPolicy', 'Bypass',
            '-File', script_path,
            '-EmployeeID', employee.employee_id,
            '-Drives', ','.join(drives)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            logger.info(f"Successfully created shared drive access for {employee.employee_id}")
            return {
                'success': True,
                'message': 'Shared drive access created successfully',
                'drives': drives,
                'output': result.stdout
            }
        else:
            logger.error(f"Failed to create shared drive access: {result.stderr}")
            return {
                'success': False,
                'message': 'Failed to create shared drive access',
                'error': result.stderr
            }
            
    except Exception as e:
        logger.error(f"Error creating shared drive access: {str(e)}")
        return {
            'success': False,
            'message': 'Error creating shared drive access',
            'error': str(e)
        }
