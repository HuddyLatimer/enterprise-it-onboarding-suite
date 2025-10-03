import os
import sqlite3
import json
from datetime import datetime, timedelta
import random

def create_example_data():
    """Create example data for demonstration"""
    
    departments = ['IT', 'HR', 'Finance', 'Sales', 'Marketing']
    positions = {
        'IT': ['Software Engineer', 'System Administrator', 'DevOps Engineer', 'IT Support Specialist'],
        'HR': ['HR Manager', 'HR Specialist', 'Recruiter', 'Benefits Coordinator'],
        'Finance': ['Financial Analyst', 'Accountant', 'Finance Manager', 'Budget Analyst'],
        'Sales': ['Sales Manager', 'Sales Representative', 'Account Executive', 'Sales Director'],
        'Marketing': ['Marketing Manager', 'Marketing Specialist', 'Content Creator', 'Digital Marketing Analyst']
    }
    locations = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego']
    
    example_employees = []
    
    for i in range(20):
        dept = random.choice(departments)
        position = random.choice(positions[dept])
        location = random.choice(locations)
        
        employee = {
            'employee_id': f'EMP{1000 + i:03d}',
            'first_name': random.choice(['John', 'Jane', 'Michael', 'Sarah', 'David', 'Lisa', 'Robert', 'Jennifer', 'William', 'Ashley']),
            'last_name': random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']),
            'email': f'emp{1000 + i:03d}@company.com',
            'department': dept,
            'manager_email': f'manager.{dept.lower()}@company.com',
            'start_date': (datetime.now() + timedelta(days=random.randint(-30, 30))).strftime('%Y-%m-%d'),
            'position': position,
            'location': location,
            'phone': f'555-{random.randint(100, 999)}-{random.randint(1000, 9999)}',
            'ad_account_created': random.choice([True, False]),
            'o365_mailbox_created': random.choice([True, False]),
            'security_groups_assigned': random.choice([True, False]),
            'equipment_assigned': random.choice([True, False]),
            'software_deployed': random.choice([True, False]),
            'welcome_email_sent': random.choice([True, False])
        }
        example_employees.append(employee)
    
    return example_employees

def create_example_equipment():
    """Create example equipment data"""
    
    equipment_types = ['Laptop', 'Desktop', 'Monitor', 'Keyboard', 'Mouse', 'Headset', 'Docking Station']
    brands = ['Dell', 'HP', 'Lenovo', 'Apple', 'Microsoft', 'Logitech', 'Cisco']
    
    example_equipment = []
    
    for i in range(50):
        equipment = {
            'employee_id': f'EMP{1000 + (i % 20):03d}',
            'equipment_type': random.choice(equipment_types),
            'brand': random.choice(brands),
            'model': f'Model-{random.randint(100, 999)}',
            'serial_number': f'SN{random.randint(100000, 999999)}',
            'asset_tag': f'AT{random.randint(1000, 9999)}',
            'assigned_date': (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
            'status': random.choice(['Active', 'Active', 'Active', 'Maintenance'])
        }
        example_equipment.append(equipment)
    
    return example_equipment

def create_example_logs():
    """Create example activity logs"""
    
    actions = [
        'Employee Created',
        'AD Account Created',
        'O365 Mailbox Created',
        'Security Groups Assigned',
        'Equipment Assigned',
        'Software Deployed',
        'Welcome Email Sent',
        'Password Reset',
        'Account Disabled',
        'Equipment Returned'
    ]
    
    statuses = ['Success', 'Error', 'Warning']
    
    example_logs = []
    
    for i in range(100):
        log = {
            'employee_id': f'EMP{1000 + (i % 20):03d}',
            'action': random.choice(actions),
            'status': random.choice(statuses),
            'details': f'Action completed for employee {1000 + (i % 20):03d}',
            'timestamp': (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d %H:%M:%S')
        }
        example_logs.append(log)
    
    return example_logs

def populate_database():
    """Populate the database with example data"""
    
    db_path = 'onboarding.db'
    
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE employee (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            manager_email TEXT NOT NULL,
            start_date DATE NOT NULL,
            position TEXT NOT NULL,
            location TEXT NOT NULL,
            phone TEXT,
            ad_account_created BOOLEAN DEFAULT 0,
            o365_mailbox_created BOOLEAN DEFAULT 0,
            security_groups_assigned BOOLEAN DEFAULT 0,
            equipment_assigned BOOLEAN DEFAULT 0,
            software_deployed BOOLEAN DEFAULT 0,
            welcome_email_sent BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE equipment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            equipment_type TEXT NOT NULL,
            brand TEXT NOT NULL,
            model TEXT NOT NULL,
            serial_number TEXT UNIQUE NOT NULL,
            asset_tag TEXT,
            assigned_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'Active',
            FOREIGN KEY (employee_id) REFERENCES employee (employee_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE onboarding_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            action TEXT NOT NULL,
            status TEXT NOT NULL,
            details TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employee (employee_id)
        )
    ''')
    
    employees = create_example_data()
    equipment = create_example_equipment()
    logs = create_example_logs()
    
    for emp in employees:
        cursor.execute('''
            INSERT INTO employee (employee_id, first_name, last_name, email, department, 
                                manager_email, start_date, position, location, phone,
                                ad_account_created, o365_mailbox_created, security_groups_assigned,
                                equipment_assigned, software_deployed, welcome_email_sent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            emp['employee_id'], emp['first_name'], emp['last_name'], emp['email'],
            emp['department'], emp['manager_email'], emp['start_date'], emp['position'],
            emp['location'], emp['phone'], emp['ad_account_created'], emp['o365_mailbox_created'],
            emp['security_groups_assigned'], emp['equipment_assigned'], emp['software_deployed'],
            emp['welcome_email_sent']
        ))
    
    for eq in equipment:
        cursor.execute('''
            INSERT INTO equipment (employee_id, equipment_type, brand, model, serial_number, asset_tag, assigned_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            eq['employee_id'], eq['equipment_type'], eq['brand'], eq['model'],
            eq['serial_number'], eq['asset_tag'], eq['assigned_date'], eq['status']
        ))
    
    for log in logs:
        cursor.execute('''
            INSERT INTO onboarding_log (employee_id, action, status, details, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            log['employee_id'], log['action'], log['status'], log['details'], log['timestamp']
        ))
    
    conn.commit()
    conn.close()
    
    print("Database populated with example data successfully!")

if __name__ == '__main__':
    populate_database()
