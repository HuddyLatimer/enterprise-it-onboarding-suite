import os
import time
import logging
from datetime import datetime, timedelta
from flask import request, jsonify, g
from functools import wraps
from collections import defaultdict, deque
import hashlib
import hmac
import secrets

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(deque)
        self.blocked_ips = set()
        self.rate_limits = {
            'default': {'requests': 100, 'window': 3600},  # 100 requests per hour
            'api': {'requests': 1000, 'window': 3600},    # 1000 API requests per hour
            'auth': {'requests': 10, 'window': 3600},      # 10 auth attempts per hour
            'upload': {'requests': 10, 'window': 3600},    # 10 uploads per hour
            'export': {'requests': 20, 'window': 3600}     # 20 exports per hour
        }
    
    def is_rate_limited(self, ip_address, endpoint_type='default'):
        """Check if IP is rate limited"""
        try:
            if ip_address in self.blocked_ips:
                return True
            
            current_time = time.time()
            window = self.rate_limits.get(endpoint_type, self.rate_limits['default'])
            
            # Clean old requests
            while (self.requests[ip_address] and 
                   self.requests[ip_address][0] < current_time - window['window']):
                self.requests[ip_address].popleft()
            
            # Check if limit exceeded
            if len(self.requests[ip_address]) >= window['requests']:
                logger.warning(f"Rate limit exceeded for IP: {ip_address}")
                return True
            
            # Add current request
            self.requests[ip_address].append(current_time)
            return False
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            return False
    
    def block_ip(self, ip_address, duration=3600):
        """Block IP address temporarily"""
        self.blocked_ips.add(ip_address)
        logger.warning(f"IP {ip_address} blocked for {duration} seconds")
    
    def unblock_ip(self, ip_address):
        """Unblock IP address"""
        self.blocked_ips.discard(ip_address)
        logger.info(f"IP {ip_address} unblocked")

rate_limiter = RateLimiter()

class SecurityHeaders:
    def __init__(self):
        self.headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com; img-src 'self' data:; font-src 'self' cdnjs.cloudflare.com;",
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
        }
    
    def add_headers(self, response):
        """Add security headers to response"""
        for header, value in self.headers.items():
            response.headers[header] = value
        return response

security_headers = SecurityHeaders()

class APIKeyManager:
    def __init__(self):
        self.api_keys = {}
        self.key_permissions = {}
    
    def generate_api_key(self, name, permissions=None):
        """Generate new API key"""
        try:
            key = secrets.token_urlsafe(32)
            self.api_keys[key] = {
                'name': name,
                'created_at': datetime.utcnow(),
                'last_used': None,
                'is_active': True
            }
            self.key_permissions[key] = permissions or []
            
            logger.info(f"API key generated for: {name}")
            return key
            
        except Exception as e:
            logger.error(f"Error generating API key: {str(e)}")
            return None
    
    def validate_api_key(self, api_key):
        """Validate API key"""
        try:
            if api_key not in self.api_keys:
                return False
            
            key_info = self.api_keys[api_key]
            if not key_info['is_active']:
                return False
            
            # Update last used
            key_info['last_used'] = datetime.utcnow()
            return True
            
        except Exception as e:
            logger.error(f"Error validating API key: {str(e)}")
            return False
    
    def revoke_api_key(self, api_key):
        """Revoke API key"""
        try:
            if api_key in self.api_keys:
                self.api_keys[api_key]['is_active'] = False
                logger.info(f"API key revoked: {api_key}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error revoking API key: {str(e)}")
            return False

api_key_manager = APIKeyManager()

class InputValidator:
    def __init__(self):
        self.max_string_length = 255
        self.max_text_length = 10000
        self.allowed_file_extensions = {'.csv', '.xlsx', '.json', '.txt'}
        self.max_file_size = 16 * 1024 * 1024  # 16MB
    
    def validate_string(self, value, field_name, max_length=None):
        """Validate string input"""
        try:
            if not isinstance(value, str):
                return False, f"{field_name} must be a string"
            
            if len(value) > (max_length or self.max_string_length):
                return False, f"{field_name} too long"
            
            # Check for SQL injection patterns
            dangerous_patterns = [';', '--', '/*', '*/', 'xp_', 'sp_', 'exec', 'execute']
            if any(pattern in value.lower() for pattern in dangerous_patterns):
                return False, f"{field_name} contains invalid characters"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating string: {str(e)}")
            return False, "Validation error"
    
    def validate_email(self, email):
        """Validate email format"""
        try:
            import re
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return bool(re.match(pattern, email))
        except Exception as e:
            logger.error(f"Error validating email: {str(e)}")
            return False
    
    def validate_file(self, file):
        """Validate uploaded file"""
        try:
            if not file:
                return False, "No file provided"
            
            if file.content_length > self.max_file_size:
                return False, "File too large"
            
            filename = file.filename
            if not filename:
                return False, "No filename provided"
            
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext not in self.allowed_file_extensions:
                return False, "Invalid file type"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating file: {str(e)}")
            return False, "File validation error"

input_validator = InputValidator()

def rate_limit(endpoint_type='default'):
    """Decorator for rate limiting"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            if ',' in ip_address:
                ip_address = ip_address.split(',')[0].strip()
            
            if rate_limiter.is_rate_limited(ip_address, endpoint_type):
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': 'Too many requests. Please try again later.'
                }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_api_key(f):
    """Decorator to require API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        if not api_key_manager.validate_api_key(api_key):
            return jsonify({'error': 'Invalid API key'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def validate_input(required_fields=None, optional_fields=None):
    """Decorator to validate input data"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                data = request.get_json() or {}
                
                # Validate required fields
                if required_fields:
                    for field in required_fields:
                        if field not in data:
                            return jsonify({'error': f'Missing required field: {field}'}), 400
                        
                        is_valid, error_msg = input_validator.validate_string(
                            data[field], field
                        )
                        if not is_valid:
                            return jsonify({'error': error_msg}), 400
                
                # Validate optional fields
                if optional_fields:
                    for field in optional_fields:
                        if field in data:
                            is_valid, error_msg = input_validator.validate_string(
                                data[field], field
                            )
                            if not is_valid:
                                return jsonify({'error': error_msg}), 400
                
                # Validate email fields
                email_fields = ['email', 'manager_email']
                for field in email_fields:
                    if field in data and data[field]:
                        if not input_validator.validate_email(data[field]):
                            return jsonify({'error': f'Invalid email format: {field}'}), 400
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Input validation error: {str(e)}")
                return jsonify({'error': 'Invalid input data'}), 400
        
        return decorated_function
    return decorator

def log_api_access(f):
    """Decorator to log API access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            user_agent = request.headers.get('User-Agent', 'Unknown')
            endpoint = request.endpoint
            method = request.method
            
            logger.info(f"API Access: {method} {endpoint} from {ip_address}")
            
            result = f(*args, **kwargs)
            
            # Log response status
            if hasattr(result, 'status_code'):
                logger.info(f"API Response: {result.status_code} for {endpoint}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error logging API access: {str(e)}")
            return f(*args, **kwargs)
    
    return decorated_function

def secure_headers(f):
    """Decorator to add security headers"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        result = f(*args, **kwargs)
        
        if hasattr(result, 'headers'):
            result = security_headers.add_headers(result)
        
        return result
    
    return decorated_function

class SecurityAuditLogger:
    def __init__(self):
        self.audit_log_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'security_audit.log')
        os.makedirs(os.path.dirname(self.audit_log_file), exist_ok=True)
    
    def log_security_event(self, event_type, details, ip_address=None, user_id=None):
        """Log security event"""
        try:
            timestamp = datetime.utcnow().isoformat()
            log_entry = f"{timestamp} | {event_type} | IP: {ip_address} | User: {user_id} | {details}\n"
            
            with open(self.audit_log_file, 'a') as f:
                f.write(log_entry)
                
        except Exception as e:
            logger.error(f"Error logging security event: {str(e)}")

security_audit = SecurityAuditLogger()

def audit_security_event(event_type):
    """Decorator to audit security events"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
                user_id = getattr(g, 'user_id', None)
                
                result = f(*args, **kwargs)
                
                # Log based on result
                if hasattr(result, 'status_code'):
                    if result.status_code >= 400:
                        security_audit.log_security_event(
                            f"{event_type}_FAILED",
                            f"Status: {result.status_code}",
                            ip_address,
                            user_id
                        )
                    else:
                        security_audit.log_security_event(
                            f"{event_type}_SUCCESS",
                            f"Status: {result.status_code}",
                            ip_address,
                            user_id
                        )
                
                return result
                
            except Exception as e:
                logger.error(f"Error auditing security event: {str(e)}")
                return f(*args, **kwargs)
        
        return decorated_function
    return decorator
