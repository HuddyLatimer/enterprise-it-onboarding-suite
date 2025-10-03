import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime, timedelta
import secrets
import string

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///onboarding.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

db = SQLAlchemy(app)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    department = db.Column(db.String(50), nullable=False)
    manager_email = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    position = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    
    ad_account_created = db.Column(db.Boolean, default=False)
    o365_mailbox_created = db.Column(db.Boolean, default=False)
    security_groups_assigned = db.Column(db.Boolean, default=False)
    equipment_assigned = db.Column(db.Boolean, default=False)
    software_deployed = db.Column(db.Boolean, default=False)
    welcome_email_sent = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'department': self.department,
            'manager_email': self.manager_email,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'position': self.position,
            'location': self.location,
            'phone': self.phone,
            'ad_account_created': self.ad_account_created,
            'o365_mailbox_created': self.o365_mailbox_created,
            'security_groups_assigned': self.security_groups_assigned,
            'equipment_assigned': self.equipment_assigned,
            'software_deployed': self.software_deployed,
            'welcome_email_sent': self.welcome_email_sent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), db.ForeignKey('employee.employee_id'), nullable=False)
    equipment_type = db.Column(db.String(50), nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    serial_number = db.Column(db.String(100), unique=True, nullable=False)
    asset_tag = db.Column(db.String(50), nullable=True)
    assigned_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Active')
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'equipment_type': self.equipment_type,
            'brand': self.brand,
            'model': self.model,
            'serial_number': self.serial_number,
            'asset_tag': self.asset_tag,
            'assigned_date': self.assigned_date.isoformat() if self.assigned_date else None,
            'status': self.status
        }

class OnboardingLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), db.ForeignKey('employee.employee_id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'action': self.action,
            'status': self.status,
            'details': self.details,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

def generate_temp_password(length=12):
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(characters) for _ in range(length))
    return password

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/employees', methods=['GET'])
def get_employees():
    employees = Employee.query.all()
    return jsonify([emp.to_dict() for emp in employees])

@app.route('/api/employees', methods=['POST'])
def create_employee():
    data = request.get_json()
    
    try:
        employee = Employee(
            employee_id=data['employee_id'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            department=data['department'],
            manager_email=data['manager_email'],
            start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
            position=data['position'],
            location=data['location'],
            phone=data.get('phone', '')
        )
        
        db.session.add(employee)
        db.session.commit()
        
        log_entry = OnboardingLog(
            employee_id=employee.employee_id,
            action='Employee Created',
            status='Success',
            details=f'Employee {employee.first_name} {employee.last_name} added to system'
        )
        db.session.add(log_entry)
        db.session.commit()
        
        return jsonify(employee.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating employee: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/api/employees/<employee_id>', methods=['GET'])
def get_employee(employee_id):
    employee = Employee.query.filter_by(employee_id=employee_id).first()
    if not employee:
        return jsonify({'error': 'Employee not found'}), 404
    return jsonify(employee.to_dict())

@app.route('/api/employees/<employee_id>/equipment', methods=['GET'])
def get_employee_equipment(employee_id):
    equipment = Equipment.query.filter_by(employee_id=employee_id).all()
    return jsonify([eq.to_dict() for eq in equipment])

@app.route('/api/employees/<employee_id>/equipment', methods=['POST'])
def assign_equipment(employee_id):
    data = request.get_json()
    
    try:
        equipment = Equipment(
            employee_id=employee_id,
            equipment_type=data['equipment_type'],
            brand=data['brand'],
            model=data['model'],
            serial_number=data['serial_number'],
            asset_tag=data.get('asset_tag', '')
        )
        
        db.session.add(equipment)
        
        employee = Employee.query.filter_by(employee_id=employee_id).first()
        if employee:
            employee.equipment_assigned = True
            employee.updated_at = datetime.utcnow()
        
        log_entry = OnboardingLog(
            employee_id=employee_id,
            action='Equipment Assigned',
            status='Success',
            details=f'{equipment.equipment_type} - {equipment.brand} {equipment.model} (SN: {equipment.serial_number})'
        )
        db.session.add(log_entry)
        db.session.commit()
        
        return jsonify(equipment.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error assigning equipment: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/api/employees/<employee_id>/logs', methods=['GET'])
def get_employee_logs(employee_id):
    logs = OnboardingLog.query.filter_by(employee_id=employee_id).order_by(OnboardingLog.timestamp.desc()).all()
    return jsonify([log.to_dict() for log in logs])

@app.route('/api/onboard/<employee_id>', methods=['POST'])
def start_onboarding(employee_id):
    employee = Employee.query.filter_by(employee_id=employee_id).first()
    if not employee:
        return jsonify({'error': 'Employee not found'}), 404
    
    try:
        temp_password = generate_temp_password()
        
        # Simulate onboarding process
        employee.ad_account_created = True
        employee.o365_mailbox_created = True
        employee.security_groups_assigned = True
        employee.welcome_email_sent = True
        employee.updated_at = datetime.utcnow()
        
        log_entry = OnboardingLog(
            employee_id=employee.employee_id,
            action='Onboarding Process Started',
            status='Success',
            details=f'Automated onboarding initiated for {employee.first_name} {employee.last_name}'
        )
        db.session.add(log_entry)
        db.session.commit()
        
        return jsonify({
            'message': 'Onboarding process completed successfully',
            'temp_password': temp_password,
            'employee': employee.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error during onboarding: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/csv', methods=['GET'])
def export_csv():
    employees = Employee.query.all()
    
    csv_data = "Employee ID,Name,Email,Department,Start Date,AD Account,O365 Mailbox,Equipment,Software,Welcome Email\n"
    
    for emp in employees:
        csv_data += f"{emp.employee_id},{emp.first_name} {emp.last_name},{emp.email},{emp.department},{emp.start_date},{emp.ad_account_created},{emp.o365_mailbox_created},{emp.equipment_assigned},{emp.software_deployed},{emp.welcome_email_sent}\n"
    
    return csv_data, 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': 'attachment; filename=onboarding_report.csv'
    }

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
