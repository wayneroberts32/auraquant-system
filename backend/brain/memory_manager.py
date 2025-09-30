"""
AuraQuant Memory Manager - Local File Storage with MongoDB Cloud Migration
Professor's Note: This implements a hybrid memory system that stores locally during development
and seamlessly migrates to MongoDB cloud during production deployment
"""

import os
import json
import pickle
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import shutil
import zipfile
from dataclasses import dataclass, asdict
import asyncio
import aiofiles
import numpy as np

# MongoDB imports (optional for cloud deployment)
try:
    from pymongo import MongoClient
    import motor.motor_asyncio
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    print("⚠️ MongoDB not installed. Running in local-only mode.")

@dataclass
class MemoryUnit:
    """Represents a single memory unit"""
    memory_id: str
    timestamp: datetime
    memory_type: str  # 'trade', 'pattern', 'evolution', 'performance'
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    checksum: str

class LocalMemoryStorage:
    """
    Manages local file-based memory storage
    Stores memories in structured directories for easy cloud migration
    """
    
    def __init__(self, base_path: str = r"D:\New AuraQuant\New_Synthetic_System_AuraQuant_Backup_2025\Memory"):
        """
        Initialize local memory storage
        
        Args:
            base_path: Base directory for memory storage
        """
        self.base_path = Path(base_path)
        self.db_path = self.base_path / "memory.db"
        
        # Create directory structure
        self._setup_directories()
        
        # Initialize SQLite for indexing
        self._init_sqlite()
        
        # Memory statistics
        self.stats = {
            'total_memories': 0,
            'memory_types': {},
            'last_backup': None,
            'storage_size_mb': 0
        }
        
        self._update_stats()
        
    def _setup_directories(self):
        """Create organized directory structure for memories"""
        directories = [
            'trades',           # Trading decisions and outcomes
            'patterns',         # Detected market patterns
            'evolution',        # Brain evolution snapshots
            'performance',      # Performance metrics
            'neural_weights',   # Neural network weights
            'quantum_states',   # Quantum state vectors
            'backups',         # Periodic backups
            'temp',            # Temporary files
            'exports'          # Ready for cloud migration
        ]
        
        for dir_name in directories:
            dir_path = self.base_path / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
            
        # Create README
        readme_path = self.base_path / "README.md"
        if not readme_path.exists():
            with open(readme_path, 'w') as f:
                f.write("""# AuraQuant Memory Storage

## Directory Structure
- **trades/**: Trading decisions and outcomes
- **patterns/**: Detected market patterns  
- **evolution/**: Brain evolution snapshots
- **performance/**: Performance metrics
- **neural_weights/**: Saved neural network states
- **quantum_states/**: Quantum state vectors
- **backups/**: Periodic full backups
- **temp/**: Temporary processing files
- **exports/**: Files ready for cloud migration

## Migration to Cloud
When deploying, all memories will be automatically migrated to MongoDB cloud.
Run: `python migrate_to_cloud.py` to initiate migration.

## File Formats
- JSON: Human-readable memory data
- PKL: Binary neural weights
- SQLite: Local index database
""")
        
        print(f"📁 Memory directories created at: {self.base_path}")
        
    def _init_sqlite(self):
        """Initialize SQLite database for memory indexing"""
        self.conn = sqlite3.connect(str(self.db_path))
        cursor = self.conn.cursor()
        
        # Create memories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                memory_id TEXT PRIMARY KEY,
                timestamp DATETIME,
                memory_type TEXT,
                file_path TEXT,
                data_json TEXT,
                metadata_json TEXT,
                checksum TEXT,
                synced_to_cloud BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_type ON memories(memory_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_synced ON memories(synced_to_cloud)')
        
        # Create patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patterns (
                pattern_id TEXT PRIMARY KEY,
                pattern_type TEXT,
                symbol TEXT,
                timestamp DATETIME,
                confidence REAL,
                outcome REAL,
                file_path TEXT
            )
        ''')
        
        # Create evolution table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS evolution (
                generation INTEGER PRIMARY KEY,
                timestamp DATETIME,
                fitness_score REAL,
                consciousness_level REAL,
                mutations_applied TEXT,
                weights_file TEXT
            )
        ''')
        
        self.conn.commit()
        
    def save_memory(self, memory_type: str, data: Dict[str, Any], 
                   metadata: Optional[Dict] = None) -> str:
        """
        Save a memory to local storage
        
        Args:
            memory_type: Type of memory (trade, pattern, evolution, performance)
            data: Memory data to save
            metadata: Optional metadata
            
        Returns:
            memory_id: Unique identifier for the memory
        """
        # Generate memory ID
        memory_id = self._generate_memory_id(memory_type, data)
        timestamp = datetime.now()
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        metadata['saved_at'] = timestamp.isoformat()
        metadata['memory_type'] = memory_type
        
        # Calculate checksum
        checksum = self._calculate_checksum(data)
        
        # Determine file path
        date_dir = timestamp.strftime("%Y-%m-%d")
        file_dir = self.base_path / memory_type / date_dir
        file_dir.mkdir(parents=True, exist_ok=True)
        
        # Save as JSON
        file_path = file_dir / f"{memory_id}.json"
        memory_data = {
            'memory_id': memory_id,
            'timestamp': timestamp.isoformat(),
            'memory_type': memory_type,
            'data': data,
            'metadata': metadata,
            'checksum': checksum
        }
        
        with open(file_path, 'w') as f:
            json.dump(memory_data, f, indent=2, default=str)
            
        # Update SQLite index
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO memories 
            (memory_id, timestamp, memory_type, file_path, data_json, metadata_json, checksum)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            memory_id,
            timestamp,
            memory_type,
            str(file_path),
            json.dumps(data, default=str),
            json.dumps(metadata, default=str),
            checksum
        ))
        self.conn.commit()
        
        # Update stats
        self._update_stats()
        
        return memory_id
        
    def save_neural_weights(self, generation: int, weights: Dict[str, Any]) -> str:
        """
        Save neural network weights
        
        Args:
            generation: Evolution generation number
            weights: Dictionary of neural network weights
            
        Returns:
            file_path: Path to saved weights file
        """
        timestamp = datetime.now()
        
        # Create file path
        file_name = f"weights_gen_{generation}_{timestamp.strftime('%Y%m%d_%H%M%S')}.pkl"
        file_path = self.base_path / "neural_weights" / file_name
        
        # Save weights
        with open(file_path, 'wb') as f:
            pickle.dump({
                'generation': generation,
                'timestamp': timestamp,
                'weights': weights
            }, f)
            
        # Also save metadata as JSON
        meta_path = file_path.with_suffix('.json')
        with open(meta_path, 'w') as f:
            json.dump({
                'generation': generation,
                'timestamp': timestamp.isoformat(),
                'file_path': str(file_path),
                'size_bytes': file_path.stat().st_size
            }, f, indent=2)
            
        return str(file_path)
        
    def save_quantum_state(self, state_vector: np.ndarray, 
                          consciousness_level: float) -> str:
        """
        Save quantum state vector
        
        Args:
            state_vector: Quantum state vector (numpy array)
            consciousness_level: Current consciousness level
            
        Returns:
            file_path: Path to saved state file
        """
        timestamp = datetime.now()
        
        # Create file path
        file_name = f"quantum_state_{timestamp.strftime('%Y%m%d_%H%M%S')}.npz"
        file_path = self.base_path / "quantum_states" / file_name
        
        # Save state
        np.savez_compressed(
            file_path,
            state_vector=state_vector,
            consciousness_level=consciousness_level,
            timestamp=timestamp.isoformat()
        )
        
        return str(file_path)
        
    def load_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a memory by ID
        
        Args:
            memory_id: Unique memory identifier
            
        Returns:
            Memory data or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT file_path FROM memories WHERE memory_id = ?',
            (memory_id,)
        )
        result = cursor.fetchone()
        
        if result:
            file_path = Path(result[0])
            if file_path.exists():
                with open(file_path, 'r') as f:
                    return json.load(f)
        return None
        
    def query_memories(self, memory_type: Optional[str] = None,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None,
                       limit: int = 100) -> List[Dict[str, Any]]:
        """
        Query memories based on criteria
        
        Args:
            memory_type: Filter by memory type
            start_date: Filter by start date
            end_date: Filter by end date  
            limit: Maximum number of results
            
        Returns:
            List of matching memories
        """
        query = 'SELECT memory_id, timestamp, memory_type, data_json FROM memories WHERE 1=1'
        params = []
        
        if memory_type:
            query += ' AND memory_type = ?'
            params.append(memory_type)
            
        if start_date:
            query += ' AND timestamp >= ?'
            params.append(start_date)
            
        if end_date:
            query += ' AND timestamp <= ?'
            params.append(end_date)
            
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        
        memories = []
        for row in cursor.fetchall():
            memories.append({
                'memory_id': row[0],
                'timestamp': row[1],
                'memory_type': row[2],
                'data': json.loads(row[3])
            })
            
        return memories
        
    def create_backup(self, compress: bool = True) -> str:
        """
        Create a full backup of all memories
        
        Args:
            compress: Whether to compress the backup
            
        Returns:
            backup_path: Path to backup file
        """
        timestamp = datetime.now()
        backup_name = f"memory_backup_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        backup_dir = self.base_path / "backups" / backup_name
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy all memory directories
        for dir_name in ['trades', 'patterns', 'evolution', 'performance', 
                        'neural_weights', 'quantum_states']:
            src = self.base_path / dir_name
            if src.exists():
                dst = backup_dir / dir_name
                shutil.copytree(src, dst, dirs_exist_ok=True)
                
        # Copy SQLite database
        shutil.copy2(self.db_path, backup_dir / "memory.db")
        
        # Create backup metadata
        metadata = {
            'timestamp': timestamp.isoformat(),
            'total_memories': self.stats['total_memories'],
            'memory_types': self.stats['memory_types'],
            'storage_size_mb': self.stats['storage_size_mb']
        }
        
        with open(backup_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
            
        # Compress if requested
        if compress:
            zip_path = backup_dir.with_suffix('.zip')
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(backup_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(backup_dir)
                        zipf.write(file_path, arcname)
                        
            # Remove uncompressed backup
            shutil.rmtree(backup_dir)
            
            print(f"✅ Backup created: {zip_path}")
            return str(zip_path)
        else:
            print(f"✅ Backup created: {backup_dir}")
            return str(backup_dir)
            
    def prepare_for_cloud_migration(self) -> str:
        """
        Prepare memories for cloud migration
        
        Returns:
            export_path: Path to export directory
        """
        timestamp = datetime.now()
        export_name = f"cloud_export_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        export_dir = self.base_path / "exports" / export_name
        export_dir.mkdir(parents=True, exist_ok=True)
        
        # Export memories as JSON chunks
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM memories WHERE synced_to_cloud = 0')
        total_unsynced = cursor.fetchone()[0]
        
        print(f"📤 Preparing {total_unsynced} memories for cloud migration...")
        
        # Export in chunks of 1000
        chunk_size = 1000
        chunk_num = 0
        
        cursor.execute('''
            SELECT memory_id, timestamp, memory_type, data_json, metadata_json, checksum
            FROM memories WHERE synced_to_cloud = 0
            ORDER BY timestamp
        ''')
        
        while True:
            rows = cursor.fetchmany(chunk_size)
            if not rows:
                break
                
            chunk_data = []
            for row in rows:
                chunk_data.append({
                    'memory_id': row[0],
                    'timestamp': row[1],
                    'memory_type': row[2],
                    'data': json.loads(row[3]),
                    'metadata': json.loads(row[4]),
                    'checksum': row[5]
                })
                
            # Save chunk
            chunk_file = export_dir / f"chunk_{chunk_num:04d}.json"
            with open(chunk_file, 'w') as f:
                json.dump(chunk_data, f, indent=2, default=str)
                
            chunk_num += 1
            
        # Export neural weights
        weights_dir = self.base_path / "neural_weights"
        if weights_dir.exists():
            export_weights = export_dir / "neural_weights"
            shutil.copytree(weights_dir, export_weights, dirs_exist_ok=True)
            
        # Export quantum states
        quantum_dir = self.base_path / "quantum_states"
        if quantum_dir.exists():
            export_quantum = export_dir / "quantum_states"
            shutil.copytree(quantum_dir, export_quantum, dirs_exist_ok=True)
            
        # Create migration manifest
        manifest = {
            'export_timestamp': timestamp.isoformat(),
            'total_memories': total_unsynced,
            'chunks': chunk_num,
            'chunk_size': chunk_size,
            'includes_weights': weights_dir.exists(),
            'includes_quantum': quantum_dir.exists()
        }
        
        with open(export_dir / "manifest.json", 'w') as f:
            json.dump(manifest, f, indent=2)
            
        print(f"✅ Export prepared: {export_dir}")
        print(f"   Total chunks: {chunk_num}")
        print(f"   Ready for cloud migration")
        
        return str(export_dir)
        
    def _generate_memory_id(self, memory_type: str, data: Dict) -> str:
        """Generate unique memory ID"""
        content = f"{memory_type}_{json.dumps(data, sort_keys=True)}_{datetime.now().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
        
    def _calculate_checksum(self, data: Dict) -> str:
        """Calculate data checksum for integrity verification"""
        content = json.dumps(data, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()
        
    def _update_stats(self):
        """Update memory statistics"""
        cursor = self.conn.cursor()
        
        # Total memories
        cursor.execute('SELECT COUNT(*) FROM memories')
        self.stats['total_memories'] = cursor.fetchone()[0]
        
        # Memories by type
        cursor.execute('SELECT memory_type, COUNT(*) FROM memories GROUP BY memory_type')
        self.stats['memory_types'] = dict(cursor.fetchall())
        
        # Calculate storage size
        total_size = 0
        for path in self.base_path.rglob('*'):
            if path.is_file():
                total_size += path.stat().st_size
        self.stats['storage_size_mb'] = total_size / (1024 * 1024)
        
    def get_stats(self) -> Dict[str, Any]:
        """Get memory storage statistics"""
        self._update_stats()
        return self.stats
        
    def cleanup_old_memories(self, days: int = 30):
        """
        Clean up old memories to save space
        
        Args:
            days: Remove memories older than this many days
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT file_path FROM memories 
            WHERE timestamp < ? AND synced_to_cloud = 1
        ''', (cutoff_date,))
        
        removed_count = 0
        for row in cursor.fetchall():
            file_path = Path(row[0])
            if file_path.exists():
                file_path.unlink()
                removed_count += 1
                
        # Remove from database
        cursor.execute('''
            DELETE FROM memories 
            WHERE timestamp < ? AND synced_to_cloud = 1
        ''', (cutoff_date,))
        self.conn.commit()
        
        print(f"🧹 Cleaned up {removed_count} old memories")
        self._update_stats()


class CloudMigrationManager:
    """
    Manages migration of local memories to MongoDB cloud
    """
    
    def __init__(self, local_storage: LocalMemoryStorage,
                 mongodb_uri: Optional[str] = None):
        """
        Initialize cloud migration manager
        
        Args:
            local_storage: Local memory storage instance
            mongodb_uri: MongoDB cloud connection string
        """
        self.local_storage = local_storage
        self.mongodb_uri = mongodb_uri or os.getenv('MONGODB_CLOUD_URI')
        
        if MONGODB_AVAILABLE and self.mongodb_uri:
            try:
                self.mongo_client = MongoClient(self.mongodb_uri)
                self.db = self.mongo_client['auraquant_brain']
                print("☁️ Connected to MongoDB Cloud")
            except Exception as e:
                print(f"⚠️ Could not connect to MongoDB Cloud: {e}")
                self.mongo_client = None
        else:
            self.mongo_client = None
            
    async def migrate_to_cloud(self, export_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Migrate local memories to MongoDB cloud
        
        Args:
            export_dir: Directory containing exported memories
            
        Returns:
            Migration statistics
        """
        if not self.mongo_client:
            return {'error': 'MongoDB cloud connection not available'}
            
        # Prepare export if not provided
        if not export_dir:
            export_dir = self.local_storage.prepare_for_cloud_migration()
            
        export_path = Path(export_dir)
        
        # Read manifest
        with open(export_path / "manifest.json", 'r') as f:
            manifest = json.load(f)
            
        print(f"☁️ Starting cloud migration...")
        print(f"   Total memories: {manifest['total_memories']}")
        print(f"   Chunks to upload: {manifest['chunks']}")
        
        stats = {
            'started_at': datetime.now().isoformat(),
            'total_memories': manifest['total_memories'],
            'migrated': 0,
            'failed': 0,
            'chunks_processed': 0
        }
        
        # Process memory chunks
        for chunk_file in sorted(export_path.glob("chunk_*.json")):
            with open(chunk_file, 'r') as f:
                chunk_data = json.load(f)
                
            for memory in chunk_data:
                try:
                    # Insert into appropriate collection
                    collection_name = f"memories_{memory['memory_type']}"
                    collection = self.db[collection_name]
                    
                    # Convert timestamp strings back to datetime
                    if isinstance(memory['timestamp'], str):
                        memory['timestamp'] = datetime.fromisoformat(memory['timestamp'])
                        
                    # Insert memory
                    collection.update_one(
                        {'memory_id': memory['memory_id']},
                        {'$set': memory},
                        upsert=True
                    )
                    
                    # Mark as synced in local database
                    cursor = self.local_storage.conn.cursor()
                    cursor.execute('''
                        UPDATE memories SET synced_to_cloud = 1 
                        WHERE memory_id = ?
                    ''', (memory['memory_id'],))
                    
                    stats['migrated'] += 1
                    
                except Exception as e:
                    print(f"❌ Failed to migrate memory {memory['memory_id']}: {e}")
                    stats['failed'] += 1
                    
            stats['chunks_processed'] += 1
            print(f"   Processed chunk {stats['chunks_processed']}/{manifest['chunks']}")
            
        # Migrate neural weights
        if manifest['includes_weights']:
            weights_dir = export_path / "neural_weights"
            weights_collection = self.db['neural_weights']
            
            for weight_file in weights_dir.glob("*.pkl"):
                with open(weight_file, 'rb') as f:
                    weight_data = pickle.load(f)
                    
                # Store in GridFS for large files
                from gridfs import GridFS
                fs = GridFS(self.db)
                
                weight_id = fs.put(
                    pickle.dumps(weight_data),
                    filename=weight_file.name,
                    generation=weight_data['generation'],
                    timestamp=weight_data['timestamp']
                )
                
                print(f"   Uploaded neural weights: {weight_file.name}")
                
        # Migrate quantum states
        if manifest['includes_quantum']:
            quantum_dir = export_path / "quantum_states"
            quantum_collection = self.db['quantum_states']
            
            for state_file in quantum_dir.glob("*.npz"):
                state_data = np.load(state_file)
                
                quantum_collection.insert_one({
                    'filename': state_file.name,
                    'timestamp': state_data['timestamp'].item(),
                    'consciousness_level': float(state_data['consciousness_level']),
                    'state_vector': state_data['state_vector'].tolist()
                })
                
                print(f"   Uploaded quantum state: {state_file.name}")
                
        self.local_storage.conn.commit()
        
        stats['completed_at'] = datetime.now().isoformat()
        stats['success_rate'] = (stats['migrated'] / stats['total_memories'] * 100 
                                 if stats['total_memories'] > 0 else 0)
        
        print(f"\n✅ Cloud migration complete!")
        print(f"   Migrated: {stats['migrated']}/{stats['total_memories']} memories")
        print(f"   Success rate: {stats['success_rate']:.2f}%")
        
        return stats


# Example usage
if __name__ == "__main__":
    # Initialize local storage
    memory_storage = LocalMemoryStorage()
    
    # Save a sample memory
    trade_memory = {
        'symbol': 'AAPL',
        'action': 'BUY',
        'price': 150.25,
        'quantity': 100,
        'confidence': 0.85
    }
    
    memory_id = memory_storage.save_memory('trades', trade_memory)
    print(f"Saved memory: {memory_id}")
    
    # Get stats
    stats = memory_storage.get_stats()
    print(f"\n📊 Memory Statistics:")
    print(f"   Total memories: {stats['total_memories']}")
    print(f"   Storage size: {stats['storage_size_mb']:.2f} MB")
    print(f"   Memory types: {stats['memory_types']}")
    
    # Create backup
    backup_path = memory_storage.create_backup()
    print(f"\nBackup created: {backup_path}")
    
    # Prepare for cloud migration
    export_path = memory_storage.prepare_for_cloud_migration()
    print(f"\nExport prepared: {export_path}")