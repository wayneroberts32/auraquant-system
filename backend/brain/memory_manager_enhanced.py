"""
Enhanced Memory Manager with MongoDB Hybrid Storage
Engineer's Note: This ENHANCES your existing memory_manager.py with MongoDB
WITHOUT modifying the original code - Task 4/12
"""

import os
import json
import pickle
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import threading
import queue
from collections import deque
from dataclasses import dataclass, asdict

from brain.mongodb_persistence import get_persistence_service

@dataclass
class MemoryEntry:
    """Enhanced memory entry with MongoDB support"""
    memory_id: str
    timestamp: datetime
    memory_type: str
    data: Dict[str, Any]
    importance: float
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    synced_to_cloud: bool = False

class HybridMemoryManager:
    """
    Hybrid memory management with local cache and MongoDB persistence
    Works alongside existing LocalMemoryStorage without modifications
    """
    
    def __init__(self, local_memory_instance=None, cache_size: int = 1000):
        """
        Initialize hybrid memory manager
        
        Args:
            local_memory_instance: Your existing LocalMemoryStorage instance
            cache_size: Maximum size of in-memory cache
        """
        self.local_memory = local_memory_instance
        self.cache_size = cache_size
        
        # Memory structures
        self.short_term_memory = deque(maxlen=100)  # Fast access buffer
        self.memory_cache = {}  # LRU cache for frequently accessed memories
        self.cache_access_counts = {}
        
        # MongoDB persistence
        self.persistence = get_persistence_service()
        
        # Sync management
        self.sync_queue = queue.Queue()
        self.sync_thread = None
        self.running = True
        
        # Memory consolidation settings
        self.consolidation_interval = 300  # 5 minutes
        self.last_consolidation = datetime.now()
        
        # Memory indexing
        self.memory_index = {}
        self._build_index()
        
        print("🧠 Hybrid Memory Manager Initialized")
        self._start_sync_thread()
        
    def _start_sync_thread(self):
        """Start background synchronization thread"""
        self.sync_thread = threading.Thread(target=self._sync_worker, daemon=True)
        self.sync_thread.start()
        print("🔄 Memory synchronization started")
        
    def _sync_worker(self):
        """Background worker for MongoDB synchronization"""
        while self.running:
            try:
                # Process sync queue
                if not self.sync_queue.empty():
                    memory = self.sync_queue.get(timeout=1)
                    self._sync_to_mongodb(memory)
                    
                # Periodic consolidation
                if (datetime.now() - self.last_consolidation).seconds > self.consolidation_interval:
                    self._consolidate_memories()
                    self.last_consolidation = datetime.now()
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in sync worker: {e}")
                
    def save_memory(self, memory_type: str, data: Dict[str, Any], 
                   importance: float = 0.5) -> str:
        """
        Save memory with hybrid storage strategy
        
        Args:
            memory_type: Type of memory
            data: Memory data
            importance: Importance score (0-1)
            
        Returns:
            Memory ID
        """
        # Generate memory ID
        memory_id = self._generate_memory_id(memory_type, data)
        
        # Create memory entry
        memory = MemoryEntry(
            memory_id=memory_id,
            timestamp=datetime.now(),
            memory_type=memory_type,
            data=data,
            importance=importance
        )
        
        # Add to short-term memory (immediate access)
        self.short_term_memory.append(memory)
        
        # Cache if important
        if importance > 0.7:
            self.memory_cache[memory_id] = memory
            self.cache_access_counts[memory_id] = 0
            
        # Update index
        self._index_memory(memory)
        
        # Queue for MongoDB sync
        self.sync_queue.put(memory)
        
        # Also save locally if available
        if self.local_memory:
            try:
                self.local_memory.save_memory(memory_type, data, {'importance': importance})
            except:
                pass
                
        return memory_id
        
    def retrieve_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        """
        Retrieve memory with cache-first strategy
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            Memory entry or None
        """
        # Check short-term memory first
        for memory in self.short_term_memory:
            if memory.memory_id == memory_id:
                memory.access_count += 1
                memory.last_accessed = datetime.now()
                return memory
                
        # Check cache
        if memory_id in self.memory_cache:
            memory = self.memory_cache[memory_id]
            memory.access_count += 1
            memory.last_accessed = datetime.now()
            self.cache_access_counts[memory_id] += 1
            
            # Promote to short-term if frequently accessed
            if self.cache_access_counts[memory_id] > 5:
                self.short_term_memory.append(memory)
                
            return memory
            
        # Load from MongoDB
        if self.persistence and self.persistence.db:
            try:
                doc = self.persistence.db.brain_memories.find_one({'memory_id': memory_id})
                if doc:
                    memory = self._doc_to_memory(doc)
                    
                    # Add to cache
                    self._add_to_cache(memory)
                    
                    return memory
            except Exception as e:
                print(f"Error retrieving from MongoDB: {e}")
                
        # Fallback to local storage
        if self.local_memory:
            try:
                local_data = self.local_memory.retrieve_memory(memory_id)
                if local_data:
                    return MemoryEntry(
                        memory_id=memory_id,
                        timestamp=datetime.now(),
                        memory_type="local",
                        data=local_data,
                        importance=0.5
                    )
            except:
                pass
                
        return None
        
    def search_memories(self, query: Dict[str, Any], limit: int = 10) -> List[MemoryEntry]:
        """
        Search memories across all storage layers
        
        Args:
            query: Search criteria
            limit: Maximum results
            
        Returns:
            List of matching memories
        """
        results = []
        
        # Search short-term memory
        for memory in self.short_term_memory:
            if self._matches_query(memory, query):
                results.append(memory)
                if len(results) >= limit:
                    return results
                    
        # Search cache
        for memory in self.memory_cache.values():
            if memory not in results and self._matches_query(memory, query):
                results.append(memory)
                if len(results) >= limit:
                    return results
                    
        # Search MongoDB
        if self.persistence and self.persistence.db and len(results) < limit:
            try:
                cursor = self.persistence.db.brain_memories.find(
                    query, 
                    limit=limit - len(results)
                )
                for doc in cursor:
                    memory = self._doc_to_memory(doc)
                    if memory not in results:
                        results.append(memory)
                        self._add_to_cache(memory)
            except Exception as e:
                print(f"Error searching MongoDB: {e}")
                
        return results[:limit]
        
    def _consolidate_memories(self):
        """Consolidate short-term memories to long-term storage"""
        if not self.short_term_memory:
            return
            
        print("🔄 Consolidating memories...")
        
        # Identify important memories
        important_memories = []
        for memory in list(self.short_term_memory):
            # Consolidation criteria
            if (memory.importance > 0.6 or 
                memory.access_count > 3 or
                memory.memory_type in ['pattern', 'evolution', 'trade']):
                important_memories.append(memory)
                
        # Move to long-term storage
        for memory in important_memories:
            # Ensure MongoDB sync
            if not memory.synced_to_cloud:
                self.sync_queue.put(memory)
                
            # Update cache
            if memory.memory_id not in self.memory_cache:
                self._add_to_cache(memory)
                
        print(f"✅ Consolidated {len(important_memories)} memories")
        
    def _sync_to_mongodb(self, memory: MemoryEntry):
        """Sync memory to MongoDB"""
        if not self.persistence or not self.persistence.db:
            return
            
        try:
            # Prepare document
            doc = asdict(memory)
            doc['_id'] = memory.memory_id
            
            # Upsert to MongoDB
            self.persistence.db.brain_memories.update_one(
                {'_id': memory.memory_id},
                {'$set': doc},
                upsert=True
            )
            
            memory.synced_to_cloud = True
            
        except Exception as e:
            print(f"Error syncing to MongoDB: {e}")
            
    def _add_to_cache(self, memory: MemoryEntry):
        """Add memory to cache with LRU eviction"""
        # Check cache size
        if len(self.memory_cache) >= self.cache_size:
            # Evict least recently used
            lru_id = min(self.cache_access_counts, 
                        key=lambda k: self.cache_access_counts[k])
            del self.memory_cache[lru_id]
            del self.cache_access_counts[lru_id]
            
        # Add to cache
        self.memory_cache[memory.memory_id] = memory
        self.cache_access_counts[memory.memory_id] = 0
        
    def _build_index(self):
        """Build memory index for fast retrieval"""
        self.memory_index = {
            'by_type': {},
            'by_date': {},
            'by_importance': {}
        }
        
        # Index existing memories
        for memory in self.memory_cache.values():
            self._index_memory(memory)
            
    def _index_memory(self, memory: MemoryEntry):
        """Add memory to index"""
        # Index by type
        if memory.memory_type not in self.memory_index['by_type']:
            self.memory_index['by_type'][memory.memory_type] = []
        self.memory_index['by_type'][memory.memory_type].append(memory.memory_id)
        
        # Index by date
        date_key = memory.timestamp.date().isoformat()
        if date_key not in self.memory_index['by_date']:
            self.memory_index['by_date'][date_key] = []
        self.memory_index['by_date'][date_key].append(memory.memory_id)
        
        # Index by importance
        importance_bucket = int(memory.importance * 10)
        if importance_bucket not in self.memory_index['by_importance']:
            self.memory_index['by_importance'][importance_bucket] = []
        self.memory_index['by_importance'][importance_bucket].append(memory.memory_id)
        
    def _matches_query(self, memory: MemoryEntry, query: Dict) -> bool:
        """Check if memory matches query criteria"""
        for key, value in query.items():
            if key == 'memory_type' and memory.memory_type != value:
                return False
            elif key == 'min_importance' and memory.importance < value:
                return False
            elif key in memory.data and memory.data[key] != value:
                return False
        return True
        
    def _doc_to_memory(self, doc: Dict) -> MemoryEntry:
        """Convert MongoDB document to MemoryEntry"""
        return MemoryEntry(
            memory_id=doc.get('memory_id', doc.get('_id')),
            timestamp=doc.get('timestamp', datetime.now()),
            memory_type=doc.get('memory_type', 'unknown'),
            data=doc.get('data', {}),
            importance=doc.get('importance', 0.5),
            access_count=doc.get('access_count', 0),
            last_accessed=doc.get('last_accessed'),
            synced_to_cloud=True
        )
        
    def _generate_memory_id(self, memory_type: str, data: Dict) -> str:
        """Generate unique memory ID"""
        content = f"{memory_type}:{json.dumps(data, sort_keys=True)}:{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()
        
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        stats = {
            'short_term_count': len(self.short_term_memory),
            'cache_count': len(self.memory_cache),
            'total_accesses': sum(self.cache_access_counts.values()),
            'memory_types': list(self.memory_index['by_type'].keys()),
            'sync_queue_size': self.sync_queue.qsize()
        }
        
        if self.persistence and self.persistence.db:
            try:
                stats['mongodb_count'] = self.persistence.db.brain_memories.count_documents({})
            except:
                stats['mongodb_count'] = 0
                
        return stats
        
    def flush_to_mongodb(self):
        """Force flush all memories to MongoDB"""
        print("💾 Flushing all memories to MongoDB...")
        
        # Flush short-term memory
        for memory in self.short_term_memory:
            if not memory.synced_to_cloud:
                self.sync_queue.put(memory)
                
        # Flush cache
        for memory in self.memory_cache.values():
            if not memory.synced_to_cloud:
                self.sync_queue.put(memory)
                
        # Wait for queue to empty
        while not self.sync_queue.empty():
            import time
            time.sleep(0.1)
            
        print("✅ Memory flush complete")
        
    def shutdown(self):
        """Graceful shutdown"""
        print("Shutting down Hybrid Memory Manager...")
        
        # Final flush
        self.flush_to_mongodb()
        
        # Stop sync thread
        self.running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
            
        print("✅ Hybrid Memory Manager shut down")

# Global instance
_hybrid_manager = None

def get_hybrid_memory_manager():
    """Get or create hybrid memory manager"""
    global _hybrid_manager
    if _hybrid_manager is None:
        _hybrid_manager = HybridMemoryManager()
    return _hybrid_manager

# Helper functions
def save_hybrid_memory(memory_type: str, data: Dict, importance: float = 0.5) -> str:
    """Save memory using hybrid storage"""
    manager = get_hybrid_memory_manager()
    return manager.save_memory(memory_type, data, importance)

def retrieve_hybrid_memory(memory_id: str):
    """Retrieve memory from hybrid storage"""
    manager = get_hybrid_memory_manager()
    return manager.retrieve_memory(memory_id)

def search_hybrid_memories(query: Dict, limit: int = 10):
    """Search memories across all storage"""
    manager = get_hybrid_memory_manager()
    return manager.search_memories(query, limit)