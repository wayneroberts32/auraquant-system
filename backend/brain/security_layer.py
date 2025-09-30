"""
MongoDB Security Layer for AuraQuant Trading System
Engineer's Note: This adds enterprise-grade security to your existing system
WITHOUT modifying any existing code - works as a security wrapper
"""

import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import base64
import jwt
from functools import wraps
from dotenv import load_dotenv

# Load environment
load_dotenv()

class SecurityManager:
    """
    Enterprise-grade security manager for MongoDB data
    Handles encryption, access control, and audit logging
    """
    
    def __init__(self):
        """Initialize security manager with encryption keys"""
        # Get or generate encryption key
        self.master_key = self._get_or_create_master_key()
        self.fernet = Fernet(self.master_key)
        
        # JWT configuration for access tokens
        self.jwt_secret = os.getenv("JWT_SECRET_KEY", self._generate_jwt_secret())
        self.jwt_algorithm = "HS256"
        
        # Session management
        self.active_sessions = {}
        self.session_timeout = timedelta(hours=24)
        
        # Audit log
        self.audit_enabled = True
        self.audit_buffer = []
        
        # Access control levels
        self.access_levels = {
            'read': 1,
            'write': 2,
            'admin': 3,
            'system': 4
        }
        
        print("🔐 Security Layer Initialized")
        
    def _get_or_create_master_key(self) -> bytes:
        """Get or create master encryption key"""
        key_file = os.path.join(os.path.dirname(__file__), '.encryption_key')
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            # Save securely (in production, use key management service)
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)  # Restrict access
            return key
            
    def _generate_jwt_secret(self) -> str:
        """Generate secure JWT secret"""
        return secrets.token_urlsafe(64)
        
    def encrypt_sensitive_data(self, data: Any) -> Dict[str, Any]:
        """
        Encrypt sensitive trading data before MongoDB storage
        
        Args:
            data: Data to encrypt (dict, list, or string)
            
        Returns:
            Encrypted data package
        """
        try:
            # Convert to JSON string
            if isinstance(data, (dict, list)):
                data_str = json.dumps(data)
            else:
                data_str = str(data)
                
            # Encrypt
            encrypted = self.fernet.encrypt(data_str.encode())
            
            # Create secure package
            return {
                'encrypted': True,
                'data': encrypted.decode('utf-8'),
                'timestamp': datetime.now().isoformat(),
                'checksum': hashlib.sha256(data_str.encode()).hexdigest()
            }
            
        except Exception as e:
            self._log_security_event('encryption_error', {'error': str(e)})
            raise
            
    def decrypt_sensitive_data(self, encrypted_package: Dict[str, Any]) -> Any:
        """
        Decrypt data retrieved from MongoDB
        
        Args:
            encrypted_package: Encrypted data package
            
        Returns:
            Decrypted original data
        """
        try:
            if not encrypted_package.get('encrypted'):
                return encrypted_package
                
            # Decrypt
            encrypted_data = encrypted_package['data'].encode('utf-8')
            decrypted = self.fernet.decrypt(encrypted_data)
            data_str = decrypted.decode('utf-8')
            
            # Verify checksum
            checksum = hashlib.sha256(data_str.encode()).hexdigest()
            if checksum != encrypted_package.get('checksum'):
                raise ValueError("Data integrity check failed")
                
            # Parse back to original format
            try:
                return json.loads(data_str)
            except json.JSONDecodeError:
                return data_str
                
        except Exception as e:
            self._log_security_event('decryption_error', {'error': str(e)})
            raise
            
    def create_access_token(self, user_id: str, access_level: str = 'read') -> str:
        """
        Create JWT access token for API authentication
        
        Args:
            user_id: User identifier
            access_level: Access level (read, write, admin, system)
            
        Returns:
            JWT token
        """
        payload = {
            'user_id': user_id,
            'access_level': access_level,
            'issued_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + self.session_timeout).isoformat(),
            'session_id': secrets.token_hex(16)
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        
        # Store session
        self.active_sessions[payload['session_id']] = {
            'user_id': user_id,
            'access_level': access_level,
            'created': datetime.now(),
            'last_active': datetime.now()
        }
        
        self._log_security_event('token_created', {
            'user_id': user_id,
            'access_level': access_level
        })
        
        return token
        
    def verify_access_token(self, token: str) -> Tuple[bool, Dict]:
        """
        Verify JWT access token
        
        Args:
            token: JWT token to verify
            
        Returns:
            Tuple of (is_valid, payload)
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            # Check expiration
            expires_at = datetime.fromisoformat(payload['expires_at'])
            if datetime.now() > expires_at:
                return False, {'error': 'Token expired'}
                
            # Check session
            session_id = payload.get('session_id')
            if session_id not in self.active_sessions:
                return False, {'error': 'Invalid session'}
                
            # Update last active
            self.active_sessions[session_id]['last_active'] = datetime.now()
            
            return True, payload
            
        except jwt.InvalidTokenError as e:
            self._log_security_event('invalid_token', {'error': str(e)})
            return False, {'error': 'Invalid token'}
            
    def check_permission(self, token: str, required_level: str) -> bool:
        """
        Check if token has required permission level
        
        Args:
            token: JWT token
            required_level: Required access level
            
        Returns:
            True if authorized
        """
        is_valid, payload = self.verify_access_token(token)
        
        if not is_valid:
            return False
            
        user_level = self.access_levels.get(payload.get('access_level', 'read'), 0)
        required = self.access_levels.get(required_level, 999)
        
        return user_level >= required
        
    def secure_wrapper(required_level: str = 'read'):
        """
        Decorator for securing functions with access control
        
        Args:
            required_level: Minimum required access level
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Get token from kwargs or environment
                token = kwargs.pop('auth_token', None) or os.getenv('AUTH_TOKEN')
                
                if not token:
                    raise PermissionError("Authentication required")
                    
                security = SecurityManager()
                if not security.check_permission(token, required_level):
                    raise PermissionError(f"Insufficient permissions - {required_level} required")
                    
                return func(*args, **kwargs)
            return wrapper
        return decorator
        
    def hash_password(self, password: str) -> str:
        """
        Hash password for storage
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        salt = secrets.token_bytes(32)
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        # Combine salt and key
        return base64.urlsafe_b64encode(salt + key).decode('utf-8')
        
    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify password against hash
        
        Args:
            password: Plain text password
            hashed: Hashed password
            
        Returns:
            True if password matches
        """
        try:
            decoded = base64.urlsafe_b64decode(hashed.encode())
            salt = decoded[:32]
            stored_key = decoded[32:]
            
            kdf = PBKDF2(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            
            test_key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            
            return test_key == stored_key
            
        except Exception:
            return False
            
    def sanitize_input(self, data: Any) -> Any:
        """
        Sanitize user input to prevent injection attacks
        
        Args:
            data: Input data to sanitize
            
        Returns:
            Sanitized data
        """
        if isinstance(data, str):
            # Remove potentially dangerous characters
            dangerous_chars = ['$', '{', '}', ';', '&&', '||', '|', '`']
            sanitized = data
            for char in dangerous_chars:
                sanitized = sanitized.replace(char, '')
            return sanitized.strip()
            
        elif isinstance(data, dict):
            return {k: self.sanitize_input(v) for k, v in data.items()}
            
        elif isinstance(data, list):
            return [self.sanitize_input(item) for item in data]
            
        return data
        
    def _log_security_event(self, event_type: str, details: Dict):
        """
        Log security events for audit trail
        
        Args:
            event_type: Type of security event
            details: Event details
        """
        if not self.audit_enabled:
            return
            
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'details': details
        }
        
        self.audit_buffer.append(event)
        
        # Flush to MongoDB if buffer is large
        if len(self.audit_buffer) >= 100:
            self._flush_audit_log()
            
    def _flush_audit_log(self):
        """Flush audit log to MongoDB"""
        if not self.audit_buffer:
            return
            
        try:
            from brain.mongodb_persistence import get_persistence_service
            service = get_persistence_service()
            
            if service and service.db:
                service.db.security_audit.insert_many(self.audit_buffer)
                self.audit_buffer.clear()
                
        except Exception as e:
            print(f"Error flushing audit log: {e}")
            
    def create_api_key(self, user_id: str, description: str = "") -> str:
        """
        Create API key for programmatic access
        
        Args:
            user_id: User identifier
            description: API key description
            
        Returns:
            API key
        """
        api_key = f"ak_{secrets.token_urlsafe(32)}"
        
        # Store API key info (hash the key for storage)
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        key_info = {
            'key_hash': key_hash,
            'user_id': user_id,
            'description': description,
            'created': datetime.now().isoformat(),
            'last_used': None,
            'active': True
        }
        
        # Store in MongoDB
        try:
            from brain.mongodb_persistence import get_persistence_service
            service = get_persistence_service()
            if service and service.db:
                service.db.api_keys.insert_one(key_info)
                
        except Exception as e:
            print(f"Error storing API key: {e}")
            
        self._log_security_event('api_key_created', {
            'user_id': user_id,
            'description': description
        })
        
        return api_key
        
    def verify_api_key(self, api_key: str) -> Tuple[bool, Optional[str]]:
        """
        Verify API key
        
        Args:
            api_key: API key to verify
            
        Returns:
            Tuple of (is_valid, user_id)
        """
        try:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            from brain.mongodb_persistence import get_persistence_service
            service = get_persistence_service()
            
            if service and service.db:
                key_info = service.db.api_keys.find_one({
                    'key_hash': key_hash,
                    'active': True
                })
                
                if key_info:
                    # Update last used
                    service.db.api_keys.update_one(
                        {'key_hash': key_hash},
                        {'$set': {'last_used': datetime.now().isoformat()}}
                    )
                    
                    return True, key_info['user_id']
                    
        except Exception as e:
            print(f"Error verifying API key: {e}")
            
        return False, None

# Global instance
_security_manager = None

def get_security_manager():
    """Get or create security manager instance"""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager

# Helper functions for easy integration
def encrypt_data(data: Any) -> Dict:
    """Encrypt data before storing in MongoDB"""
    manager = get_security_manager()
    return manager.encrypt_sensitive_data(data)

def decrypt_data(encrypted_package: Dict) -> Any:
    """Decrypt data retrieved from MongoDB"""
    manager = get_security_manager()
    return manager.decrypt_sensitive_data(encrypted_package)

def create_token(user_id: str, access_level: str = 'read') -> str:
    """Create access token"""
    manager = get_security_manager()
    return manager.create_access_token(user_id, access_level)

def verify_token(token: str) -> Tuple[bool, Dict]:
    """Verify access token"""
    manager = get_security_manager()
    return manager.verify_access_token(token)