import os
import subprocess
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def assign_department_security_groups(employee):
    """
    Assign security groups based on department and role
    """
    try:
        script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'assign_department_groups.ps1')
        
        department_groups = {
            'IT': {
                'groups': ['IT-Department', 'IT-Admins', 'Server-Access', 'Network-Access'],
                'permissions': ['Full-Control'],
                'shared_drives': ['\\\\server\\IT$', '\\\\server\\Software$', '\\\\server\\Scripts$']
            },
            'HR': {
                'groups': ['HR-Department', 'HR-Managers', 'Employee-Data-Access', 'HR-Systems'],
                'permissions': ['Read-Write'],
                'shared_drives': ['\\\\server\\HR$', '\\\\server\\Employee-Files$', '\\\\server\\Policies$']
            },
            'Finance': {
                'groups': ['Finance-Department', 'Financial-Systems', 'Budget-Access', 'Accounting-Software'],
                'permissions': ['Read-Write'],
                'shared_drives': ['\\\\server\\Finance$', '\\\\server\\Accounting$', '\\\\server\\Reports$']
            },
            'Sales': {
                'groups': ['Sales-Department', 'CRM-Access', 'Sales-Tools', 'Customer-Data'],
                'permissions': ['Read-Write'],
                'shared_drives': ['\\\\server\\Sales$', '\\\\server\\CRM-Data$', '\\\\server\\Proposals$']
            },
            'Marketing': {
                'groups': ['Marketing-Department', 'Marketing-Tools', 'Social-Media-Access', 'Creative-Software'],
                'permissions': ['Read-Write'],
                'shared_drives': ['\\\\server\\Marketing$', '\\\\server\\Assets$', '\\\\server\\Campaigns$']
            }
        }
        
        dept_config = department_groups.get(employee.department, {
            'groups': ['General-Users'],
            'permissions': ['Read'],
            'shared_drives': ['\\\\server\\General$']
        })
        
        cmd = [
            'powershell.exe',
            '-ExecutionPolicy', 'Bypass',
            '-File', script_path,
            '-EmployeeID', employee.employee_id,
            '-Groups', ','.join(dept_config['groups']),
            '-Permissions', ','.join(dept_config['permissions']),
            '-SharedDrives', ','.join(dept_config['shared_drives'])
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            logger.info(f"Successfully assigned security groups for {employee.employee_id}")
            return {
                'success': True,
                'message': 'Security groups assigned successfully',
                'groups': dept_config['groups'],
                'permissions': dept_config['permissions'],
                'shared_drives': dept_config['shared_drives'],
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

def create_home_directory(employee):
    """
    Create home directory for employee
    """
    try:
        script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'create_home_directory.ps1')
        
        home_path = f"\\\\server\\Home$\\{employee.employee_id}"
        
        cmd = [
            'powershell.exe',
            '-ExecutionPolicy', 'Bypass',
            '-File', script_path,
            '-EmployeeID', employee.employee_id,
            '-HomePath', home_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            logger.info(f"Successfully created home directory for {employee.employee_id}")
            return {
                'success': True,
                'message': 'Home directory created successfully',
                'home_path': home_path,
                'output': result.stdout
            }
        else:
            logger.error(f"Failed to create home directory: {result.stderr}")
            return {
                'success': False,
                'message': 'Failed to create home directory',
                'error': result.stderr
            }
            
    except Exception as e:
        logger.error(f"Error creating home directory: {str(e)}")
        return {
            'success': False,
            'message': 'Error creating home directory',
            'error': str(e)
        }

def setup_folder_redirection(employee):
    """
    Setup folder redirection for Documents, Desktop, etc.
    """
    try:
        script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'setup_folder_redirection.ps1')
        
        home_path = f"\\\\server\\Home$\\{employee.employee_id}"
        
        cmd = [
            'powershell.exe',
            '-ExecutionPolicy', 'Bypass',
            '-File', script_path,
            '-EmployeeID', employee.employee_id,
            '-HomePath', home_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            logger.info(f"Successfully setup folder redirection for {employee.employee_id}")
            return {
                'success': True,
                'message': 'Folder redirection setup successfully',
                'output': result.stdout
            }
        else:
            logger.error(f"Failed to setup folder redirection: {result.stderr}")
            return {
                'success': False,
                'message': 'Failed to setup folder redirection',
                'error': result.stderr
            }
            
    except Exception as e:
        logger.error(f"Error setting up folder redirection: {str(e)}")
        return {
            'success': False,
            'message': 'Error setting up folder redirection',
            'error': str(e)
        }

def configure_printers(employee):
    """
    Configure department-specific printers
    """
    try:
        script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'configure_printers.ps1')
        
        department_printers = {
            'IT': ['IT-Printer-Color', 'IT-Printer-BW', 'IT-Plotter'],
            'HR': ['HR-Printer-Color', 'HR-Printer-BW'],
            'Finance': ['Finance-Printer-BW', 'Finance-Printer-Color'],
            'Sales': ['Sales-Printer-Color', 'Sales-Printer-BW'],
            'Marketing': ['Marketing-Printer-Color', 'Marketing-Printer-BW', 'Marketing-Plotter']
        }
        
        printers = department_printers.get(employee.department, ['General-Printer'])
        
        cmd = [
            'powershell.exe',
            '-ExecutionPolicy', 'Bypass',
            '-File', script_path,
            '-EmployeeID', employee.employee_id,
            '-Printers', ','.join(printers)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            logger.info(f"Successfully configured printers for {employee.employee_id}")
            return {
                'success': True,
                'message': 'Printers configured successfully',
                'printers': printers,
                'output': result.stdout
            }
        else:
            logger.error(f"Failed to configure printers: {result.stderr}")
            return {
                'success': False,
                'message': 'Failed to configure printers',
                'error': result.stderr
            }
            
    except Exception as e:
        logger.error(f"Error configuring printers: {str(e)}")
        return {
            'success': False,
            'message': 'Error configuring printers',
            'error': str(e)
        }

def setup_drive_mappings(employee):
    """
    Setup network drive mappings
    """
    try:
        script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'setup_drive_mappings.ps1')
        
        department_drives = {
            'IT': {
                'H:': '\\\\server\\IT$',
                'S:': '\\\\server\\Software$',
                'T:': '\\\\server\\Scripts$'
            },
            'HR': {
                'H:': '\\\\server\\HR$',
                'E:': '\\\\server\\Employee-Files$',
                'P:': '\\\\server\\Policies$'
            },
            'Finance': {
                'F:': '\\\\server\\Finance$',
                'A:': '\\\\server\\Accounting$',
                'R:': '\\\\server\\Reports$'
            },
            'Sales': {
                'S:': '\\\\server\\Sales$',
                'C:': '\\\\server\\CRM-Data$',
                'P:': '\\\\server\\Proposals$'
            },
            'Marketing': {
                'M:': '\\\\server\\Marketing$',
                'A:': '\\\\server\\Assets$',
                'C:': '\\\\server\\Campaigns$'
            }
        }
        
        drives = department_drives.get(employee.department, {
            'G:': '\\\\server\\General$'
        })
        
        drive_mappings = ','.join([f"{drive}:{path}" for drive, path in drives.items()])
        
        cmd = [
            'powershell.exe',
            '-ExecutionPolicy', 'Bypass',
            '-File', script_path,
            '-EmployeeID', employee.employee_id,
            '-DriveMappings', drive_mappings
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            logger.info(f"Successfully setup drive mappings for {employee.employee_id}")
            return {
                'success': True,
                'message': 'Drive mappings setup successfully',
                'drives': drives,
                'output': result.stdout
            }
        else:
            logger.error(f"Failed to setup drive mappings: {result.stderr}")
            return {
                'success': False,
                'message': 'Failed to setup drive mappings',
                'error': result.stderr
            }
            
    except Exception as e:
        logger.error(f"Error setting up drive mappings: {str(e)}")
        return {
            'success': False,
            'message': 'Error setting up drive mappings',
            'error': str(e)
        }
