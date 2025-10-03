import os
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session, redirect, url_for
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
logger = logging.getLogger(__name__)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')
    department = db.Column(db.String(50), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'department': self.department,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    permissions = db.Column(db.Text, nullable=True)  # JSON string of permissions
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'permissions': self.permissions
        }

class Permission(db.Model):
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    resource = db.Column(db.String(50), nullable=False)  # employees, equipment, analytics, etc.
    action = db.Column(db.String(50), nullable=False)   # create, read, update, delete
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'resource': self.resource,
            'action': self.action
        }

class UserSession(db.Model):
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_token = db.Column(db.String(255), unique=True, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    user = db.relationship('User', backref=db.backref('sessions', lazy=True))

class RoleManager:
    def __init__(self):
        self.default_roles = {
            'admin': {
                'description': 'System Administrator',
                'permissions': ['*']  # All permissions
            },
            'hr_manager': {
                'description': 'HR Manager',
                'permissions': [
                    'employees:create', 'employees:read', 'employees:update',
                    'analytics:read', 'notifications:read', 'bulk_operations:read'
                ]
            },
            'it_manager': {
                'description': 'IT Manager',
                'permissions': [
                    'employees:read', 'employees:update',
                    'equipment:create', 'equipment:read', 'equipment:update', 'equipment:delete',
                    'analytics:read', 'notifications:read', 'bulk_operations:read'
                ]
            },
            'it_support': {
                'description': 'IT Support',
                'permissions': [
                    'employees:read', 'equipment:read', 'equipment:update',
                    'notifications:read'
                ]
            },
            'user': {
                'description': 'Regular User',
                'permissions': [
                    'employees:read'
                ]
            }
        }
    
    def initialize_default_roles(self):
        """Initialize default roles and permissions"""
        try:
            for role_name, role_data in self.default_roles.items():
                existing_role = Role.query.filter_by(name=role_name).first()
                if not existing_role:
                    role = Role(
                        name=role_name,
                        description=role_data['description'],
                        permissions=','.join(role_data['permissions'])
                    )
                    db.session.add(role)
            
            db.session.commit()
            logger.info("Default roles initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing default roles: {str(e)}")
            db.session.rollback()
    
    def get_user_permissions(self, user):
        """Get user permissions based on role"""
        try:
            if user.role == 'admin':
                return ['*']  # Admin has all permissions
            
            role = Role.query.filter_by(name=user.role).first()
            if not role:
                return []
            
            permissions = role.permissions.split(',') if role.permissions else []
            return [p.strip() for p in permissions]
            
        except Exception as e:
            logger.error(f"Error getting user permissions: {str(e)}")
            return []
    
    def has_permission(self, user, resource, action):
        """Check if user has specific permission"""
        try:
            permissions = self.get_user_permissions(user)
            
            if '*' in permissions:
                return True
            
            permission_string = f"{resource}:{action}"
            return permission_string in permissions
            
        except Exception as e:
            logger.error(f"Error checking permission: {str(e)}")
            return False

role_manager = RoleManager()

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def permission_required(resource, action):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            user = User.query.get(session['user_id'])
            if not user:
                return jsonify({'error': 'User not found'}), 401
            
            if not role_manager.has_permission(user, resource, action):
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        user = User.query.get(session['user_id'])
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        user = User.query.filter_by(username=username, is_active=True).first()
        
        if not user or not user.check_password(password):
            logger.warning(f"Failed login attempt for username: {username}")
            return jsonify({'error': 'Invalid credentials'}), 401
        
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"User {username} logged in successfully")
        
        return jsonify({
            'success': True,
            'user': user.to_dict(),
            'permissions': role_manager.get_user_permissions(user)
        })
        
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """User logout"""
    try:
        if 'user_id' in session:
            user_id = session['user_id']
            
            UserSession.query.filter_by(
                user_id=user_id,
                is_active=True
            ).update({'is_active': False})
            
            db.session.commit()
        
        session.clear()
        
        return jsonify({'success': True, 'message': 'Logged out successfully'})
        
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        return jsonify({'error': 'Logout failed'}), 500

@auth_bp.route('/register', methods=['POST'])
@admin_required
def register():
    """Register new user (admin only)"""
    try:
        data = request.get_json()
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'user')
        department = data.get('department')
        
        if not all([username, email, password]):
            return jsonify({'error': 'Username, email, and password required'}), 400
        
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        user = User(
            username=username,
            email=email,
            role=role,
            department=department
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"New user registered: {username} with role {role}")
        
        return jsonify({
            'success': True,
            'user': user.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Registration failed'}), 500

@auth_bp.route('/profile')
@login_required
def get_profile():
    """Get current user profile"""
    try:
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'user': user.to_dict(),
            'permissions': role_manager.get_user_permissions(user)
        })
        
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}")
        return jsonify({'error': 'Failed to get profile'}), 500

@auth_bp.route('/users')
@admin_required
def get_users():
    """Get all users (admin only)"""
    try:
        users = User.query.all()
        
        return jsonify({
            'success': True,
            'users': [user.to_dict() for user in users]
        })
        
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        return jsonify({'error': 'Failed to get users'}), 500

@auth_bp.route('/roles')
@admin_required
def get_roles():
    """Get all roles (admin only)"""
    try:
        roles = Role.query.all()
        
        return jsonify({
            'success': True,
            'roles': [role.to_dict() for role in roles]
        })
        
    except Exception as e:
        logger.error(f"Error getting roles: {str(e)}")
        return jsonify({'error': 'Failed to get roles'}), 500

@auth_bp.route('/permissions')
@admin_required
def get_permissions():
    """Get all permissions (admin only)"""
    try:
        permissions = Permission.query.all()
        
        return jsonify({
            'success': True,
            'permissions': [perm.to_dict() for perm in permissions]
        })
        
    except Exception as e:
        logger.error(f"Error getting permissions: {str(e)}")
        return jsonify({'error': 'Failed to get permissions'}), 500

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    try:
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not all([current_password, new_password]):
            return jsonify({'error': 'Current and new password required'}), 400
        
        user = User.query.get(session['user_id'])
        if not user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        user.set_password(new_password)
        db.session.commit()
        
        logger.info(f"Password changed for user: {user.username}")
        
        return jsonify({'success': True, 'message': 'Password changed successfully'})
        
    except Exception as e:
        logger.error(f"Error changing password: {str(e)}")
        return jsonify({'error': 'Failed to change password'}), 500

def create_default_admin():
    """Create default admin user"""
    try:
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@company.com',
                role='admin',
                department='IT'
            )
            admin_user.set_password('admin123')  # Change this in production!
            
            db.session.add(admin_user)
            db.session.commit()
            
            logger.info("Default admin user created")
        
        return admin_user
        
    except Exception as e:
        logger.error(f"Error creating default admin: {str(e)}")
        return None
