import os
import logging
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
import hashlib
import secrets

logger = logging.getLogger(__name__)

class SecurityManager:
    def __init__(self):
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
    
    def _get_or_create_encryption_key(self):
        """Get or create encryption key for sensitive data"""
        key_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'encryption.key')
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def encrypt_password(self, password):
        """Encrypt a password for storage"""
        try:
            encrypted_password = self.cipher_suite.encrypt(password.encode())
            return encrypted_password.decode()
        except Exception as e:
            logger.error(f"Error encrypting password: {str(e)}")
            return None
    
    def decrypt_password(self, encrypted_password):
        """Decrypt a password for use"""
        try:
            decrypted_password = self.cipher_suite.decrypt(encrypted_password.encode())
            return decrypted_password.decode()
        except Exception as e:
            logger.error(f"Error decrypting password: {str(e)}")
            return None
    
    def generate_secure_password(self, length=16):
        """Generate a secure random password"""
        characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*"
        password = ''.join(secrets.choice(characters) for _ in range(length))
        return password
    
    def hash_password(self, password):
        """Hash a password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def validate_password_strength(self, password):
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            return False, "Password must contain at least one special character"
        
        return True, "Password is strong"

class AuditLogger:
    def __init__(self):
        self.log_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'audit.log')
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
    
    def log_action(self, user_id, action, details, status='SUCCESS'):
        """Log an audit action"""
        timestamp = datetime.utcnow().isoformat()
        log_entry = f"{timestamp} | {user_id} | {action} | {status} | {details}\n"
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_entry)
        except Exception as e:
            logger.error(f"Error writing audit log: {str(e)}")
    
    def log_login_attempt(self, user_id, ip_address, success=True):
        """Log login attempt"""
        status = 'SUCCESS' if success else 'FAILED'
        details = f"IP: {ip_address}"
        self.log_action(user_id, 'LOGIN_ATTEMPT', details, status)
    
    def log_user_creation(self, user_id, employee_id, success=True):
        """Log user creation"""
        status = 'SUCCESS' if success else 'FAILED'
        details = f"Employee ID: {employee_id}"
        self.log_action(user_id, 'USER_CREATION', details, status)
    
    def log_password_change(self, user_id, employee_id, success=True):
        """Log password change"""
        status = 'SUCCESS' if success else 'FAILED'
        details = f"Employee ID: {employee_id}"
        self.log_action(user_id, 'PASSWORD_CHANGE', details, status)

class AccessControl:
    def __init__(self):
        self.allowed_ips = self._load_allowed_ips()
        self.blocked_ips = self._load_blocked_ips()
    
    def _load_allowed_ips(self):
        """Load allowed IP addresses from configuration"""
        allowed_ips_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'allowed_ips.txt')
        
        if os.path.exists(allowed_ips_file):
            with open(allowed_ips_file, 'r') as f:
                return [line.strip() for line in f if line.strip()]
        return []
    
    def _load_blocked_ips(self):
        """Load blocked IP addresses from configuration"""
        blocked_ips_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'blocked_ips.txt')
        
        if os.path.exists(blocked_ips_file):
            with open(blocked_ips_file, 'r') as f:
                return [line.strip() for line in f if line.strip()]
        return []
    
    def is_ip_allowed(self, ip_address):
        """Check if IP address is allowed"""
        if self.allowed_ips and ip_address not in self.allowed_ips:
            return False
        
        if ip_address in self.blocked_ips:
            return False
        
        return True
    
    def add_blocked_ip(self, ip_address):
        """Add IP address to blocked list"""
        if ip_address not in self.blocked_ips:
            self.blocked_ips.append(ip_address)
            self._save_blocked_ips()
    
    def _save_blocked_ips(self):
        """Save blocked IP addresses to file"""
        blocked_ips_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'blocked_ips.txt')
        os.makedirs(os.path.dirname(blocked_ips_file), exist_ok=True)
        
        with open(blocked_ips_file, 'w') as f:
            for ip in self.blocked_ips:
                f.write(f"{ip}\n")

class SessionManager:
    def __init__(self):
        self.active_sessions = {}
        self.session_timeout = timedelta(hours=8)
    
    def create_session(self, user_id, ip_address):
        """Create a new session"""
        session_id = secrets.token_urlsafe(32)
        self.active_sessions[session_id] = {
            'user_id': user_id,
            'ip_address': ip_address,
            'created_at': datetime.utcnow(),
            'last_activity': datetime.utcnow()
        }
        return session_id
    
    def validate_session(self, session_id, ip_address):
        """Validate an existing session"""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        
        if session['ip_address'] != ip_address:
            return False
        
        if datetime.utcnow() - session['last_activity'] > self.session_timeout:
            del self.active_sessions[session_id]
            return False
        
        session['last_activity'] = datetime.utcnow()
        return True
    
    def destroy_session(self, session_id):
        """Destroy a session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        current_time = datetime.utcnow()
        expired_sessions = [
            session_id for session_id, session in self.active_sessions.items()
            if current_time - session['last_activity'] > self.session_timeout
        ]
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]

def validate_environment():
    """Validate environment configuration"""
    required_vars = [
        'DATABASE_URL',
        'AD_SERVER',
        'AD_DOMAIN',
        'AD_USERNAME',
        'AD_PASSWORD',
        'O365_TENANT_ID',
        'O365_CLIENT_ID',
        'O365_CLIENT_SECRET',
        'SMTP_SERVER',
        'SMTP_USERNAME',
        'SMTP_PASSWORD',
        'SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    return True

def setup_logging():
    """Setup secure logging configuration"""
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, 'application.log')),
            logging.StreamHandler()
        ]
    )
    
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

def create_directories():
    """Create necessary directories"""
    directories = [
        'data',
        'logs',
        'config',
        'modules/scripts',
        'templates',
        'static'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def initialize_security():
    """Initialize security components"""
    try:
        create_directories()
        setup_logging()
        
        if not validate_environment():
            raise Exception("Environment validation failed")
        
        logger.info("Security initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Security initialization failed: {str(e)}")
        return False
