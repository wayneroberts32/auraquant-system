"""
AuraQuant Cloud Migration Script
Migrates all local memories to MongoDB Cloud for production deployment
Professor's Note: This ensures no learning is lost during deployment
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
import argparse
from typing import Dict, Any, Optional

# Add brain modules to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory_manager import LocalMemoryStorage, CloudMigrationManager
from quantum_brain_local import QuantumBrainLocal


class CloudMigrationOrchestrator:
    """
    Orchestrates the complete migration of AuraQuant brain to cloud
    """
    
    def __init__(self, memory_path: str = r"D:\New AuraQuant\New_Synthetic_System_AuraQuant_Backup_2025\Memory"):
        """
        Initialize migration orchestrator
        
        Args:
            memory_path: Path to local memory storage
        """
        self.memory_path = Path(memory_path)
        self.memory_storage = LocalMemoryStorage(memory_path)
        self.brain = QuantumBrainLocal(memory_path)
        
        # Migration statistics
        self.migration_stats = {
            'start_time': None,
            'end_time': None,
            'memories_migrated': 0,
            'strategies_migrated': 0,
            'neural_weights_migrated': 0,
            'quantum_states_migrated': 0,
            'total_size_mb': 0,
            'errors': []
        }
        
    def validate_mongodb_uri(self, uri: str) -> bool:
        """
        Validate MongoDB URI format
        
        Args:
            uri: MongoDB connection string
            
        Returns:
            True if valid, False otherwise
        """
        # Basic validation
        valid_prefixes = ['mongodb://', 'mongodb+srv://']
        return any(uri.startswith(prefix) for prefix in valid_prefixes)
        
    async def pre_migration_checks(self) -> Dict[str, Any]:
        """
        Perform pre-migration checks
        
        Returns:
            Check results
        """
        print("\n🔍 PERFORMING PRE-MIGRATION CHECKS...")
        
        checks = {
            'memory_path_exists': self.memory_path.exists(),
            'has_memories': False,
            'has_neural_weights': False,
            'has_quantum_states': False,
            'total_files': 0,
            'total_size_mb': 0,
            'backup_created': False
        }
        
        if checks['memory_path_exists']:
            # Count memories
            memory_files = list(self.memory_path.rglob('*.json'))
            checks['total_files'] = len(memory_files)
            checks['has_memories'] = len(memory_files) > 0
            
            # Check for neural weights
            weights_dir = self.memory_path / 'neural_weights'
            if weights_dir.exists():
                weight_files = list(weights_dir.glob('*.pkl'))
                checks['has_neural_weights'] = len(weight_files) > 0
                
            # Check for quantum states
            quantum_dir = self.memory_path / 'quantum_states'
            if quantum_dir.exists():
                quantum_files = list(quantum_dir.glob('*.npz'))
                checks['has_quantum_states'] = len(quantum_files) > 0
                
            # Calculate total size
            total_size = 0
            for file_path in self.memory_path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            checks['total_size_mb'] = total_size / (1024 * 1024)
            
        # Display check results
        print("\n✅ Pre-Migration Check Results:")
        for key, value in checks.items():
            status = "✓" if value else "✗"
            print(f"   {status} {key}: {value}")
            
        return checks
        
    async def create_backup(self) -> str:
        """
        Create a backup before migration
        
        Returns:
            Backup path
        """
        print("\n💾 CREATING PRE-MIGRATION BACKUP...")
        
        backup_path = self.memory_storage.create_backup(compress=True)
        print(f"   Backup saved: {backup_path}")
        
        return backup_path
        
    async def migrate_memories(self, mongodb_uri: str) -> Dict[str, Any]:
        """
        Migrate all memories to MongoDB cloud
        
        Args:
            mongodb_uri: MongoDB connection string
            
        Returns:
            Migration results
        """
        print("\n☁️ STARTING CLOUD MIGRATION...")
        print(f"   Target: MongoDB Cloud")
        
        self.migration_stats['start_time'] = datetime.now()
        
        # Prepare for migration
        export_path = self.memory_storage.prepare_for_cloud_migration()
        
        # Initialize cloud migration manager
        migration_manager = CloudMigrationManager(
            self.memory_storage,
            mongodb_uri
        )
        
        # Perform migration
        try:
            migration_result = await migration_manager.migrate_to_cloud(export_path)
            
            # Update statistics
            self.migration_stats['memories_migrated'] = migration_result.get('migrated', 0)
            self.migration_stats['errors'] = migration_result.get('errors', [])
            
        except Exception as e:
            print(f"❌ Migration error: {e}")
            self.migration_stats['errors'].append(str(e))
            return self.migration_stats
            
        self.migration_stats['end_time'] = datetime.now()
        
        return self.migration_stats
        
    async def verify_migration(self, mongodb_uri: str) -> bool:
        """
        Verify migration success
        
        Args:
            mongodb_uri: MongoDB connection string
            
        Returns:
            True if verification successful
        """
        print("\n🔍 VERIFYING MIGRATION...")
        
        try:
            from pymongo import MongoClient
            
            client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
            db = client['auraquant_brain']
            
            # Check collections
            collections = db.list_collection_names()
            print(f"   Collections in cloud: {len(collections)}")
            
            # Check document counts
            for collection_name in collections:
                count = db[collection_name].count_documents({})
                print(f"   {collection_name}: {count} documents")
                
            client.close()
            return True
            
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False
            
    async def post_migration_cleanup(self, keep_local: bool = True):
        """
        Clean up after successful migration
        
        Args:
            keep_local: Whether to keep local copies
        """
        print("\n🧹 POST-MIGRATION CLEANUP...")
        
        if not keep_local:
            # Clean up old memories that are synced
            self.memory_storage.cleanup_old_memories(days=0)
            print("   ✓ Cleaned up synced memories")
        else:
            print("   ✓ Keeping local copies as backup")
            
        # Update brain configuration
        config_file = self.memory_path / 'migration_complete.json'
        config = {
            'migration_date': datetime.now().isoformat(),
            'memories_migrated': self.migration_stats['memories_migrated'],
            'cloud_enabled': True,
            'local_backup': keep_local
        }
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
            
        print(f"   ✓ Configuration updated: {config_file}")
        
    async def full_migration_pipeline(self, mongodb_uri: str, keep_local: bool = True):
        """
        Execute complete migration pipeline
        
        Args:
            mongodb_uri: MongoDB connection string
            keep_local: Whether to keep local copies after migration
        """
        print("""
        ╔══════════════════════════════════════════════════════════╗
        ║           AuraQuant Cloud Migration Pipeline              ║
        ║         Migrating Brain Memories to MongoDB Cloud         ║
        ╚══════════════════════════════════════════════════════════╝
        """)
        
        # Step 1: Validate URI
        if not self.validate_mongodb_uri(mongodb_uri):
            print("❌ Invalid MongoDB URI format")
            print("   Expected format: mongodb+srv://username:password@cluster.mongodb.net/")
            return
            
        # Step 2: Pre-migration checks
        checks = await self.pre_migration_checks()
        
        if not checks['has_memories']:
            print("\n⚠️ No memories found to migrate")
            return
            
        print(f"\n📊 Migration Summary:")
        print(f"   Files to migrate: {checks['total_files']}")
        print(f"   Total size: {checks['total_size_mb']:.2f} MB")
        
        # Step 3: Create backup
        backup_path = await self.create_backup()
        
        # Step 4: Confirm migration
        print("\n" + "="*60)
        print("⚠️  MIGRATION CONFIRMATION")
        print(f"   Source: {self.memory_path}")
        print(f"   Destination: MongoDB Cloud")
        print(f"   Backup: {backup_path}")
        print("="*60)
        
        confirm = input("\n🔄 Proceed with migration? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Migration cancelled")
            return
            
        # Step 5: Perform migration
        migration_stats = await self.migrate_memories(mongodb_uri)
        
        # Step 6: Verify migration
        verified = await self.verify_migration(mongodb_uri)
        
        if verified:
            print("\n✅ MIGRATION SUCCESSFUL!")
            
            # Step 7: Post-migration cleanup
            await self.post_migration_cleanup(keep_local)
            
            # Display final statistics
            duration = (migration_stats['end_time'] - migration_stats['start_time']).total_seconds()
            
            print(f"\n📊 MIGRATION STATISTICS:")
            print(f"   Duration: {duration:.2f} seconds")
            print(f"   Memories migrated: {migration_stats['memories_migrated']}")
            print(f"   Errors: {len(migration_stats.get('errors', []))}")
            print(f"   Local backup: {'Kept' if keep_local else 'Removed'}")
            
        else:
            print("\n❌ MIGRATION VERIFICATION FAILED")
            print("   Please check your MongoDB connection and try again")


def get_mongodb_uri() -> str:
    """
    Get MongoDB URI from user or environment
    
    Returns:
        MongoDB connection string
    """
    # Try environment variable first
    uri = os.getenv('MONGODB_CLOUD_URI')
    
    if uri:
        print(f"✓ Using MongoDB URI from environment variable")
        return uri
        
    # Provide options
    print("\n🔗 MongoDB Connection Options:")
    print("1. MongoDB Atlas (Cloud)")
    print("2. Local MongoDB")
    print("3. Custom URI")
    
    choice = input("\nSelect option (1-3): ")
    
    if choice == '1':
        print("\n📝 MongoDB Atlas Setup:")
        print("   1. Go to https://cloud.mongodb.com")
        print("   2. Create a free cluster")
        print("   3. Get your connection string")
        print("   4. Replace <password> with your password")
        
        uri = input("\nEnter MongoDB Atlas URI: ")
        
    elif choice == '2':
        uri = "mongodb://localhost:27017/"
        print(f"✓ Using local MongoDB: {uri}")
        
    else:
        uri = input("\nEnter custom MongoDB URI: ")
        
    return uri


async def main():
    """Main execution function"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Migrate AuraQuant memories to MongoDB Cloud')
    parser.add_argument('--uri', type=str, help='MongoDB connection URI')
    parser.add_argument('--keep-local', action='store_true', default=True,
                       help='Keep local copies after migration')
    parser.add_argument('--no-backup', action='store_true',
                       help='Skip backup creation')
    
    args = parser.parse_args()
    
    # Get MongoDB URI
    if args.uri:
        mongodb_uri = args.uri
    else:
        mongodb_uri = get_mongodb_uri()
        
    if not mongodb_uri:
        print("❌ No MongoDB URI provided")
        return
        
    # Initialize orchestrator
    orchestrator = CloudMigrationOrchestrator()
    
    # Run migration
    await orchestrator.full_migration_pipeline(
        mongodb_uri=mongodb_uri,
        keep_local=args.keep_local
    )
    
    print("\n🎉 Cloud migration process complete!")
    print("📝 Next steps:")
    print("   1. Verify data in MongoDB Atlas dashboard")
    print("   2. Update application configuration to use cloud connection")
    print("   3. Test the system with cloud data")
    print("   4. Enable automatic backups in MongoDB Atlas")


if __name__ == "__main__":
    asyncio.run(main())