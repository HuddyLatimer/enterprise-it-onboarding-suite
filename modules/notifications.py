import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request
from app import db, Employee, OnboardingLog
import schedule
import threading
import time

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')
logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self):
        self.notification_queue = []
        self.email_templates = self._load_email_templates()
        self.smtp_config = self._get_smtp_config()
        self.scheduler_running = False
    
    def _load_email_templates(self):
        """Load email notification templates"""
        return {
            'onboarding_started': {
                'subject': 'Onboarding Process Started - {employee_name}',
                'template': 'notifications/onboarding_started.html'
            },
            'onboarding_completed': {
                'subject': 'Onboarding Process Completed - {employee_name}',
                'template': 'notifications/onboarding_completed.html'
            },
            'onboarding_delayed': {
                'subject': 'Onboarding Process Delayed - {employee_name}',
                'template': 'notifications/onboarding_delayed.html'
            },
            'equipment_assigned': {
                'subject': 'Equipment Assigned - {employee_name}',
                'template': 'notifications/equipment_assigned.html'
            },
            'system_alert': {
                'subject': 'System Alert - {alert_type}',
                'template': 'notifications/system_alert.html'
            },
            'weekly_report': {
                'subject': 'Weekly Onboarding Report - {week_date}',
                'template': 'notifications/weekly_report.html'
            }
        }
    
    def _get_smtp_config(self):
        """Get SMTP configuration from environment"""
        return {
            'server': os.getenv('SMTP_SERVER'),
            'port': int(os.getenv('SMTP_PORT', 587)),
            'username': os.getenv('SMTP_USERNAME'),
            'password': os.getenv('SMTP_PASSWORD')
        }
    
    def send_notification(self, notification_type, recipients, data, priority='normal'):
        """Send notification to recipients"""
        try:
            template_config = self.email_templates.get(notification_type)
            if not template_config:
                logger.error(f"Unknown notification type: {notification_type}")
                return False
            
            subject = template_config['subject'].format(**data)
            
            notification = {
                'type': notification_type,
                'subject': subject,
                'recipients': recipients if isinstance(recipients, list) else [recipients],
                'data': data,
                'priority': priority,
                'created_at': datetime.now(),
                'status': 'pending'
            }
            
            self.notification_queue.append(notification)
            logger.info(f"Notification queued: {notification_type} for {len(recipients)} recipients")
            
            return True
            
        except Exception as e:
            logger.error(f"Error queuing notification: {str(e)}")
            return False
    
    def process_notification_queue(self):
        """Process pending notifications"""
        try:
            pending_notifications = [n for n in self.notification_queue if n['status'] == 'pending']
            
            for notification in pending_notifications:
                if self._send_email_notification(notification):
                    notification['status'] = 'sent'
                    notification['sent_at'] = datetime.now()
                else:
                    notification['status'] = 'failed'
                    notification['failed_at'] = datetime.now()
            
            logger.info(f"Processed {len(pending_notifications)} notifications")
            
        except Exception as e:
            logger.error(f"Error processing notification queue: {str(e)}")
    
    def _send_email_notification(self, notification):
        """Send email notification"""
        try:
            template_config = self.email_templates[notification['type']]
            
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config['username']
            msg['To'] = ', '.join(notification['recipients'])
            msg['Subject'] = notification['subject']
            
            body = self._render_email_template(template_config['template'], notification['data'])
            msg.attach(MIMEText(body, 'html'))
            
            server = smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port'])
            server.starttls()
            server.login(self.smtp_config['username'], self.smtp_config['password'])
            
            text = msg.as_string()
            server.sendmail(self.smtp_config['username'], notification['recipients'], text)
            server.quit()
            
            logger.info(f"Email sent successfully: {notification['subject']}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
            return False
    
    def _render_email_template(self, template_name, data):
        """Render email template with data"""
        try:
            template_path = os.path.join('templates', template_name)
            
            if not os.path.exists(template_path):
                return self._get_default_template(data)
            
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            return template_content.format(**data)
            
        except Exception as e:
            logger.error(f"Error rendering email template: {str(e)}")
            return self._get_default_template(data)
    
    def _get_default_template(self, data):
        """Get default email template"""
        return f"""
        <html>
        <body>
            <h2>Notification</h2>
            <p>This is an automated notification from the IT Onboarding System.</p>
            <p>Details: {data}</p>
            <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </body>
        </html>
        """
    
    def check_onboarding_delays(self):
        """Check for delayed onboarding processes"""
        try:
            delayed_threshold = datetime.now() - timedelta(days=3)
            
            delayed_employees = Employee.query.filter(
                Employee.created_at < delayed_threshold,
                Employee.ad_account_created == False
            ).all()
            
            for employee in delayed_employees:
                self.send_notification(
                    'onboarding_delayed',
                    [employee.manager_email, 'it-support@company.com'],
                    {
                        'employee_name': f"{employee.first_name} {employee.last_name}",
                        'employee_id': employee.employee_id,
                        'start_date': employee.start_date.isoformat(),
                        'days_delayed': (datetime.now().date() - employee.start_date).days
                    },
                    'high'
                )
            
            logger.info(f"Checked for delays: {len(delayed_employees)} delayed employees found")
            
        except Exception as e:
            logger.error(f"Error checking onboarding delays: {str(e)}")
    
    def send_weekly_report(self):
        """Send weekly onboarding report"""
        try:
            week_start = datetime.now() - timedelta(days=7)
            
            weekly_stats = {
                'employees_added': Employee.query.filter(Employee.created_at >= week_start).count(),
                'onboardings_completed': Employee.query.filter(
                    Employee.created_at >= week_start,
                    Employee.ad_account_created == True,
                    Employee.o365_mailbox_created == True,
                    Employee.security_groups_assigned == True
                ).count(),
                'pending_onboardings': Employee.query.filter(
                    Employee.ad_account_created == False
                ).count()
            }
            
            self.send_notification(
                'weekly_report',
                ['it-manager@company.com', 'hr-manager@company.com'],
                {
                    'week_date': week_start.strftime('%Y-%m-%d'),
                    'employees_added': weekly_stats['employees_added'],
                    'onboardings_completed': weekly_stats['onboardings_completed'],
                    'pending_onboardings': weekly_stats['pending_onboardings'],
                    'completion_rate': round((weekly_stats['onboardings_completed'] / weekly_stats['employees_added'] * 100) if weekly_stats['employees_added'] > 0 else 0, 2)
                }
            )
            
            logger.info("Weekly report sent")
            
        except Exception as e:
            logger.error(f"Error sending weekly report: {str(e)}")
    
    def start_scheduler(self):
        """Start notification scheduler"""
        if self.scheduler_running:
            return
        
        self.scheduler_running = True
        
        schedule.every(5).minutes.do(self.process_notification_queue)
        schedule.every().day.at("09:00").do(self.check_onboarding_delays)
        schedule.every().monday.at("08:00").do(self.send_weekly_report)
        
        def run_scheduler():
            while self.scheduler_running:
                schedule.run_pending()
                time.sleep(60)
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        logger.info("Notification scheduler started")
    
    def stop_scheduler(self):
        """Stop notification scheduler"""
        self.scheduler_running = False
        logger.info("Notification scheduler stopped")

notification_manager = NotificationManager()

@notifications_bp.route('/dashboard')
def notifications_dashboard():
    """Notifications dashboard page"""
    return render_template('notifications.html')

@notifications_bp.route('/api/queue')
def get_notification_queue():
    """Get notification queue status"""
    try:
        queue_stats = {
            'total': len(notification_manager.notification_queue),
            'pending': len([n for n in notification_manager.notification_queue if n['status'] == 'pending']),
            'sent': len([n for n in notification_manager.notification_queue if n['status'] == 'sent']),
            'failed': len([n for n in notification_manager.notification_queue if n['status'] == 'failed']),
            'recent_notifications': notification_manager.notification_queue[-10:]
        }
        
        return jsonify({
            'success': True,
            'queue_stats': queue_stats
        })
    except Exception as e:
        logger.error(f"Error getting notification queue: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/api/send', methods=['POST'])
def send_custom_notification():
    """Send custom notification"""
    try:
        data = request.get_json()
        
        notification_type = data.get('type')
        recipients = data.get('recipients', [])
        notification_data = data.get('data', {})
        priority = data.get('priority', 'normal')
        
        if not notification_type or not recipients:
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400
        
        success = notification_manager.send_notification(
            notification_type,
            recipients,
            notification_data,
            priority
        )
        
        return jsonify({
            'success': success,
            'message': 'Notification queued successfully' if success else 'Failed to queue notification'
        })
        
    except Exception as e:
        logger.error(f"Error sending custom notification: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/api/test')
def test_notification_system():
    """Test notification system"""
    try:
        test_data = {
            'employee_name': 'Test Employee',
            'employee_id': 'TEST001',
            'start_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        success = notification_manager.send_notification(
            'onboarding_started',
            ['test@company.com'],
            test_data
        )
        
        return jsonify({
            'success': success,
            'message': 'Test notification sent' if success else 'Failed to send test notification'
        })
        
    except Exception as e:
        logger.error(f"Error testing notification system: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
