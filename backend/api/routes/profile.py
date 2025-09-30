"""
User Profile Routes
Handles user profile management and preferences
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import db_config
from core.auth import get_current_user

router = APIRouter()

class BrokerConfig(BaseModel):
    name: str
    api_key: str
    api_secret: str = ""
    account_id: str = ""
    enabled: bool = True

class RiskPreferences(BaseModel):
    max_drawdown: float = 0.20  # 20%
    target_growth: float = 0.15  # 15% annual
    trading_mode: str = "conservative"  # conservative, moderate, aggressive
    max_position_size: float = 0.1  # 10% per position
    stop_loss: float = 0.02  # 2% stop loss
    take_profit: float = 0.05  # 5% take profit

class NotificationSettings(BaseModel):
    telegram: Dict[str, Any] = {}
    discord: Dict[str, Any] = {}
    email: Dict[str, Any] = {}
    sms: Dict[str, Any] = {}

class UserProfile(BaseModel):
    username: str
    email: str
    brokers: List[BrokerConfig] = []
    risk_preferences: RiskPreferences = RiskPreferences()
    notifications: NotificationSettings = NotificationSettings()
    trading_experience: str = "beginner"  # beginner, intermediate, advanced, expert
    preferred_assets: List[str] = ["BTC", "ETH"]
    auto_trade_enabled: bool = False

@router.get("/get")
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user's profile"""
    try:
        client = AsyncIOMotorClient(db_config.mongodb_uri)
        db = client[db_config.database_name]
        
        # Find user profile
        profile = await db.user_profiles.find_one({"user_id": current_user["user_id"]})
        
        if not profile:
            # Create default profile if doesn't exist
            default_profile = {
                "user_id": current_user["user_id"],
                "username": current_user.get("username", ""),
                "email": current_user.get("email", ""),
                "brokers": [],
                "risk_preferences": RiskPreferences().dict(),
                "notifications": NotificationSettings().dict(),
                "trading_experience": "beginner",
                "preferred_assets": ["BTC", "ETH"],
                "auto_trade_enabled": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await db.user_profiles.insert_one(default_profile)
            profile = default_profile
        
        # Remove MongoDB _id field
        if "_id" in profile:
            profile["_id"] = str(profile["_id"])
        
        return {"success": True, "profile": profile}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        client.close()

@router.post("/update")
async def update_user_profile(
    profile: UserProfile,
    current_user: dict = Depends(get_current_user)
):
    """Update user's profile"""
    try:
        client = AsyncIOMotorClient(db_config.mongodb_uri)
        db = client[db_config.database_name]
        
        # Prepare update data
        update_data = profile.dict()
        update_data["user_id"] = current_user["user_id"]
        update_data["updated_at"] = datetime.utcnow()
        
        # Update or create profile
        result = await db.user_profiles.update_one(
            {"user_id": current_user["user_id"]},
            {"$set": update_data},
            upsert=True
        )
        
        # Log profile update
        await db.system_logs.insert_one({
            "user_id": current_user["user_id"],
            "action": "profile_updated",
            "timestamp": datetime.utcnow(),
            "changes": update_data
        })
        
        return {
            "success": True,
            "message": "Profile updated successfully",
            "modified": result.modified_count > 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        client.close()

@router.post("/brokers/add")
async def add_broker(
    broker: BrokerConfig,
    current_user: dict = Depends(get_current_user)
):
    """Add a new broker configuration"""
    try:
        client = AsyncIOMotorClient(db_config.mongodb_uri)
        db = client[db_config.database_name]
        
        # Add broker to user profile
        result = await db.user_profiles.update_one(
            {"user_id": current_user["user_id"]},
            {
                "$push": {"brokers": broker.dict()},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return {
            "success": True,
            "message": f"Broker {broker.name} added successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        client.close()

@router.delete("/brokers/remove/{broker_name}")
async def remove_broker(
    broker_name: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove a broker configuration"""
    try:
        client = AsyncIOMotorClient(db_config.mongodb_uri)
        db = client[db_config.database_name]
        
        # Remove broker from user profile
        result = await db.user_profiles.update_one(
            {"user_id": current_user["user_id"]},
            {
                "$pull": {"brokers": {"name": broker_name}},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return {
            "success": True,
            "message": f"Broker {broker_name} removed successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        client.close()

@router.post("/preferences/risk")
async def update_risk_preferences(
    preferences: RiskPreferences,
    current_user: dict = Depends(get_current_user)
):
    """Update risk preferences"""
    try:
        client = AsyncIOMotorClient(db_config.mongodb_uri)
        db = client[db_config.database_name]
        
        result = await db.user_profiles.update_one(
            {"user_id": current_user["user_id"]},
            {
                "$set": {
                    "risk_preferences": preferences.dict(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "success": True,
            "message": "Risk preferences updated successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        client.close()

@router.post("/preferences/notifications")
async def update_notification_settings(
    settings: NotificationSettings,
    current_user: dict = Depends(get_current_user)
):
    """Update notification settings"""
    try:
        client = AsyncIOMotorClient(db_config.mongodb_uri)
        db = client[db_config.database_name]
        
        result = await db.user_profiles.update_one(
            {"user_id": current_user["user_id"]},
            {
                "$set": {
                    "notifications": settings.dict(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "success": True,
            "message": "Notification settings updated successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        client.close()