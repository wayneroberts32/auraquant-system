#!/usr/bin/env python3
"""
AuraQuant Admin Management System
Engineer's Note: Complete admin control for users, AI agents, and system monitoring
Handles user CRUD, agent deployment, role-based access control
"""

import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import jwt
from pathlib import Path
import logging

# MongoDB imports
from pymongo import MongoClient
from bson import ObjectId

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserRole(Enum):
    """User role definitions"""
    ADMIN = "admin"           # Full system access
    TRADER = "trader"         # Trading access
    VIEWER = "viewer"         # Read-only access
    DEMO = "demo"            # Demo account
    SUSPENDED = "suspended"   # Account suspended

class AgentType(Enum):
    """AI Agent types"""
    TRADING = "trading"           # Trading execution agent
    ANALYSIS = "analysis"         # Market analysis agent
    RISK = "risk"                # Risk management agent
    RESEARCH = "research"         # Research agent
    ARBITRAGE = "arbitrage"       # Arbitrage detection
    NEWS = "news"                # News sentiment agent
    PATTERN = "pattern"          # Pattern recognition
    QUANTUM = "quantum"          # Quantum computing agent

@dataclass
class User:
    """User data structure"""
    id: str
    email: str
    username: str
    role: UserRole
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool
    settings: Dict[str, Any]
    api_keys: List[Dict[str, str]]
    trading_limits: Dict[str, Any]

@dataclass
class AIAgent:
    """AI Agent data structure"""
    id: str
    name: str
    type: AgentType
    status: str  # active, paused, stopped
    owner_id: str  # User who owns this agent
    configuration: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    created_at: datetime
    last_active: datetime

class AdminManagementSystem:
    """
    Comprehensive admin management system for AuraQuant
    Handles users, AI agents, and system administration
    """
    
    def __init__(self):
        """Initialize admin system"""
        # Database connection
        self.mongo_uri = os.getenv("MONGO_URI", os.getenv("MONGODB_URI", ""))
        self.db_name = os.getenv("MONGODB_DATABASE", "auraquant")
        
        # JWT configuration
        self.jwt_secret = os.getenv("JWT_SECRET_KEY", "auraquant-secret-key-2025")
        self.jwt_algorithm = "HS256"
        self.jwt_expiration_hours = 24
        
        # Initialize database
        self.client = None
        self.db = None
        self._initialize_database()
        
        # Admin defaults
        self.default_admin_email = os.getenv("ADMIN_EMAIL", "wayneroberts32@outlook.com.au")
        self.max_agents_per_user = 10
        self.max_api_keys_per_user = 5
        
        # Create default admin if doesn't exist
        self._ensure_admin_exists()
        
    def _initialize_database(self):
        """Initialize MongoDB connection"""
        if not self.mongo_uri:
            logger.warning("MongoDB not configured - using local storage")
            return
            
        try:
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            self.db = self.client[self.db_name]
            
            # Create indexes
            self.db.users.create_index("email", unique=True)
            self.db.users.create_index("username", unique=True)
            self.db.agents.create_index("owner_id")
            self.db.agents.create_index("type")
            
            logger.info("✅ Admin Management System connected to MongoDB")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            
    def _ensure_admin_exists(self):
        """Create default admin user if doesn't exist"""
        if not self.db:
            return
            
        try:
            existing_admin = self.db.users.find_one({"email": self.default_admin_email})
            
            if not existing_admin:
                admin_user = {
                    "email": self.default_admin_email,
                    "username": "admin",
                    "password_hash": self._hash_password("admin123"),  # Change in production
                    "role": UserRole.ADMIN.value,
                    "created_at": datetime.now(),
                    "is_active": True,
                    "settings": {
                        "theme": "dark",
                        "notifications": True,
                        "two_factor": False
                    },
                    "api_keys": [],
                    "trading_limits": {
                        "max_daily_trades": -1,  # Unlimited
                        "max_position_size": -1,  # Unlimited
                        "max_daily_loss": -1      # Unlimited
                    }
                }
                
                self.db.users.insert_one(admin_user)
                logger.info(f"✅ Created default admin user: {self.default_admin_email}")
                
        except Exception as e:
            logger.error(f"Failed to create admin user: {e}")
            
    # =====================
    # User Management
    # =====================
    
    def create_user(self, admin_token: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new user (Admin only)
        
        Args:
            admin_token: Admin JWT token
            user_data: User information
            
        Returns:
            Created user or error
        """
        # Verify admin
        if not self._verify_admin(admin_token):
            return {"success": False, "error": "Unauthorized - Admin access required"}
            
        try:
            # Check if user exists
            existing = self.db.users.find_one({
                "$or": [
                    {"email": user_data["email"]},
                    {"username": user_data["username"]}
                ]
            })
            
            if existing:
                return {"success": False, "error": "User already exists"}
                
            # Create user
            new_user = {
                "email": user_data["email"],
                "username": user_data["username"],
                "password_hash": self._hash_password(user_data["password"]),
                "role": user_data.get("role", UserRole.TRADER.value),
                "created_at": datetime.now(),
                "last_login": None,
                "is_active": True,
                "settings": user_data.get("settings", {
                    "theme": "dark",
                    "notifications": True,
                    "two_factor": False
                }),
                "api_keys": [],
                "trading_limits": user_data.get("trading_limits", {
                    "max_daily_trades": 100,
                    "max_position_size": 10000,
                    "max_daily_loss": 1000
                })
            }
            
            result = self.db.users.insert_one(new_user)
            new_user["_id"] = str(result.inserted_id)
            
            logger.info(f"Created new user: {user_data['email']}")
            
            return {
                "success": True,
                "user": self._sanitize_user(new_user)
            }
            
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return {"success": False, "error": str(e)}
            
    def update_user(self, admin_token: str, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user information (Admin only)"""
        if not self._verify_admin(admin_token):
            return {"success": False, "error": "Unauthorized"}
            
        try:
            # Don't allow password updates through this method
            updates.pop("password", None)
            updates.pop("password_hash", None)
            
            result = self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": updates}
            )
            
            if result.modified_count > 0:
                return {"success": True, "message": "User updated"}
            else:
                return {"success": False, "error": "User not found"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def delete_user(self, admin_token: str, user_id: str) -> Dict[str, Any]:
        """Delete user (Admin only)"""
        if not self._verify_admin(admin_token):
            return {"success": False, "error": "Unauthorized"}
            
        try:
            # First delete user's agents
            self.db.agents.delete_many({"owner_id": user_id})
            
            # Delete user
            result = self.db.users.delete_one({"_id": ObjectId(user_id)})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted user: {user_id}")
                return {"success": True, "message": "User deleted"}
            else:
                return {"success": False, "error": "User not found"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def list_users(self, admin_token: str, limit: int = 100) -> Dict[str, Any]:
        """List all users (Admin only)"""
        if not self._verify_admin(admin_token):
            return {"success": False, "error": "Unauthorized"}
            
        try:
            users = []
            for user in self.db.users.find().limit(limit):
                users.append(self._sanitize_user(user))
                
            return {
                "success": True,
                "users": users,
                "total": self.db.users.count_documents({})
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def suspend_user(self, admin_token: str, user_id: str, reason: str = "") -> Dict[str, Any]:
        """Suspend user account (Admin only)"""
        if not self._verify_admin(admin_token):
            return {"success": False, "error": "Unauthorized"}
            
        try:
            result = self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "role": UserRole.SUSPENDED.value,
                        "is_active": False,
                        "suspension_reason": reason,
                        "suspended_at": datetime.now()
                    }
                }
            )
            
            # Stop user's agents
            self.db.agents.update_many(
                {"owner_id": user_id},
                {"$set": {"status": "stopped"}}
            )
            
            if result.modified_count > 0:
                logger.info(f"Suspended user: {user_id}")
                return {"success": True, "message": "User suspended"}
            else:
                return {"success": False, "error": "User not found"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    # =====================
    # AI Agent Management
    # =====================
    
    def create_agent(self, user_token: str, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new AI agent
        
        Args:
            user_token: User JWT token
            agent_data: Agent configuration
            
        Returns:
            Created agent or error
        """
        user = self._verify_user(user_token)
        if not user:
            return {"success": False, "error": "Unauthorized"}
            
        try:
            # Check agent limit
            agent_count = self.db.agents.count_documents({"owner_id": str(user["_id"])})
            if agent_count >= self.max_agents_per_user and user["role"] != UserRole.ADMIN.value:
                return {"success": False, "error": f"Agent limit reached ({self.max_agents_per_user})"}
                
            # Create agent
            new_agent = {
                "name": agent_data["name"],
                "type": agent_data["type"],
                "status": "active",
                "owner_id": str(user["_id"]),
                "configuration": agent_data.get("configuration", {
                    "strategy": "default",
                    "risk_level": "medium",
                    "max_positions": 5,
                    "stop_loss": 0.02,
                    "take_profit": 0.05,
                    "indicators": ["RSI", "MACD", "BB"]
                }),
                "performance_metrics": {
                    "total_trades": 0,
                    "winning_trades": 0,
                    "losing_trades": 0,
                    "profit_loss": 0.0,
                    "win_rate": 0.0,
                    "sharpe_ratio": 0.0
                },
                "created_at": datetime.now(),
                "last_active": datetime.now()
            }
            
            result = self.db.agents.insert_one(new_agent)
            new_agent["_id"] = str(result.inserted_id)
            
            logger.info(f"Created agent '{agent_data['name']}' for user {user['email']}")
            
            return {
                "success": True,
                "agent": new_agent
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def update_agent(self, user_token: str, agent_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update AI agent configuration"""
        user = self._verify_user(user_token)
        if not user:
            return {"success": False, "error": "Unauthorized"}
            
        try:
            # Verify ownership or admin
            agent = self.db.agents.find_one({"_id": ObjectId(agent_id)})
            if not agent:
                return {"success": False, "error": "Agent not found"}
                
            if agent["owner_id"] != str(user["_id"]) and user["role"] != UserRole.ADMIN.value:
                return {"success": False, "error": "Unauthorized"}
                
            # Update agent
            updates["last_active"] = datetime.now()
            result = self.db.agents.update_one(
                {"_id": ObjectId(agent_id)},
                {"$set": updates}
            )
            
            if result.modified_count > 0:
                return {"success": True, "message": "Agent updated"}
            else:
                return {"success": False, "error": "No changes made"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def delete_agent(self, user_token: str, agent_id: str) -> Dict[str, Any]:
        """Delete AI agent"""
        user = self._verify_user(user_token)
        if not user:
            return {"success": False, "error": "Unauthorized"}
            
        try:
            # Verify ownership or admin
            agent = self.db.agents.find_one({"_id": ObjectId(agent_id)})
            if not agent:
                return {"success": False, "error": "Agent not found"}
                
            if agent["owner_id"] != str(user["_id"]) and user["role"] != UserRole.ADMIN.value:
                return {"success": False, "error": "Unauthorized"}
                
            # Delete agent
            result = self.db.agents.delete_one({"_id": ObjectId(agent_id)})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted agent: {agent_id}")
                return {"success": True, "message": "Agent deleted"}
            else:
                return {"success": False, "error": "Agent not found"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def list_agents(self, user_token: str) -> Dict[str, Any]:
        """List user's AI agents (or all for admin)"""
        user = self._verify_user(user_token)
        if not user:
            return {"success": False, "error": "Unauthorized"}
            
        try:
            # Admin sees all agents
            if user["role"] == UserRole.ADMIN.value:
                agents = list(self.db.agents.find())
            else:
                agents = list(self.db.agents.find({"owner_id": str(user["_id"])}))
                
            # Convert ObjectIds to strings
            for agent in agents:
                agent["_id"] = str(agent["_id"])
                
            return {
                "success": True,
                "agents": agents,
                "total": len(agents)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def control_agent(self, user_token: str, agent_id: str, action: str) -> Dict[str, Any]:
        """Control agent status (start/stop/pause)"""
        user = self._verify_user(user_token)
        if not user:
            return {"success": False, "error": "Unauthorized"}
            
        try:
            # Verify ownership or admin
            agent = self.db.agents.find_one({"_id": ObjectId(agent_id)})
            if not agent:
                return {"success": False, "error": "Agent not found"}
                
            if agent["owner_id"] != str(user["_id"]) and user["role"] != UserRole.ADMIN.value:
                return {"success": False, "error": "Unauthorized"}
                
            # Update status
            status_map = {
                "start": "active",
                "stop": "stopped",
                "pause": "paused"
            }
            
            if action not in status_map:
                return {"success": False, "error": "Invalid action"}
                
            result = self.db.agents.update_one(
                {"_id": ObjectId(agent_id)},
                {"$set": {"status": status_map[action], "last_active": datetime.now()}}
            )
            
            if result.modified_count > 0:
                logger.info(f"Agent {agent_id} status changed to {status_map[action]}")
                return {"success": True, "message": f"Agent {action}ed"}
            else:
                return {"success": False, "error": "Failed to update agent"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    # =====================
    # Authentication
    # =====================
    
    def authenticate(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user and return JWT token"""
        try:
            user = self.db.users.find_one({"email": email})
            
            if not user:
                return {"success": False, "error": "Invalid credentials"}
                
            if not self._verify_password(password, user["password_hash"]):
                return {"success": False, "error": "Invalid credentials"}
                
            if not user.get("is_active", True):
                return {"success": False, "error": "Account suspended"}
                
            # Generate JWT token
            token = self._generate_token(user)
            
            # Update last login
            self.db.users.update_one(
                {"_id": user["_id"]},
                {"$set": {"last_login": datetime.now()}}
            )
            
            return {
                "success": True,
                "token": token,
                "user": self._sanitize_user(user)
            }
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return {"success": False, "error": "Authentication failed"}
            
    def _generate_token(self, user: Dict) -> str:
        """Generate JWT token for user"""
        payload = {
            "user_id": str(user["_id"]),
            "email": user["email"],
            "role": user["role"],
            "exp": datetime.utcnow() + timedelta(hours=self.jwt_expiration_hours)
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        
    def _verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
            
    def _verify_admin(self, token: str) -> bool:
        """Verify if token belongs to admin"""
        payload = self._verify_token(token)
        return payload and payload.get("role") == UserRole.ADMIN.value
        
    def _verify_user(self, token: str) -> Optional[Dict]:
        """Verify user token and return user"""
        payload = self._verify_token(token)
        if not payload:
            return None
            
        try:
            user = self.db.users.find_one({"_id": ObjectId(payload["user_id"])})
            return user
        except:
            return None
            
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA256"""
        salt = os.getenv("PASSWORD_SALT", "auraquant-2025")
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
        
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return self._hash_password(password) == password_hash
        
    def _sanitize_user(self, user: Dict) -> Dict:
        """Remove sensitive data from user object"""
        user = dict(user)
        user["_id"] = str(user["_id"])
        user.pop("password_hash", None)
        return user
        
    # =====================
    # System Monitoring (Admin Only)
    # =====================
    
    def get_system_stats(self, admin_token: str) -> Dict[str, Any]:
        """Get system statistics (Admin only)"""
        if not self._verify_admin(admin_token):
            return {"success": False, "error": "Unauthorized"}
            
        try:
            stats = {
                "users": {
                    "total": self.db.users.count_documents({}),
                    "active": self.db.users.count_documents({"is_active": True}),
                    "suspended": self.db.users.count_documents({"role": UserRole.SUSPENDED.value}),
                    "admins": self.db.users.count_documents({"role": UserRole.ADMIN.value})
                },
                "agents": {
                    "total": self.db.agents.count_documents({}),
                    "active": self.db.agents.count_documents({"status": "active"}),
                    "paused": self.db.agents.count_documents({"status": "paused"}),
                    "stopped": self.db.agents.count_documents({"status": "stopped"})
                },
                "agent_types": {}
            }
            
            # Count agents by type
            for agent_type in AgentType:
                count = self.db.agents.count_documents({"type": agent_type.value})
                stats["agent_types"][agent_type.value] = count
                
            return {
                "success": True,
                "statistics": stats
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def get_user_activity(self, admin_token: str, days: int = 7) -> Dict[str, Any]:
        """Get user activity report (Admin only)"""
        if not self._verify_admin(admin_token):
            return {"success": False, "error": "Unauthorized"}
            
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            activity = {
                "new_users": self.db.users.count_documents({
                    "created_at": {"$gte": cutoff_date}
                }),
                "active_users": self.db.users.count_documents({
                    "last_login": {"$gte": cutoff_date}
                }),
                "new_agents": self.db.agents.count_documents({
                    "created_at": {"$gte": cutoff_date}
                }),
                "active_agents": self.db.agents.count_documents({
                    "last_active": {"$gte": cutoff_date},
                    "status": "active"
                })
            }
            
            return {
                "success": True,
                "activity": activity,
                "period_days": days
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

# Global instance
admin_system = AdminManagementSystem()

if __name__ == "__main__":
    print("✅ Admin Management System initialized")
    print(f"   Default admin: {admin_system.default_admin_email}")