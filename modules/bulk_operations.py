import os
import csv
import json
import logging
import pandas as pd
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
from app import db, Employee, Equipment, OnboardingLog
import io
import zipfile

bulk_operations_bp = Blueprint('bulk_operations', __name__, url_prefix='/bulk')
logger = logging.getLogger(__name__)

class BulkOperationsManager:
    def __init__(self):
        self.allowed_extensions = {'csv', 'xlsx', 'json'}
        self.upload_folder = os.path.join(os.path.dirname(__file__), '..', 'uploads')
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def allowed_file(self, filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def import_employees_csv(self, file_path):
        """Import employees from CSV file"""
        try:
            employees_data = []
            errors = []
            
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        employee_data = {
                            'employee_id': row.get('employee_id', '').strip(),
                            'first_name': row.get('first_name', '').strip(),
                            'last_name': row.get('last_name', '').strip(),
                            'email': row.get('email', '').strip(),
                            'department': row.get('department', '').strip(),
                            'manager_email': row.get('manager_email', '').strip(),
                            'start_date': row.get('start_date', '').strip(),
                            'position': row.get('position', '').strip(),
                            'location': row.get('location', '').strip(),
                            'phone': row.get('phone', '').strip()
                        }
                        
                        if not all([employee_data['employee_id'], employee_data['first_name'], 
                                  employee_data['last_name'], employee_data['email']]):
                            errors.append(f"Row {row_num}: Missing required fields")
                            continue
                        
                        employees_data.append(employee_data)
                        
                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")
            
            return employees_data, errors
            
        except Exception as e:
            logger.error(f"Error importing CSV: {str(e)}")
            return [], [str(e)]
    
    def import_employees_excel(self, file_path):
        """Import employees from Excel file"""
        try:
            df = pd.read_excel(file_path)
            employees_data = []
            errors = []
            
            for index, row in df.iterrows():
                try:
                    employee_data = {
                        'employee_id': str(row.get('employee_id', '')).strip(),
                        'first_name': str(row.get('first_name', '')).strip(),
                        'last_name': str(row.get('last_name', '')).strip(),
                        'email': str(row.get('email', '')).strip(),
                        'department': str(row.get('department', '')).strip(),
                        'manager_email': str(row.get('manager_email', '')).strip(),
                        'start_date': str(row.get('start_date', '')).strip(),
                        'position': str(row.get('position', '')).strip(),
                        'location': str(row.get('location', '')).strip(),
                        'phone': str(row.get('phone', '')).strip()
                    }
                    
                    if not all([employee_data['employee_id'], employee_data['first_name'], 
                              employee_data['last_name'], employee_data['email']]):
                        errors.append(f"Row {index + 2}: Missing required fields")
                        continue
                    
                    employees_data.append(employee_data)
                    
                except Exception as e:
                    errors.append(f"Row {index + 2}: {str(e)}")
            
            return employees_data, errors
            
        except Exception as e:
            logger.error(f"Error importing Excel: {str(e)}")
            return [], [str(e)]
    
    def import_equipment_csv(self, file_path):
        """Import equipment from CSV file"""
        try:
            equipment_data = []
            errors = []
            
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        equipment_item = {
                            'asset_tag': row.get('asset_tag', '').strip(),
                            'equipment_type': row.get('equipment_type', '').strip(),
                            'brand': row.get('brand', '').strip(),
                            'model': row.get('model', '').strip(),
                            'serial_number': row.get('serial_number', '').strip(),
                            'mac_address': row.get('mac_address', '').strip(),
                            'purchase_date': row.get('purchase_date', '').strip(),
                            'warranty_expiry': row.get('warranty_expiry', '').strip(),
                            'cost': row.get('cost', '0').strip(),
                            'supplier': row.get('supplier', '').strip(),
                            'status': row.get('status', 'Available').strip(),
                            'location': row.get('location', '').strip(),
                            'notes': row.get('notes', '').strip()
                        }
                        
                        if not all([equipment_item['asset_tag'], equipment_item['equipment_type'], 
                                  equipment_item['brand'], equipment_item['serial_number']]):
                            errors.append(f"Row {row_num}: Missing required fields")
                            continue
                        
                        equipment_data.append(equipment_item)
                        
                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")
            
            return equipment_data, errors
            
        except Exception as e:
            logger.error(f"Error importing equipment CSV: {str(e)}")
            return [], [str(e)]
    
    def export_employees_csv(self, filters=None):
        """Export employees to CSV"""
        try:
            query = Employee.query
            
            if filters:
                if filters.get('department'):
                    query = query.filter(Employee.department == filters['department'])
                if filters.get('status') == 'completed':
                    query = query.filter(
                        Employee.ad_account_created == True,
                        Employee.o365_mailbox_created == True,
                        Employee.security_groups_assigned == True
                    )
                elif filters.get('status') == 'pending':
                    query = query.filter(Employee.ad_account_created == False)
            
            employees = query.all()
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            writer.writerow([
                'Employee ID', 'First Name', 'Last Name', 'Email', 'Department',
                'Manager Email', 'Start Date', 'Position', 'Location', 'Phone',
                'AD Account Created', 'O365 Mailbox Created', 'Security Groups Assigned',
                'Equipment Assigned', 'Software Deployed', 'Welcome Email Sent',
                'Created At', 'Updated At'
            ])
            
            for emp in employees:
                writer.writerow([
                    emp.employee_id, emp.first_name, emp.last_name, emp.email,
                    emp.department, emp.manager_email, emp.start_date, emp.position,
                    emp.location, emp.phone, emp.ad_account_created, emp.o365_mailbox_created,
                    emp.security_groups_assigned, emp.equipment_assigned, emp.software_deployed,
                    emp.welcome_email_sent, emp.created_at, emp.updated_at
                ])
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error exporting employees: {str(e)}")
            return None
    
    def export_equipment_csv(self, filters=None):
        """Export equipment to CSV"""
        try:
            query = Equipment.query
            
            if filters:
                if filters.get('status'):
                    query = query.filter(Equipment.status == filters['status'])
                if filters.get('equipment_type'):
                    query = query.filter(Equipment.equipment_type == filters['equipment_type'])
            
            equipment = query.all()
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            writer.writerow([
                'Asset Tag', 'Equipment Type', 'Brand', 'Model', 'Serial Number',
                'MAC Address', 'Purchase Date', 'Warranty Expiry', 'Cost', 'Supplier',
                'Status', 'Assigned Employee ID', 'Assigned Date', 'Location', 'Notes'
            ])
            
            for eq in equipment:
                writer.writerow([
                    eq.asset_tag, eq.equipment_type, eq.brand, eq.model,
                    eq.serial_number, eq.mac_address, eq.purchase_date,
                    eq.warranty_expiry, eq.cost, eq.supplier, eq.status,
                    eq.assigned_employee_id, eq.assigned_date, eq.location, eq.notes
                ])
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error exporting equipment: {str(e)}")
            return None
    
    def export_comprehensive_report(self):
        """Export comprehensive report with all data"""
        try:
            employees = Employee.query.all()
            equipment = Equipment.query.all()
            logs = OnboardingLog.query.order_by(OnboardingLog.timestamp.desc()).limit(1000).all()
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            writer.writerow(['COMPREHENSIVE ONBOARDING REPORT'])
            writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow([])
            
            writer.writerow(['EMPLOYEES'])
            writer.writerow([
                'Employee ID', 'Name', 'Email', 'Department', 'Start Date',
                'AD Account', 'O365 Mailbox', 'Security Groups', 'Equipment', 'Software', 'Welcome Email'
            ])
            
            for emp in employees:
                writer.writerow([
                    emp.employee_id, f"{emp.first_name} {emp.last_name}", emp.email,
                    emp.department, emp.start_date, emp.ad_account_created,
                    emp.o365_mailbox_created, emp.security_groups_assigned,
                    emp.equipment_assigned, emp.software_deployed, emp.welcome_email_sent
                ])
            
            writer.writerow([])
            writer.writerow(['EQUIPMENT'])
            writer.writerow([
                'Asset Tag', 'Type', 'Brand', 'Model', 'Serial Number',
                'Status', 'Assigned Employee', 'Assigned Date'
            ])
            
            for eq in equipment:
                writer.writerow([
                    eq.asset_tag, eq.equipment_type, eq.brand, eq.model,
                    eq.serial_number, eq.status, eq.assigned_employee_id, eq.assigned_date
                ])
            
            writer.writerow([])
            writer.writerow(['RECENT ACTIVITY LOGS'])
            writer.writerow(['Timestamp', 'Employee ID', 'Action', 'Status', 'Details'])
            
            for log in logs:
                writer.writerow([
                    log.timestamp, log.employee_id, log.action, log.status, log.details
                ])
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error exporting comprehensive report: {str(e)}")
            return None
    
    def create_import_template(self, data_type):
        """Create import template file"""
        try:
            if data_type == 'employees':
                template_data = [
                    ['employee_id', 'first_name', 'last_name', 'email', 'department', 'manager_email', 'start_date', 'position', 'location', 'phone'],
                    ['EMP001', 'John', 'Doe', 'john.doe@company.com', 'IT', 'manager.it@company.com', '2024-01-15', 'Software Engineer', 'New York', '555-1234'],
                    ['EMP002', 'Jane', 'Smith', 'jane.smith@company.com', 'HR', 'manager.hr@company.com', '2024-01-16', 'HR Specialist', 'Los Angeles', '555-5678']
                ]
            elif data_type == 'equipment':
                template_data = [
                    ['asset_tag', 'equipment_type', 'brand', 'model', 'serial_number', 'mac_address', 'purchase_date', 'warranty_expiry', 'cost', 'supplier', 'status', 'location', 'notes'],
                    ['LT001', 'Laptop', 'Dell', 'Latitude 5520', 'ABC123456', '00:11:22:33:44:55', '2024-01-01', '2027-01-01', '1200.00', 'Dell Inc', 'Available', 'IT Storage', 'New laptop'],
                    ['MN001', 'Monitor', 'Dell', '24" Monitor', 'DEF789012', '', '2024-01-01', '2027-01-01', '300.00', 'Dell Inc', 'Available', 'IT Storage', '24 inch monitor']
                ]
            else:
                return None
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            for row in template_data:
                writer.writerow(row)
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error creating template: {str(e)}")
            return None

bulk_manager = BulkOperationsManager()

@bulk_operations_bp.route('/dashboard')
def bulk_dashboard():
    """Bulk operations dashboard"""
    return render_template('bulk_operations.html')

@bulk_operations_bp.route('/api/import', methods=['POST'])
def import_data():
    """Import data from file"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        data_type = request.form.get('data_type', 'employees')
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not bulk_manager.allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file type'}), 400
        
        filename = secure_filename(file.filename)
        file_path = os.path.join(bulk_manager.upload_folder, filename)
        file.save(file_path)
        
        if data_type == 'employees':
            if filename.endswith('.csv'):
                data, errors = bulk_manager.import_employees_csv(file_path)
            elif filename.endswith('.xlsx'):
                data, errors = bulk_manager.import_employees_excel(file_path)
            else:
                return jsonify({'success': False, 'error': 'Unsupported file format'}), 400
            
            if errors:
                return jsonify({
                    'success': False,
                    'error': 'Import errors found',
                    'errors': errors
                }), 400
            
            imported_count = 0
            for emp_data in data:
                try:
                    employee = Employee(**emp_data)
                    db.session.add(employee)
                    imported_count += 1
                except Exception as e:
                    logger.error(f"Error importing employee {emp_data.get('employee_id')}: {str(e)}")
            
            db.session.commit()
            
        elif data_type == 'equipment':
            data, errors = bulk_manager.import_equipment_csv(file_path)
            
            if errors:
                return jsonify({
                    'success': False,
                    'error': 'Import errors found',
                    'errors': errors
                }), 400
            
            imported_count = 0
            for eq_data in data:
                try:
                    equipment = Equipment(**eq_data)
                    db.session.add(equipment)
                    imported_count += 1
                except Exception as e:
                    logger.error(f"Error importing equipment {eq_data.get('asset_tag')}: {str(e)}")
            
            db.session.commit()
        
        os.remove(file_path)
        
        return jsonify({
            'success': True,
            'message': f'Successfully imported {imported_count} {data_type}',
            'imported_count': imported_count
        })
        
    except Exception as e:
        logger.error(f"Error importing data: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bulk_operations_bp.route('/api/export/<data_type>')
def export_data(data_type):
    """Export data to CSV"""
    try:
        filters = request.args.to_dict()
        
        if data_type == 'employees':
            csv_data = bulk_manager.export_employees_csv(filters)
        elif data_type == 'equipment':
            csv_data = bulk_manager.export_equipment_csv(filters)
        elif data_type == 'comprehensive':
            csv_data = bulk_manager.export_comprehensive_report()
        else:
            return jsonify({'success': False, 'error': 'Invalid data type'}), 400
        
        if csv_data is None:
            return jsonify({'success': False, 'error': 'Export failed'}), 500
        
        filename = f"{data_type}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return csv_data, 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': f'attachment; filename={filename}'
        }
        
    except Exception as e:
        logger.error(f"Error exporting data: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bulk_operations_bp.route('/api/template/<data_type>')
def download_template(data_type):
    """Download import template"""
    try:
        template_data = bulk_manager.create_import_template(data_type)
        
        if template_data is None:
            return jsonify({'success': False, 'error': 'Invalid data type'}), 400
        
        filename = f"{data_type}_import_template.csv"
        
        return template_data, 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': f'attachment; filename={filename}'
        }
        
    except Exception as e:
        logger.error(f"Error creating template: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
