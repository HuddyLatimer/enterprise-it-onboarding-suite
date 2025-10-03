import os
import shutil
import sqlite3
import json
import logging
import zipfile
import schedule
import threading
import time
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, send_file
from app import db, Employee, Equipment, OnboardingLog, User, Role, Permission, UserSession

backup_bp = Blueprint('backup', __name__, url_prefix='/backup')
logger = logging.getLogger(__name__)

class BackupManager:
    def __init__(self):
        self.backup_dir = os.path.join(os.path.dirname(__file__), '..', 'backups')
        self.temp_dir = os.path.join(os.path.dirname(__file__), '..', 'temp')
        self.retention_days = 30
        self.max_backups = 10
        
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def create_full_backup(self):
        """Create full system backup"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"full_backup_{timestamp}"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            os.makedirs(backup_path, exist_ok=True)
            
            # Backup database
            self._backup_database(backup_path)
            
            # Backup configuration files
            self._backup_config_files(backup_path)
            
            # Backup logs
            self._backup_logs(backup_path)
            
            # Backup uploaded files
            self._backup_uploads(backup_path)
            
            # Create backup manifest
            self._create_backup_manifest(backup_path, 'full')
            
            # Compress backup
            compressed_path = self._compress_backup(backup_path)
            
            # Clean up temporary directory
            shutil.rmtree(backup_path)
            
            logger.info(f"Full backup created: {compressed_path}")
            return compressed_path
            
        except Exception as e:
            logger.error(f"Error creating full backup: {str(e)}")
            return None
    
    def create_database_backup(self):
        """Create database-only backup"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"database_backup_{timestamp}"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            os.makedirs(backup_path, exist_ok=True)
            
            # Backup database
            self._backup_database(backup_path)
            
            # Create backup manifest
            self._create_backup_manifest(backup_path, 'database')
            
            # Compress backup
            compressed_path = self._compress_backup(backup_path)
            
            # Clean up temporary directory
            shutil.rmtree(backup_path)
            
            logger.info(f"Database backup created: {compressed_path}")
            return compressed_path
            
        except Exception as e:
            logger.error(f"Error creating database backup: {str(e)}")
            return None
    
    def _backup_database(self, backup_path):
        """Backup SQLite database"""
        try:
            db_path = 'onboarding.db'
            if os.path.exists(db_path):
                backup_db_path = os.path.join(backup_path, 'onboarding.db')
                shutil.copy2(db_path, backup_db_path)
                
                # Also create SQL dump
                sql_dump_path = os.path.join(backup_path, 'database_dump.sql')
                self._create_sql_dump(sql_dump_path)
                
        except Exception as e:
            logger.error(f"Error backing up database: {str(e)}")
    
    def _create_sql_dump(self, dump_path):
        """Create SQL dump of database"""
        try:
            conn = sqlite3.connect('onboarding.db')
            
            with open(dump_path, 'w') as f:
                for line in conn.iterdump():
                    f.write(f"{line}\n")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error creating SQL dump: {str(e)}")
    
    def _backup_config_files(self, backup_path):
        """Backup configuration files"""
        try:
            config_dir = os.path.join(backup_path, 'config')
            os.makedirs(config_dir, exist_ok=True)
            
            config_files = ['.env', 'requirements.txt', 'app.py']
            
            for config_file in config_files:
                if os.path.exists(config_file):
                    shutil.copy2(config_file, config_dir)
            
            # Backup modules directory
            modules_dir = os.path.join(backup_path, 'modules')
            if os.path.exists('modules'):
                shutil.copytree('modules', modules_dir)
            
        except Exception as e:
            logger.error(f"Error backing up config files: {str(e)}")
    
    def _backup_logs(self, backup_path):
        """Backup log files"""
        try:
            logs_dir = os.path.join(backup_path, 'logs')
            if os.path.exists('logs'):
                shutil.copytree('logs', logs_dir)
            
        except Exception as e:
            logger.error(f"Error backing up logs: {str(e)}")
    
    def _backup_uploads(self, backup_path):
        """Backup uploaded files"""
        try:
            uploads_dir = os.path.join(backup_path, 'uploads')
            if os.path.exists('uploads'):
                shutil.copytree('uploads', uploads_dir)
            
        except Exception as e:
            logger.error(f"Error backing up uploads: {str(e)}")
    
    def _create_backup_manifest(self, backup_path, backup_type):
        """Create backup manifest file"""
        try:
            manifest = {
                'backup_type': backup_type,
                'created_at': datetime.now().isoformat(),
                'version': '1.0',
                'tables': {
                    'employees': Employee.query.count(),
                    'equipment': Equipment.query.count(),
                    'logs': OnboardingLog.query.count(),
                    'users': User.query.count(),
                    'roles': Role.query.count(),
                    'permissions': Permission.query.count(),
                    'sessions': UserSession.query.count()
                },
                'files': self._get_backup_files(backup_path)
            }
            
            manifest_path = os.path.join(backup_path, 'manifest.json')
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            
        except Exception as e:
            logger.error(f"Error creating backup manifest: {str(e)}")
    
    def _get_backup_files(self, backup_path):
        """Get list of files in backup"""
        try:
            files = []
            for root, dirs, filenames in os.walk(backup_path):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(file_path, backup_path)
                    file_size = os.path.getsize(file_path)
                    files.append({
                        'path': rel_path,
                        'size': file_size,
                        'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    })
            return files
            
        except Exception as e:
            logger.error(f"Error getting backup files: {str(e)}")
            return []
    
    def _compress_backup(self, backup_path):
        """Compress backup directory"""
        try:
            compressed_path = f"{backup_path}.zip"
            
            with zipfile.ZipFile(compressed_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(backup_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, backup_path)
                        zipf.write(file_path, arcname)
            
            return compressed_path
            
        except Exception as e:
            logger.error(f"Error compressing backup: {str(e)}")
            return None
    
    def restore_backup(self, backup_file_path):
        """Restore from backup file"""
        try:
            # Extract backup
            extract_path = os.path.join(self.temp_dir, f"restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            os.makedirs(extract_path, exist_ok=True)
            
            with zipfile.ZipFile(backup_file_path, 'r') as zipf:
                zipf.extractall(extract_path)
            
            # Read manifest
            manifest_path = os.path.join(extract_path, 'manifest.json')
            if not os.path.exists(manifest_path):
                raise Exception("Backup manifest not found")
            
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            # Restore database
            if manifest['backup_type'] in ['full', 'database']:
                self._restore_database(extract_path)
            
            # Restore configuration files
            if manifest['backup_type'] == 'full':
                self._restore_config_files(extract_path)
                self._restore_logs(extract_path)
                self._restore_uploads(extract_path)
            
            # Clean up
            shutil.rmtree(extract_path)
            
            logger.info(f"Backup restored successfully: {backup_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring backup: {str(e)}")
            return False
    
    def _restore_database(self, extract_path):
        """Restore database from backup"""
        try:
            backup_db_path = os.path.join(extract_path, 'onboarding.db')
            
            if os.path.exists(backup_db_path):
                # Backup current database
                current_db_path = 'onboarding.db'
                if os.path.exists(current_db_path):
                    backup_current_path = f"{current_db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    shutil.copy2(current_db_path, backup_current_path)
                
                # Restore database
                shutil.copy2(backup_db_path, current_db_path)
                
                logger.info("Database restored successfully")
            
        except Exception as e:
            logger.error(f"Error restoring database: {str(e)}")
    
    def _restore_config_files(self, extract_path):
        """Restore configuration files"""
        try:
            config_dir = os.path.join(extract_path, 'config')
            if os.path.exists(config_dir):
                for file in os.listdir(config_dir):
                    src_path = os.path.join(config_dir, file)
                    dst_path = file
                    shutil.copy2(src_path, dst_path)
            
        except Exception as e:
            logger.error(f"Error restoring config files: {str(e)}")
    
    def _restore_logs(self, extract_path):
        """Restore log files"""
        try:
            logs_dir = os.path.join(extract_path, 'logs')
            if os.path.exists(logs_dir):
                if os.path.exists('logs'):
                    shutil.rmtree('logs')
                shutil.copytree(logs_dir, 'logs')
            
        except Exception as e:
            logger.error(f"Error restoring logs: {str(e)}")
    
    def _restore_uploads(self, extract_path):
        """Restore uploaded files"""
        try:
            uploads_dir = os.path.join(extract_path, 'uploads')
            if os.path.exists(uploads_dir):
                if os.path.exists('uploads'):
                    shutil.rmtree('uploads')
                shutil.copytree(uploads_dir, 'uploads')
            
        except Exception as e:
            logger.error(f"Error restoring uploads: {str(e)}")
    
    def cleanup_old_backups(self):
        """Clean up old backups based on retention policy"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            backup_files = []
            for file in os.listdir(self.backup_dir):
                if file.endswith('.zip'):
                    file_path = os.path.join(self.backup_dir, file)
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    backup_files.append((file_path, file_time))
            
            # Sort by creation time (newest first)
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # Keep only the most recent backups
            backups_to_delete = backup_files[self.max_backups:]
            
            for backup_path, backup_time in backups_to_delete:
                if backup_time < cutoff_date:
                    os.remove(backup_path)
                    logger.info(f"Deleted old backup: {backup_path}")
            
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {str(e)}")
    
    def get_backup_list(self):
        """Get list of available backups"""
        try:
            backups = []
            
            for file in os.listdir(self.backup_dir):
                if file.endswith('.zip'):
                    file_path = os.path.join(self.backup_dir, file)
                    file_size = os.path.getsize(file_path)
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    backups.append({
                        'filename': file,
                        'size': file_size,
                        'created_at': file_time.isoformat(),
                        'size_mb': round(file_size / (1024 * 1024), 2)
                    })
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            
            return backups
            
        except Exception as e:
            logger.error(f"Error getting backup list: {str(e)}")
            return []
    
    def start_automated_backups(self):
        """Start automated backup schedule"""
        try:
            # Daily full backup at 2 AM
            schedule.every().day.at("02:00").do(self.create_full_backup)
            
            # Hourly database backup
            schedule.every().hour.do(self.create_database_backup)
            
            # Weekly cleanup
            schedule.every().week.do(self.cleanup_old_backups)
            
            def run_scheduler():
                while True:
                    schedule.run_pending()
                    time.sleep(60)
            
            scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
            scheduler_thread.start()
            
            logger.info("Automated backup scheduler started")
            
        except Exception as e:
            logger.error(f"Error starting automated backups: {str(e)}")

backup_manager = BackupManager()

@backup_bp.route('/dashboard')
def backup_dashboard():
    """Backup management dashboard"""
    return render_template('backup_management.html')

@backup_bp.route('/api/create', methods=['POST'])
def create_backup():
    """Create new backup"""
    try:
        backup_type = request.json.get('type', 'full')
        
        if backup_type == 'full':
            backup_path = backup_manager.create_full_backup()
        elif backup_type == 'database':
            backup_path = backup_manager.create_database_backup()
        else:
            return jsonify({'error': 'Invalid backup type'}), 400
        
        if backup_path:
            return jsonify({
                'success': True,
                'message': f'{backup_type.title()} backup created successfully',
                'backup_path': backup_path
            })
        else:
            return jsonify({'error': 'Failed to create backup'}), 500
        
    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}")
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/api/list')
def list_backups():
    """List available backups"""
    try:
        backups = backup_manager.get_backup_list()
        
        return jsonify({
            'success': True,
            'backups': backups
        })
        
    except Exception as e:
        logger.error(f"Error listing backups: {str(e)}")
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/api/download/<filename>')
def download_backup(filename):
    """Download backup file"""
    try:
        backup_path = os.path.join(backup_manager.backup_dir, filename)
        
        if not os.path.exists(backup_path):
            return jsonify({'error': 'Backup file not found'}), 404
        
        return send_file(backup_path, as_attachment=True)
        
    except Exception as e:
        logger.error(f"Error downloading backup: {str(e)}")
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/api/restore', methods=['POST'])
def restore_backup():
    """Restore from backup"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No backup file provided'}), 400
        
        backup_file = request.files['file']
        
        if backup_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save uploaded file temporarily
        temp_path = os.path.join(backup_manager.temp_dir, backup_file.filename)
        backup_file.save(temp_path)
        
        # Restore backup
        success = backup_manager.restore_backup(temp_path)
        
        # Clean up temporary file
        os.remove(temp_path)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Backup restored successfully'
            })
        else:
            return jsonify({'error': 'Failed to restore backup'}), 500
        
    except Exception as e:
        logger.error(f"Error restoring backup: {str(e)}")
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/api/delete/<filename>', methods=['DELETE'])
def delete_backup(filename):
    """Delete backup file"""
    try:
        backup_path = os.path.join(backup_manager.backup_dir, filename)
        
        if not os.path.exists(backup_path):
            return jsonify({'error': 'Backup file not found'}), 404
        
        os.remove(backup_path)
        
        return jsonify({
            'success': True,
            'message': 'Backup deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting backup: {str(e)}")
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/api/cleanup', methods=['POST'])
def cleanup_backups():
    """Clean up old backups"""
    try:
        backup_manager.cleanup_old_backups()
        
        return jsonify({
            'success': True,
            'message': 'Old backups cleaned up successfully'
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up backups: {str(e)}")
        return jsonify({'error': str(e)}), 500
