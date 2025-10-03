import os
import sqlite3
import logging
import qrcode
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class EquipmentTracker:
    def __init__(self, db_path=None):
        self.db_path = db_path or os.getenv('EQUIPMENT_DB_PATH', './data/equipment.db')
        self.init_database()
    
    def init_database(self):
        """Initialize equipment tracking database"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS equipment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_tag TEXT UNIQUE NOT NULL,
                    equipment_type TEXT NOT NULL,
                    brand TEXT NOT NULL,
                    model TEXT NOT NULL,
                    serial_number TEXT UNIQUE NOT NULL,
                    mac_address TEXT,
                    purchase_date DATE,
                    warranty_expiry DATE,
                    cost DECIMAL(10,2),
                    supplier TEXT,
                    status TEXT DEFAULT 'Available',
                    assigned_employee_id TEXT,
                    assigned_date DATETIME,
                    location TEXT,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS equipment_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_tag TEXT NOT NULL,
                    action TEXT NOT NULL,
                    employee_id TEXT,
                    details TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (asset_tag) REFERENCES equipment (asset_tag)
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("Equipment database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing equipment database: {str(e)}")
            raise
    
    def add_equipment(self, equipment_data):
        """Add new equipment to inventory"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO equipment (asset_tag, equipment_type, brand, model, serial_number,
                                    mac_address, purchase_date, warranty_expiry, cost, supplier,
                                    status, location, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                equipment_data['asset_tag'],
                equipment_data['equipment_type'],
                equipment_data['brand'],
                equipment_data['model'],
                equipment_data['serial_number'],
                equipment_data.get('mac_address', ''),
                equipment_data.get('purchase_date', ''),
                equipment_data.get('warranty_expiry', ''),
                equipment_data.get('cost', 0),
                equipment_data.get('supplier', ''),
                equipment_data.get('status', 'Available'),
                equipment_data.get('location', ''),
                equipment_data.get('notes', '')
            ))
            
            equipment_id = cursor.lastrowid
            
            self.log_equipment_action(
                equipment_data['asset_tag'],
                'Equipment Added',
                None,
                f"Added {equipment_data['equipment_type']} - {equipment_data['brand']} {equipment_data['model']}"
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"Successfully added equipment: {equipment_data['asset_tag']}")
            return {
                'success': True,
                'message': 'Equipment added successfully',
                'equipment_id': equipment_id
            }
            
        except sqlite3.IntegrityError as e:
            logger.error(f"Duplicate equipment entry: {str(e)}")
            return {
                'success': False,
                'message': 'Equipment with this asset tag or serial number already exists',
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Error adding equipment: {str(e)}")
            return {
                'success': False,
                'message': 'Error adding equipment',
                'error': str(e)
            }
    
    def assign_equipment(self, asset_tag, employee_id, assignment_notes=''):
        """Assign equipment to employee"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE equipment 
                SET status = 'Assigned', 
                    assigned_employee_id = ?, 
                    assigned_date = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE asset_tag = ? AND status = 'Available'
            ''', (employee_id, asset_tag))
            
            if cursor.rowcount == 0:
                conn.close()
                return {
                    'success': False,
                    'message': 'Equipment not found or already assigned'
                }
            
            self.log_equipment_action(
                asset_tag,
                'Equipment Assigned',
                employee_id,
                f"Assigned to employee {employee_id}. Notes: {assignment_notes}"
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"Successfully assigned equipment {asset_tag} to {employee_id}")
            return {
                'success': True,
                'message': 'Equipment assigned successfully'
            }
            
        except Exception as e:
            logger.error(f"Error assigning equipment: {str(e)}")
            return {
                'success': False,
                'message': 'Error assigning equipment',
                'error': str(e)
            }
    
    def return_equipment(self, asset_tag, return_notes=''):
        """Return equipment from employee"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT assigned_employee_id FROM equipment WHERE asset_tag = ?
            ''', (asset_tag,))
            
            result = cursor.fetchone()
            if not result:
                conn.close()
                return {
                    'success': False,
                    'message': 'Equipment not found'
                }
            
            employee_id = result[0]
            
            cursor.execute('''
                UPDATE equipment 
                SET status = 'Available', 
                    assigned_employee_id = NULL, 
                    assigned_date = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE asset_tag = ?
            ''', (asset_tag,))
            
            self.log_equipment_action(
                asset_tag,
                'Equipment Returned',
                employee_id,
                f"Returned from employee {employee_id}. Notes: {return_notes}"
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"Successfully returned equipment {asset_tag}")
            return {
                'success': True,
                'message': 'Equipment returned successfully'
            }
            
        except Exception as e:
            logger.error(f"Error returning equipment: {str(e)}")
            return {
                'success': False,
                'message': 'Error returning equipment',
                'error': str(e)
            }
    
    def get_employee_equipment(self, employee_id):
        """Get all equipment assigned to employee"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM equipment WHERE assigned_employee_id = ?
                ORDER BY assigned_date DESC
            ''', (employee_id,))
            
            columns = [description[0] for description in cursor.description]
            equipment = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                'success': True,
                'equipment': equipment
            }
            
        except Exception as e:
            logger.error(f"Error getting employee equipment: {str(e)}")
            return {
                'success': False,
                'message': 'Error getting employee equipment',
                'error': str(e)
            }
    
    def get_equipment_inventory(self, status=None):
        """Get equipment inventory"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if status:
                cursor.execute('''
                    SELECT * FROM equipment WHERE status = ? ORDER BY asset_tag
                ''', (status,))
            else:
                cursor.execute('''
                    SELECT * FROM equipment ORDER BY asset_tag
                ''')
            
            columns = [description[0] for description in cursor.description]
            equipment = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                'success': True,
                'equipment': equipment
            }
            
        except Exception as e:
            logger.error(f"Error getting equipment inventory: {str(e)}")
            return {
                'success': False,
                'message': 'Error getting equipment inventory',
                'error': str(e)
            }
    
    def log_equipment_action(self, asset_tag, action, employee_id, details):
        """Log equipment action"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO equipment_history (asset_tag, action, employee_id, details)
                VALUES (?, ?, ?, ?)
            ''', (asset_tag, action, employee_id, details))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error logging equipment action: {str(e)}")
    
    def get_equipment_history(self, asset_tag):
        """Get equipment history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM equipment_history WHERE asset_tag = ?
                ORDER BY timestamp DESC
            ''', (asset_tag,))
            
            columns = [description[0] for description in cursor.description]
            history = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                'success': True,
                'history': history
            }
            
        except Exception as e:
            logger.error(f"Error getting equipment history: {str(e)}")
            return {
                'success': False,
                'message': 'Error getting equipment history',
                'error': str(e)
            }
    
    def generate_asset_tag(self, equipment_type, brand):
        """Generate unique asset tag"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            prefix = f"{equipment_type[:2].upper()}{brand[:2].upper()}"
            
            cursor.execute('''
                SELECT COUNT(*) FROM equipment WHERE asset_tag LIKE ?
            ''', (f"{prefix}%",))
            
            count = cursor.fetchone()[0]
            asset_tag = f"{prefix}{count + 1:04d}"
            
            conn.close()
            
            return asset_tag
            
        except Exception as e:
            logger.error(f"Error generating asset tag: {str(e)}")
            return f"EQ{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def create_qr_code(self, asset_tag, equipment_info):
        """Create QR code for equipment"""
        try:
            qr_data = {
                'asset_tag': asset_tag,
                'equipment_type': equipment_info['equipment_type'],
                'brand': equipment_info['brand'],
                'model': equipment_info['model'],
                'serial_number': equipment_info['serial_number']
            }
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(json.dumps(qr_data))
            qr.make(fit=True)
            
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            qr_path = os.path.join(os.path.dirname(self.db_path), 'qr_codes', f"{asset_tag}.png")
            os.makedirs(os.path.dirname(qr_path), exist_ok=True)
            
            qr_image.save(qr_path)
            
            logger.info(f"QR code created for {asset_tag}")
            return {
                'success': True,
                'qr_path': qr_path
            }
            
        except Exception as e:
            logger.error(f"Error creating QR code: {str(e)}")
            return {
                'success': False,
                'message': 'Error creating QR code',
                'error': str(e)
            }
    
    def get_equipment_statistics(self):
        """Get equipment statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT status, COUNT(*) as count FROM equipment GROUP BY status
            ''')
            
            status_counts = dict(cursor.fetchall())
            
            cursor.execute('''
                SELECT equipment_type, COUNT(*) as count FROM equipment GROUP BY equipment_type
            ''')
            
            type_counts = dict(cursor.fetchall())
            
            cursor.execute('''
                SELECT COUNT(*) FROM equipment WHERE assigned_employee_id IS NOT NULL
            ''')
            
            assigned_count = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM equipment WHERE status = 'Available'
            ''')
            
            available_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'success': True,
                'statistics': {
                    'total_equipment': sum(status_counts.values()),
                    'assigned_equipment': assigned_count,
                    'available_equipment': available_count,
                    'status_breakdown': status_counts,
                    'type_breakdown': type_counts
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting equipment statistics: {str(e)}")
            return {
                'success': False,
                'message': 'Error getting equipment statistics',
                'error': str(e)
            }
