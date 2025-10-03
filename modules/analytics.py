import os
import json
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request
from sqlalchemy import func, and_, or_

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')
logger = logging.getLogger(__name__)

class AnalyticsEngine:
    def __init__(self):
        self.metrics_cache = {}
        self.cache_duration = 300  # 5 minutes
    
    def get_onboarding_metrics(self, db, Employee):
        """Get comprehensive onboarding metrics"""
        try:
            total_employees = Employee.query.count()
            
            completed_onboardings = Employee.query.filter(
                and_(
                    Employee.ad_account_created == True,
                    Employee.o365_mailbox_created == True,
                    Employee.security_groups_assigned == True,
                    Employee.equipment_assigned == True,
                    Employee.software_deployed == True,
                    Employee.welcome_email_sent == True
                )
            ).count()
            
            pending_onboardings = total_employees - completed_onboardings
            
            success_rate = (completed_onboardings / total_employees * 100) if total_employees > 0 else 0
            
            return {
                'total_employees': total_employees,
                'completed_onboardings': completed_onboardings,
                'pending_onboardings': pending_onboardings,
                'success_rate': round(success_rate, 2)
            }
        except Exception as e:
            logger.error(f"Error getting onboarding metrics: {str(e)}")
            return {}
    
    def get_department_breakdown(self):
        """Get department-wise statistics"""
        try:
            dept_stats = db.session.query(
                Employee.department,
                func.count(Employee.id).label('total'),
                func.sum(Employee.ad_account_created.cast(db.Integer)).label('ad_completed'),
                func.sum(Employee.o365_mailbox_created.cast(db.Integer)).label('o365_completed'),
                func.sum(Employee.equipment_assigned.cast(db.Integer)).label('equipment_completed')
            ).group_by(Employee.department).all()
            
            breakdown = []
            for dept in dept_stats:
                breakdown.append({
                    'department': dept.department,
                    'total': dept.total,
                    'ad_completion_rate': round((dept.ad_completed / dept.total * 100) if dept.total > 0 else 0, 2),
                    'o365_completion_rate': round((dept.o365_completed / dept.total * 100) if dept.total > 0 else 0, 2),
                    'equipment_completion_rate': round((dept.equipment_completed / dept.total * 100) if dept.total > 0 else 0, 2)
                })
            
            return breakdown
        except Exception as e:
            logger.error(f"Error getting department breakdown: {str(e)}")
            return []
    
    def get_time_series_data(self, days=30):
        """Get time series data for trends"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            daily_stats = db.session.query(
                func.date(Employee.created_at).label('date'),
                func.count(Employee.id).label('employees_added'),
                func.sum(Employee.ad_account_created.cast(db.Integer)).label('ad_completed'),
                func.sum(Employee.o365_mailbox_created.cast(db.Integer)).label('o365_completed')
            ).filter(
                Employee.created_at >= start_date
            ).group_by(
                func.date(Employee.created_at)
            ).order_by('date').all()
            
            time_series = []
            for stat in daily_stats:
                time_series.append({
                    'date': stat.date.isoformat(),
                    'employees_added': stat.employees_added,
                    'ad_completed': stat.ad_completed,
                    'o365_completed': stat.o365_completed
                })
            
            return time_series
        except Exception as e:
            logger.error(f"Error getting time series data: {str(e)}")
            return []
    
    def get_equipment_statistics(self):
        """Get equipment statistics"""
        try:
            total_equipment = Equipment.query.count()
            assigned_equipment = Equipment.query.filter(Equipment.status == 'Assigned').count()
            available_equipment = Equipment.query.filter(Equipment.status == 'Available').count()
            
            equipment_by_type = db.session.query(
                Equipment.equipment_type,
                func.count(Equipment.id).label('count')
            ).group_by(Equipment.equipment_type).all()
            
            equipment_breakdown = [{'type': eq.equipment_type, 'count': eq.count} for eq in equipment_by_type]
            
            return {
                'total_equipment': total_equipment,
                'assigned_equipment': assigned_equipment,
                'available_equipment': available_equipment,
                'utilization_rate': round((assigned_equipment / total_equipment * 100) if total_equipment > 0 else 0, 2),
                'equipment_breakdown': equipment_breakdown
            }
        except Exception as e:
            logger.error(f"Error getting equipment statistics: {str(e)}")
            return {}
    
    def get_performance_metrics(self):
        """Get system performance metrics"""
        try:
            avg_completion_time = db.session.query(
                func.avg(
                    func.julianday(Employee.updated_at) - func.julianday(Employee.created_at)
                )
            ).filter(
                Employee.ad_account_created == True,
                Employee.o365_mailbox_created == True,
                Employee.security_groups_assigned == True
            ).scalar()
            
            avg_completion_days = round(avg_completion_time, 2) if avg_completion_time else 0
            
            error_logs = OnboardingLog.query.filter(
                OnboardingLog.status == 'Error'
            ).count()
            
            total_logs = OnboardingLog.query.count()
            error_rate = round((error_logs / total_logs * 100) if total_logs > 0 else 0, 2)
            
            return {
                'avg_completion_days': avg_completion_days,
                'error_rate': error_rate,
                'total_logs': total_logs,
                'error_logs': error_logs
            }
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return {}

analytics_engine = AnalyticsEngine()

@analytics_bp.route('/dashboard')
def analytics_dashboard():
    """Analytics dashboard page"""
    return render_template('analytics.html')

@analytics_bp.route('/api/metrics')
def get_metrics():
    """Get all analytics metrics"""
    try:
        metrics = {
            'onboarding': analytics_engine.get_onboarding_metrics(),
            'departments': analytics_engine.get_department_breakdown(),
            'equipment': analytics_engine.get_equipment_statistics(),
            'performance': analytics_engine.get_performance_metrics(),
            'time_series': analytics_engine.get_time_series_data()
        }
        
        return jsonify({
            'success': True,
            'metrics': metrics,
            'generated_at': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analytics_bp.route('/api/trends')
def get_trends():
    """Get trend analysis"""
    try:
        days = request.args.get('days', 30, type=int)
        trends = analytics_engine.get_time_series_data(days)
        
        return jsonify({
            'success': True,
            'trends': trends
        })
    except Exception as e:
        logger.error(f"Error getting trends: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analytics_bp.route('/api/export/analytics')
def export_analytics():
    """Export analytics data as CSV"""
    try:
        metrics = analytics_engine.get_onboarding_metrics()
        dept_breakdown = analytics_engine.get_department_breakdown()
        equipment_stats = analytics_engine.get_equipment_statistics()
        
        csv_data = "Metric,Value\n"
        csv_data += f"Total Employees,{metrics.get('total_employees', 0)}\n"
        csv_data += f"Completed Onboardings,{metrics.get('completed_onboardings', 0)}\n"
        csv_data += f"Success Rate,{metrics.get('success_rate', 0)}%\n"
        csv_data += f"Equipment Utilization,{equipment_stats.get('utilization_rate', 0)}%\n\n"
        
        csv_data += "Department,Total,AD Completion Rate,O365 Completion Rate,Equipment Completion Rate\n"
        for dept in dept_breakdown:
            csv_data += f"{dept['department']},{dept['total']},{dept['ad_completion_rate']}%,{dept['o365_completion_rate']}%,{dept['equipment_completion_rate']}%\n"
        
        return csv_data, 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename=analytics_report.csv'
        }
    except Exception as e:
        logger.error(f"Error exporting analytics: {str(e)}")
        return jsonify({'error': str(e)}), 500
