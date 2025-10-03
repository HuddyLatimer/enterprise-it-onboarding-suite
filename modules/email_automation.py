import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import json

logger = logging.getLogger(__name__)

def send_welcome_email(employee, temp_password):
    """
    Send welcome email to new employee with credentials and instructions
    """
    try:
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = employee.email
        msg['Cc'] = employee.manager_email
        msg['Subject'] = f"Welcome to the Team - {employee.first_name} {employee.last_name}"
        
        body = create_welcome_email_body(employee, temp_password)
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        
        recipients = [employee.email, employee.manager_email]
        text = msg.as_string()
        
        server.sendmail(smtp_username, recipients, text)
        server.quit()
        
        logger.info(f"Successfully sent welcome email to {employee.email}")
        return {
            'success': True,
            'message': 'Welcome email sent successfully',
            'recipients': recipients
        }
        
    except Exception as e:
        logger.error(f"Error sending welcome email: {str(e)}")
        return {
            'success': False,
            'message': 'Failed to send welcome email',
            'error': str(e)
        }

def create_welcome_email_body(employee, temp_password):
    """
    Create HTML email body for welcome message
    """
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f8f9fa; }}
            .credentials {{ background-color: #e8f4fd; padding: 15px; border-left: 4px solid #007bff; margin: 20px 0; }}
            .footer {{ background-color: #6c757d; color: white; padding: 15px; text-align: center; font-size: 12px; }}
            .button {{ background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Welcome to the Team!</h1>
            </div>
            
            <div class="content">
                <p>Dear {employee.first_name},</p>
                
                <p>Welcome to our company! We're excited to have you join the {employee.department} team as a {employee.position}.</p>
                
                <p>Your start date is scheduled for <strong>{employee.start_date}</strong> at our {employee.location} location.</p>
                
                <div class="credentials">
                    <h3>Your Login Credentials</h3>
                    <p><strong>Username:</strong> {employee.email}</p>
                    <p><strong>Temporary Password:</strong> {temp_password}</p>
                    <p><strong>Important:</strong> You will be required to change this password on your first login.</p>
                </div>
                
                <h3>Next Steps:</h3>
                <ol>
                    <li>Report to the IT department on your first day to receive your equipment</li>
                    <li>Log in to your computer using the credentials above</li>
                    <li>Change your password when prompted</li>
                    <li>Check your email for additional setup instructions</li>
                    <li>Complete the new employee orientation</li>
                </ol>
                
                <h3>Important Information:</h3>
                <ul>
                    <li>Your manager is: {employee.manager_email}</li>
                    <li>IT Support: it-support@company.com</li>
                    <li>HR Contact: hr@company.com</li>
                    <li>Emergency Contact: security@company.com</li>
                </ul>
                
                <p>If you have any questions before your start date, please don't hesitate to reach out to your manager or the HR department.</p>
                
                <p>We look forward to working with you!</p>
                
                <p>Best regards,<br>
                IT Onboarding Team</p>
            </div>
            
            <div class="footer">
                <p>This is an automated message. Please do not reply to this email.</p>
                <p>For technical support, contact IT Support at it-support@company.com</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_body

def send_manager_notification(employee, temp_password):
    """
    Send notification email to manager about new employee
    """
    try:
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = employee.manager_email
        msg['Subject'] = f"New Employee Onboarding - {employee.first_name} {employee.last_name}"
        
        body = create_manager_notification_body(employee, temp_password)
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        
        text = msg.as_string()
        server.sendmail(smtp_username, employee.manager_email, text)
        server.quit()
        
        logger.info(f"Successfully sent manager notification to {employee.manager_email}")
        return {
            'success': True,
            'message': 'Manager notification sent successfully'
        }
        
    except Exception as e:
        logger.error(f"Error sending manager notification: {str(e)}")
        return {
            'success': False,
            'message': 'Failed to send manager notification',
            'error': str(e)
        }

def create_manager_notification_body(employee, temp_password):
    """
    Create HTML email body for manager notification
    """
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #28a745; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f8f9fa; }}
            .info-box {{ background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; }}
            .footer {{ background-color: #6c757d; color: white; padding: 15px; text-align: center; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>New Employee Onboarding Complete</h1>
            </div>
            
            <div class="content">
                <p>Dear Manager,</p>
                
                <p>The onboarding process for your new team member has been initiated:</p>
                
                <div class="info-box">
                    <h3>Employee Information</h3>
                    <p><strong>Name:</strong> {employee.first_name} {employee.last_name}</p>
                    <p><strong>Position:</strong> {employee.position}</p>
                    <p><strong>Department:</strong> {employee.department}</p>
                    <p><strong>Start Date:</strong> {employee.start_date}</p>
                    <p><strong>Email:</strong> {employee.email}</p>
                    <p><strong>Temporary Password:</strong> {temp_password}</p>
                </div>
                
                <h3>Onboarding Status:</h3>
                <ul>
                    <li>✓ Active Directory account created</li>
                    <li>✓ O365 mailbox provisioned</li>
                    <li>✓ Security groups assigned</li>
                    <li>✓ Welcome email sent to employee</li>
                    <li>⏳ Equipment assignment (pending IT setup)</li>
                    <li>⏳ Software deployment (pending IT setup)</li>
                </ul>
                
                <h3>Manager Action Items:</h3>
                <ol>
                    <li>Schedule first-day meeting with the new employee</li>
                    <li>Prepare workstation and equipment</li>
                    <li>Review department policies and procedures</li>
                    <li>Introduce team members</li>
                    <li>Set up initial project assignments</li>
                </ol>
                
                <p>The employee will receive their login credentials via email. Please ensure they have access to their workstation on their first day.</p>
                
                <p>If you have any questions about the onboarding process, please contact the IT department.</p>
                
                <p>Best regards,<br>
                IT Onboarding Team</p>
            </div>
            
            <div class="footer">
                <p>This is an automated notification. For support, contact IT Support at it-support@company.com</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_body

def send_onboarding_completion_email(employee):
    """
    Send completion email when all onboarding tasks are finished
    """
    try:
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = employee.email
        msg['Cc'] = employee.manager_email
        msg['Subject'] = f"Onboarding Complete - {employee.first_name} {employee.last_name}"
        
        body = create_completion_email_body(employee)
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        
        recipients = [employee.email, employee.manager_email]
        text = msg.as_string()
        
        server.sendmail(smtp_username, recipients, text)
        server.quit()
        
        logger.info(f"Successfully sent completion email to {employee.email}")
        return {
            'success': True,
            'message': 'Completion email sent successfully',
            'recipients': recipients
        }
        
    except Exception as e:
        logger.error(f"Error sending completion email: {str(e)}")
        return {
            'success': False,
            'message': 'Failed to send completion email',
            'error': str(e)
        }

def create_completion_email_body(employee):
    """
    Create HTML email body for completion message
    """
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #28a745; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f8f9fa; }}
            .success-box {{ background-color: #d4edda; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0; }}
            .footer {{ background-color: #6c757d; color: white; padding: 15px; text-align: center; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Onboarding Complete!</h1>
            </div>
            
            <div class="content">
                <p>Dear {employee.first_name},</p>
                
                <div class="success-box">
                    <h3>🎉 Congratulations!</h3>
                    <p>Your IT onboarding process has been completed successfully. All systems are now ready for your use.</p>
                </div>
                
                <h3>What's Been Set Up:</h3>
                <ul>
                    <li>✓ Active Directory account</li>
                    <li>✓ Office 365 mailbox</li>
                    <li>✓ Security group memberships</li>
                    <li>✓ Shared drive access</li>
                    <li>✓ Equipment assignment</li>
                    <li>✓ Software installation</li>
                </ul>
                
                <h3>You're All Set!</h3>
                <p>You now have access to all the systems and resources you need to be productive. If you encounter any issues or need assistance, please don't hesitate to contact:</p>
                
                <ul>
                    <li><strong>IT Support:</strong> it-support@company.com</li>
                    <li><strong>Your Manager:</strong> {employee.manager_email}</li>
                    <li><strong>HR:</strong> hr@company.com</li>
                </ul>
                
                <p>Welcome aboard and best of luck in your new role!</p>
                
                <p>Best regards,<br>
                IT Onboarding Team</p>
            </div>
            
            <div class="footer">
                <p>This is an automated message. For support, contact IT Support at it-support@company.com</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_body
