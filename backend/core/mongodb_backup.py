#!/usr/bin/env python3
"""
AuraQuant MongoDB Backup & Restore System
Engineer's Note: Automated backup to MongoDB Atlas with local fallback
Includes scheduled backups, compression, and point-in-time recovery
"""

import os
import json
import gzip
import shutil
import hashlib
import schedule
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import asyncio
import logging

# MongoDB imports
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
import gridfs
from bson import ObjectId

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BackupMetadata:
    """Backup metadata structure"""
    backup_id: str
    timestamp: datetime
    collections: List[str]
    document_count: int
    size_bytes: int
    compression_ratio: float
    backup_type: str  # full, incremental, differential
    location: str     # local, cloud, both
    checksum: str

class MongoDBBackupSystem:
    """
    Comprehensive MongoDB backup and restore system
    Handles automated backups to MongoDB Atlas and local storage
    """
    
    def __init__(self):
        """Initialize backup system"""
        # MongoDB connection
        self.mongo_uri = os.getenv("MONGO_URI", os.getenv("MONGODB_URI", ""))
        self.database_name = os.getenv("MONGODB_DATABASE", "auraquant")
        
        # Backup configuration
        self.backup_dir = Path(os.getenv("BACKUP_DIR", "D:\\New AuraQuant\\Backups"))
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Cloud backup bucket (MongoDB Atlas)
        self.cloud_backup_enabled = bool(self.mongo_uri)
        
        # Backup settings
        self.max_local_backups = 30  # Keep 30 days of backups
        self.compression_enabled = True
        self.encryption_enabled = False  # TODO: Implement encryption
        
        # Backup schedule
        self.schedule_enabled = True
        self.backup_times = ["02:00", "14:00"]  # Backup at 2 AM and 2 PM
        
        # Initialize connections
        self.client = None
        self.db = None
        self.gridfs_db = None
        
        self._initialize_connections()
        
    def _initialize_connections(self):
        """Initialize MongoDB connections"""
        if not self.mongo_uri:
            logger.warning("MongoDB URI not configured - backups will be local only")
            return
            
        try:
            # URL encode the password if needed
            if '@' in self.mongo_uri and '%40' not in self.mongo_uri:
                # Need to fix password encoding
                import urllib.parse
                parts = self.mongo_uri.split('@')
                if len(parts) > 1:
                    creds_part = parts[0].split('://')[-1]
                    if ':' in creds_part:
                        username, password = creds_part.rsplit(':', 1)
                        encoded_password = urllib.parse.quote_plus(password)
                        self.mongo_uri = self.mongo_uri.replace(f":{password}@", f":{encoded_password}@")
                        
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            
            # Initialize GridFS for large backups
            self.gridfs_db = gridfs.GridFS(self.client['auraquant_backups'])
            
            logger.info("✅ MongoDB Backup System connected to Atlas")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self.cloud_backup_enabled = False
            
    def backup_collection(self, collection_name: str) -> Dict[str, Any]:
        """
        Backup a single collection
        
        Args:
            collection_name: Name of collection to backup
            
        Returns:
            Backup statistics
        """
        try:
            if not self.db:
                logger.error("Database not connected")
                return {"success": False, "error": "Database not connected"}
                
            collection = self.db[collection_name]
            
            # Get all documents
            documents = list(collection.find())
            doc_count = len(documents)
            
            # Prepare backup data
            backup_data = {
                "collection": collection_name,
                "timestamp": datetime.now().isoformat(),
                "documents": documents,
                "count": doc_count
            }
            
            # Convert ObjectIds to strings for JSON serialization
            backup_json = json.dumps(backup_data, default=str)
            
            # Compress if enabled
            if self.compression_enabled:
                backup_bytes = backup_json.encode('utf-8')
                compressed = gzip.compress(backup_bytes)
                compression_ratio = len(backup_bytes) / len(compressed)
            else:
                compressed = backup_json.encode('utf-8')
                compression_ratio = 1.0
                
            # Calculate checksum
            checksum = hashlib.sha256(compressed).hexdigest()
            
            # Save locally
            backup_id = self._generate_backup_id()
            local_path = self._save_local_backup(backup_id, collection_name, compressed)
            
            # Save to cloud if enabled
            cloud_path = None
            if self.cloud_backup_enabled:
                cloud_path = self._save_cloud_backup(backup_id, collection_name, compressed)
                
            return {
                "success": True,
                "backup_id": backup_id,
                "collection": collection_name,
                "documents": doc_count,
                "size_bytes": len(compressed),
                "compression_ratio": compression_ratio,
                "checksum": checksum,
                "local_path": str(local_path),
                "cloud_path": cloud_path
            }
            
        except Exception as e:
            logger.error(f"Backup failed for {collection_name}: {e}")
            return {"success": False, "error": str(e)}
            
    def backup_database(self, backup_type: str = "full") -> Dict[str, Any]:
        """
        Backup entire database
        
        Args:
            backup_type: Type of backup (full, incremental, differential)
            
        Returns:
            Backup statistics
        """
        if not self.db:
            logger.error("Database not connected")
            return {"success": False, "error": "Database not connected"}
            
        backup_id = self._generate_backup_id()
        backup_stats = {
            "backup_id": backup_id,
            "timestamp": datetime.now().isoformat(),
            "type": backup_type,
            "collections": {},
            "total_documents": 0,
            "total_size": 0,
            "success": True
        }
        
        try:
            # Get all collections
            collections = self.db.list_collection_names()
            
            for collection_name in collections:
                # Skip system collections
                if collection_name.startswith('system.'):
                    continue
                    
                logger.info(f"Backing up collection: {collection_name}")
                
                # Backup collection
                result = self.backup_collection(collection_name)
                
                if result["success"]:
                    backup_stats["collections"][collection_name] = result
                    backup_stats["total_documents"] += result["documents"]
                    backup_stats["total_size"] += result["size_bytes"]
                else:
                    logger.error(f"Failed to backup {collection_name}: {result.get('error')}")
                    
            # Save backup metadata
            self._save_backup_metadata(backup_id, backup_stats)
            
            # Cleanup old backups
            self._cleanup_old_backups()
            
            logger.info(f"✅ Database backup complete: {backup_id}")
            logger.info(f"   Collections: {len(backup_stats['collections'])}")
            logger.info(f"   Documents: {backup_stats['total_documents']}")
            logger.info(f"   Size: {backup_stats['total_size'] / 1024 / 1024:.2f} MB")
            
            return backup_stats
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            backup_stats["success"] = False
            backup_stats["error"] = str(e)
            return backup_stats
            
    def restore_collection(self, backup_id: str, collection_name: str) -> bool:
        """
        Restore a single collection from backup
        
        Args:
            backup_id: Backup identifier
            collection_name: Name of collection to restore
            
        Returns:
            Success status
        """
        try:
            # Try to load from local first
            backup_data = self._load_local_backup(backup_id, collection_name)
            
            # If not found locally, try cloud
            if not backup_data and self.cloud_backup_enabled:
                backup_data = self._load_cloud_backup(backup_id, collection_name)
                
            if not backup_data:
                logger.error(f"Backup not found: {backup_id}/{collection_name}")
                return False
                
            # Parse backup data
            if isinstance(backup_data, bytes):
                if self.compression_enabled:
                    backup_data = gzip.decompress(backup_data)
                backup_json = backup_data.decode('utf-8')
            else:
                backup_json = backup_data
                
            backup = json.loads(backup_json)
            
            # Restore to database
            collection = self.db[collection_name]
            
            # Clear existing data (optional - could also merge)
            collection.delete_many({})
            
            # Insert documents
            if backup["documents"]:
                # Convert string IDs back to ObjectIds
                for doc in backup["documents"]:
                    if "_id" in doc and isinstance(doc["_id"], str):
                        doc["_id"] = ObjectId(doc["_id"])
                        
                collection.insert_many(backup["documents"])
                
            logger.info(f"✅ Restored {collection_name}: {backup['count']} documents")
            return True
            
        except Exception as e:
            logger.error(f"Restore failed for {collection_name}: {e}")
            return False
            
    def restore_database(self, backup_id: str) -> bool:
        """
        Restore entire database from backup
        
        Args:
            backup_id: Backup identifier
            
        Returns:
            Success status
        """
        try:
            # Load backup metadata
            metadata = self._load_backup_metadata(backup_id)
            
            if not metadata:
                logger.error(f"Backup metadata not found: {backup_id}")
                return False
                
            success = True
            restored_count = 0
            
            # Restore each collection
            for collection_name in metadata.get("collections", {}).keys():
                if self.restore_collection(backup_id, collection_name):
                    restored_count += 1
                else:
                    success = False
                    
            logger.info(f"✅ Database restore complete: {restored_count} collections")
            return success
            
        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            return False
            
    def list_backups(self, limit: int = 10) -> List[Dict]:
        """
        List available backups
        
        Args:
            limit: Maximum number of backups to return
            
        Returns:
            List of backup metadata
        """
        backups = []
        
        # List local backups
        metadata_dir = self.backup_dir / "metadata"
        if metadata_dir.exists():
            for metadata_file in sorted(metadata_dir.glob("*.json"), reverse=True)[:limit]:
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                        backups.append(metadata)
                except Exception as e:
                    logger.error(f"Failed to load metadata {metadata_file}: {e}")
                    
        return backups
        
    def schedule_backups(self):
        """Schedule automatic backups"""
        if not self.schedule_enabled:
            return
            
        # Schedule backup times
        for backup_time in self.backup_times:
            schedule.every().day.at(backup_time).do(self._scheduled_backup)
            
        # Start scheduler thread
        def run_scheduler():
            while self.schedule_enabled:
                schedule.run_pending()
                threading.Event().wait(60)  # Check every minute
                
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        logger.info(f"✅ Backup scheduler started: {self.backup_times}")
        
    def _scheduled_backup(self):
        """Execute scheduled backup"""
        logger.info("⏰ Starting scheduled backup...")
        result = self.backup_database()
        
        if result["success"]:
            logger.info(f"✅ Scheduled backup complete: {result['backup_id']}")
            
            # Send notification
            try:
                from .alert_system import alert_system, AlertPriority
                asyncio.run(alert_system.send_alert(
                    "Backup Complete",
                    f"Database backup successful: {result['total_documents']} documents",
                    priority=AlertPriority.LOW,
                    category="Backup",
                    data=result
                ))
            except:
                pass
        else:
            logger.error(f"❌ Scheduled backup failed: {result.get('error')}")
            
    def _save_local_backup(self, backup_id: str, collection_name: str, data: bytes) -> Path:
        """Save backup to local filesystem"""
        # Create backup directory structure
        backup_path = self.backup_dir / backup_id
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Save backup file
        file_ext = ".gz" if self.compression_enabled else ".json"
        file_path = backup_path / f"{collection_name}{file_ext}"
        
        with open(file_path, 'wb') as f:
            f.write(data)
            
        return file_path
        
    def _save_cloud_backup(self, backup_id: str, collection_name: str, data: bytes) -> str:
        """Save backup to MongoDB GridFS"""
        if not self.gridfs_db:
            return None
            
        try:
            # Store in GridFS
            file_id = self.gridfs_db.put(
                data,
                filename=f"{backup_id}/{collection_name}",
                backup_id=backup_id,
                collection=collection_name,
                timestamp=datetime.now()
            )
            
            return str(file_id)
            
        except Exception as e:
            logger.error(f"Failed to save cloud backup: {e}")
            return None
            
    def _load_local_backup(self, backup_id: str, collection_name: str) -> Optional[bytes]:
        """Load backup from local filesystem"""
        backup_path = self.backup_dir / backup_id
        
        # Try compressed first
        file_path = backup_path / f"{collection_name}.gz"
        if not file_path.exists():
            file_path = backup_path / f"{collection_name}.json"
            
        if file_path.exists():
            with open(file_path, 'rb') as f:
                return f.read()
                
        return None
        
    def _load_cloud_backup(self, backup_id: str, collection_name: str) -> Optional[bytes]:
        """Load backup from MongoDB GridFS"""
        if not self.gridfs_db:
            return None
            
        try:
            # Find file in GridFS
            file = self.gridfs_db.find_one({
                "filename": f"{backup_id}/{collection_name}"
            })
            
            if file:
                return file.read()
                
        except Exception as e:
            logger.error(f"Failed to load cloud backup: {e}")
            
        return None
        
    def _save_backup_metadata(self, backup_id: str, metadata: Dict):
        """Save backup metadata"""
        metadata_dir = self.backup_dir / "metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        metadata_file = metadata_dir / f"{backup_id}.json"
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
            
    def _load_backup_metadata(self, backup_id: str) -> Optional[Dict]:
        """Load backup metadata"""
        metadata_file = self.backup_dir / "metadata" / f"{backup_id}.json"
        
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                return json.load(f)
                
        return None
        
    def _cleanup_old_backups(self):
        """Remove old backups beyond retention period"""
        cutoff_date = datetime.now() - timedelta(days=self.max_local_backups)
        
        # Clean local backups
        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir() and backup_dir.name != "metadata":
                try:
                    # Check backup date from directory name
                    backup_date_str = backup_dir.name.split('_')[1]
                    backup_date = datetime.strptime(backup_date_str, '%Y%m%d')
                    
                    if backup_date < cutoff_date:
                        shutil.rmtree(backup_dir)
                        logger.info(f"Cleaned up old backup: {backup_dir.name}")
                        
                except Exception as e:
                    logger.error(f"Failed to clean up {backup_dir}: {e}")
                    
    def _generate_backup_id(self) -> str:
        """Generate unique backup ID"""
        return f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def get_backup_statistics(self) -> Dict[str, Any]:
        """Get backup system statistics"""
        stats = {
            "cloud_enabled": self.cloud_backup_enabled,
            "compression_enabled": self.compression_enabled,
            "schedule_enabled": self.schedule_enabled,
            "backup_times": self.backup_times,
            "retention_days": self.max_local_backups,
            "backup_directory": str(self.backup_dir)
        }
        
        # Count backups
        backups = self.list_backups(limit=100)
        stats["total_backups"] = len(backups)
        
        if backups:
            # Calculate total size
            total_size = sum(b.get("total_size", 0) for b in backups)
            stats["total_size_mb"] = total_size / 1024 / 1024
            
            # Latest backup
            stats["latest_backup"] = backups[0].get("timestamp")
            
        return stats

# Global backup system instance
backup_system = MongoDBBackupSystem()

# Convenience functions

def backup_now() -> Dict:
    """Execute immediate backup"""
    return backup_system.backup_database()

def restore_latest() -> bool:
    """Restore from latest backup"""
    backups = backup_system.list_backups(limit=1)
    if backups:
        return backup_system.restore_database(backups[0]["backup_id"])
    return False

def enable_auto_backup():
    """Enable automatic scheduled backups"""
    backup_system.schedule_backups()

if __name__ == "__main__":
    # Test backup system
    print("🔄 Testing MongoDB Backup System...")
    
    # Test backup
    result = backup_now()
    
    if result["success"]:
        print(f"✅ Backup successful!")
        print(f"   Backup ID: {result['backup_id']}")
        print(f"   Collections: {len(result['collections'])}")
        print(f"   Documents: {result['total_documents']}")
        print(f"   Size: {result['total_size'] / 1024:.2f} KB")
    else:
        print(f"❌ Backup failed: {result.get('error')}")
        
    # Show statistics
    stats = backup_system.get_backup_statistics()
    print("\n📊 Backup System Statistics:")
    print(json.dumps(stats, indent=2))
    
    print("\n✅ Backup System Test Complete")