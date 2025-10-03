import os
import subprocess
import logging
import requests
import json
from datetime import datetime

logger = logging.getLogger(__name__)

def create_mailbox(employee):
    """
    Create O365 mailbox using PowerShell Exchange Online
    """
    try:
        script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'create_o365_mailbox.ps1')
        
        cmd = [
            'powershell.exe',
            '-ExecutionPolicy', 'Bypass',
            '-File', script_path,
            '-Email', employee.email,
            '-FirstName', employee.first_name,
            '-LastName', employee.last_name,
            '-Department', employee.department
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            logger.info(f"Successfully created O365 mailbox for {employee.email}")
            return {
                'success': True,
                'message': 'O365 mailbox created successfully',
                'output': result.stdout
            }
        else:
            logger.error(f"Failed to create O365 mailbox: {result.stderr}")
            return {
                'success': False,
                'message': 'Failed to create O365 mailbox',
                'error': result.stderr
            }
            
    except subprocess.TimeoutExpired:
        logger.error("O365 mailbox creation timed out")
        return {
            'success': False,
            'message': 'O365 mailbox creation timed out',
            'error': 'Timeout'
        }
    except Exception as e:
        logger.error(f"Error creating O365 mailbox: {str(e)}")
        return {
            'success': False,
            'message': 'Error creating O365 mailbox',
            'error': str(e)
        }

def assign_distribution_lists(employee):
    """
    Assign user to department-specific distribution lists
    """
    try:
        script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'assign_distribution_lists.ps1')
        
        department_lists = {
            'IT': ['IT-All', 'IT-Announcements', 'IT-Support'],
            'HR': ['HR-All', 'HR-Announcements', 'HR-Policies'],
            'Finance': ['Finance-All', 'Finance-Reports', 'Finance-Updates'],
            'Sales': ['Sales-All', 'Sales-Targets', 'Sales-Updates'],
            'Marketing': ['Marketing-All', 'Marketing-Campaigns', 'Marketing-Assets']
        }
        
        lists = department_lists.get(employee.department, ['Company-All'])
        
        cmd = [
            'powershell.exe',
            '-ExecutionPolicy', 'Bypass',
            '-File', script_path,
            '-Email', employee.email,
            '-DistributionLists', ','.join(lists)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            logger.info(f"Successfully assigned distribution lists for {employee.email}")
            return {
                'success': True,
                'message': 'Distribution lists assigned successfully',
                'lists': lists,
                'output': result.stdout
            }
        else:
            logger.error(f"Failed to assign distribution lists: {result.stderr}")
            return {
                'success': False,
                'message': 'Failed to assign distribution lists',
                'error': result.stderr
            }
            
    except Exception as e:
        logger.error(f"Error assigning distribution lists: {str(e)}")
        return {
            'success': False,
            'message': 'Error assigning distribution lists',
            'error': str(e)
        }

def set_mailbox_quota(employee):
    """
    Set mailbox quota based on department
    """
    try:
        script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'set_mailbox_quota.ps1')
        
        quota_sizes = {
            'IT': '50GB',
            'HR': '25GB',
            'Finance': '25GB',
            'Sales': '30GB',
            'Marketing': '40GB'
        }
        
        quota_size = quota_sizes.get(employee.department, '25GB')
        
        cmd = [
            'powershell.exe',
            '-ExecutionPolicy', 'Bypass',
            '-File', script_path,
            '-Email', employee.email,
            '-QuotaSize', quota_size
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            logger.info(f"Successfully set mailbox quota for {employee.email}")
            return {
                'success': True,
                'message': 'Mailbox quota set successfully',
                'quota_size': quota_size,
                'output': result.stdout
            }
        else:
            logger.error(f"Failed to set mailbox quota: {result.stderr}")
            return {
                'success': False,
                'message': 'Failed to set mailbox quota',
                'error': result.stderr
            }
            
    except Exception as e:
        logger.error(f"Error setting mailbox quota: {str(e)}")
        return {
            'success': False,
            'message': 'Error setting mailbox quota',
            'error': str(e)
        }

def create_email_signature(employee):
    """
    Create standardized email signature
    """
    try:
        script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'create_email_signature.ps1')
        
        cmd = [
            'powershell.exe',
            '-ExecutionPolicy', 'Bypass',
            '-File', script_path,
            '-Email', employee.email,
            '-FirstName', employee.first_name,
            '-LastName', employee.last_name,
            '-Department', employee.department,
            '-Position', employee.position,
            '-Phone', employee.phone or 'N/A'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            logger.info(f"Successfully created email signature for {employee.email}")
            return {
                'success': True,
                'message': 'Email signature created successfully',
                'output': result.stdout
            }
        else:
            logger.error(f"Failed to create email signature: {result.stderr}")
            return {
                'success': False,
                'message': 'Failed to create email signature',
                'error': result.stderr
            }
            
    except Exception as e:
        logger.error(f"Error creating email signature: {str(e)}")
        return {
            'success': False,
            'message': 'Error creating email signature',
            'error': str(e)
        }
