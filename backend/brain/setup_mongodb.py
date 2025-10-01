"""
MongoDB Setup Script for AuraQuant Quantum Brain
Sets up the database structure and initializes collections
"""

import os
import sys
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from datetime import datetime
import json

def setup_mongodb(mongodb_uri="mongodb://localhost:27017/", reset=False):
    """
    Setup MongoDB for the Quantum Brain
    
    Args:
        mongodb_uri: MongoDB connection string
        reset: If True, drops existing database and recreates
    """
    print("🔧 Setting up MongoDB for AuraQuant Quantum Brain...")
    
    try:
        # Connect to MongoDB
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        
        # Test connection
        client.admin.command('ping')
        print("✅ Connected to MongoDB")
        
        # Get or create database
        db_name = 'auraquant_brain'
        
        if reset:
            print(f"⚠️ Dropping existing database: {db_name}")
            client.drop_database(db_name)
            
        db = client[db_name]
        
        # Create collections with validation schemas
        collections_config = {
            'memories': {
                'validator': {
                    '$jsonSchema': {
                        'bsonType': 'object',
                        'required': ['timestamp', 'pattern_hash', 'action_taken'],
                        'properties': {
                            'timestamp': {'bsonType': 'date'},
                            'pattern_hash': {'bsonType': 'string'},
                            'market_state': {'bsonType': 'object'},
                            'action_taken': {'enum': ['BUY', 'SELL', 'HOLD']},
                            'outcome': {'bsonType': 'double'},
                            'confidence': {'bsonType': 'double', 'minimum': 0, 'maximum': 1},
                            'learning_rate': {'bsonType': 'double'},
                            'evolution_generation': {'bsonType': 'int'},
                            'neural_weights': {'bsonType': 'binData'}
                        }
                    }
                },
                'indexes': [
                    [('timestamp', DESCENDING)],
                    [('pattern_hash', ASCENDING)],
                    [('outcome', DESCENDING)],
                    [('confidence', DESCENDING)],
                    [('evolution_generation', DESCENDING)]
                ]
            },
            'patterns': {
                'validator': {
                    '$jsonSchema': {
                        'bsonType': 'object',
                        'required': ['type', 'probability', 'timestamp'],
                        'properties': {
                            'type': {'bsonType': 'string'},
                            'probability': {'bsonType': 'double', 'minimum': 0, 'maximum': 1},
                            'confidence': {'bsonType': 'double', 'minimum': 0, 'maximum': 1},
                            'timestamp': {'bsonType': 'string'},
                            'frequency': {'bsonType': 'int'},
                            'success_rate': {'bsonType': 'double'}
                        }
                    }
                },
                'indexes': [
                    [('type', ASCENDING)],
                    [('probability', DESCENDING)],
                    [('timestamp', DESCENDING)],
                    [('frequency', DESCENDING)],
                    [('success_rate', DESCENDING)]
                ]
            },
            'evolution': {
                'validator': {
                    '$jsonSchema': {
                        'bsonType': 'object',
                        'required': ['generation', 'timestamp', 'fitness_score'],
                        'properties': {
                            'generation': {'bsonType': 'int', 'minimum': 1},
                            'timestamp': {'bsonType': 'date'},
                            'fitness_score': {'bsonType': 'double', 'minimum': 0, 'maximum': 1},
                            'consciousness_level': {'bsonType': 'double', 'minimum': 0, 'maximum': 1},
                            'quantum_state_hash': {'bsonType': 'string'},
                            'neural_weights': {'bsonType': 'binData'},
                            'mutations_applied': {'bsonType': 'array'}
                        }
                    }
                },
                'indexes': [
                    [('generation', DESCENDING)],
                    [('fitness_score', DESCENDING)],
                    [('timestamp', DESCENDING)]
                ]
            },
            'performance': {
                'validator': {
                    '$jsonSchema': {
                        'bsonType': 'object',
                        'required': ['timestamp', 'symbol', 'prediction', 'actual_outcome'],
                        'properties': {
                            'timestamp': {'bsonType': 'date'},
                            'symbol': {'bsonType': 'string'},
                            'prediction': {'enum': ['BUY', 'SELL', 'HOLD']},
                            'actual_outcome': {'bsonType': 'double'},
                            'profit_loss': {'bsonType': 'double'},
                            'confidence': {'bsonType': 'double'},
                            'generation': {'bsonType': 'int'}
                        }
                    }
                },
                'indexes': [
                    [('timestamp', DESCENDING)],
                    [('symbol', ASCENDING)],
                    [('profit_loss', DESCENDING)],
                    [('generation', DESCENDING)]
                ]
            },
            'market_snapshots': {
                'validator': {
                    '$jsonSchema': {
                        'bsonType': 'object',
                        'required': ['timestamp', 'symbol', 'ohlcv'],
                        'properties': {
                            'timestamp': {'bsonType': 'date'},
                            'symbol': {'bsonType': 'string'},
                            'ohlcv': {
                                'bsonType': 'object',
                                'properties': {
                                    'open': {'bsonType': 'double'},
                                    'high': {'bsonType': 'double'},
                                    'low': {'bsonType': 'double'},
                                    'close': {'bsonType': 'double'},
                                    'volume': {'bsonType': 'long'}
                                }
                            },
                            'indicators': {'bsonType': 'object'},
                            'sentiment': {'bsonType': 'object'}
                        }
                    }
                },
                'indexes': [
                    [('timestamp', DESCENDING)],
                    [('symbol', ASCENDING), ('timestamp', DESCENDING)]
                ]
            },
            'training_sessions': {
                'validator': {
                    '$jsonSchema': {
                        'bsonType': 'object',
                        'required': ['session_id', 'start_time', 'status'],
                        'properties': {
                            'session_id': {'bsonType': 'string'},
                            'start_time': {'bsonType': 'date'},
                            'end_time': {'bsonType': 'date'},
                            'status': {'enum': ['running', 'completed', 'failed']},
                            'epochs_completed': {'bsonType': 'int'},
                            'loss_history': {'bsonType': 'array'},
                            'accuracy_history': {'bsonType': 'array'},
                            'model_checkpoints': {'bsonType': 'array'}
                        }
                    }
                },
                'indexes': [
                    [('session_id', ASCENDING)],
                    [('start_time', DESCENDING)],
                    [('status', ASCENDING)]
                ]
            },
            'quantum_states': {
                'validator': {
                    '$jsonSchema': {
                        'bsonType': 'object',
                        'required': ['timestamp', 'state_vector', 'entanglement_measure'],
                        'properties': {
                            'timestamp': {'bsonType': 'date'},
                            'state_vector': {'bsonType': 'array'},
                            'entanglement_measure': {'bsonType': 'double'},
                            'coherence_time': {'bsonType': 'double'},
                            'decoherence_rate': {'bsonType': 'double'}
                        }
                    }
                },
                'indexes': [
                    [('timestamp', DESCENDING)],
                    [('entanglement_measure', DESCENDING)]
                ]
            }
        }
        
        # Create collections with validation
        for collection_name, config in collections_config.items():
            if collection_name not in db.list_collection_names():
                print(f"📁 Creating collection: {collection_name}")
                db.create_collection(
                    collection_name,
                    validator=config.get('validator')
                )
            else:
                print(f"✓ Collection exists: {collection_name}")
                
            # Create indexes
            collection = db[collection_name]
            for index_spec in config.get('indexes', []):
                collection.create_index(index_spec)
                
        # Create text search index for patterns
        db.patterns.create_index([('type', TEXT)])
        
        # Initialize with seed data
        print("\n🌱 Initializing seed data...")
        
        # Add initial evolution record
        db.evolution.insert_one({
            'generation': 0,
            'timestamp': datetime.now(),
            'fitness_score': 0.5,
            'consciousness_level': 0.5,
            'quantum_state_hash': 'initial_state',
            'neural_weights': b'',
            'mutations_applied': []
        })
        
        # Add sample patterns
        sample_patterns = [
            {'type': 'Breakout', 'probability': 0.0, 'confidence': 0.0, 
             'timestamp': datetime.now().isoformat(), 'frequency': 0, 'success_rate': 0.0},
            {'type': 'Reversal', 'probability': 0.0, 'confidence': 0.0,
             'timestamp': datetime.now().isoformat(), 'frequency': 0, 'success_rate': 0.0},
            {'type': 'Continuation', 'probability': 0.0, 'confidence': 0.0,
             'timestamp': datetime.now().isoformat(), 'frequency': 0, 'success_rate': 0.0}
        ]
        
        for pattern in sample_patterns:
            db.patterns.update_one(
                {'type': pattern['type']},
                {'$set': pattern},
                upsert=True
            )
            
        # Create configuration collection
        db.config.insert_one({
            'version': '1.0.0',
            'created_at': datetime.now(),
            'brain_config': {
                'learning_rate': 0.001,
                'evolution_threshold': 0.7,
                'memory_capacity': 10000,
                'quantum_dimensions': 1024,
                'consciousness_threshold': 0.8
            },
            'trading_config': {
                'risk_tolerance': 0.02,
                'position_size': 0.1,
                'stop_loss': 0.05,
                'take_profit': 0.10,
                'max_positions': 5
            }
        })
        
        print("\n✅ MongoDB setup complete!")
        
        # Display statistics
        print("\n📊 Database Statistics:")
        stats = db.command("dbStats")
        print(f"  Database: {db_name}")
        print(f"  Collections: {stats['collections']}")
        print(f"  Data Size: {stats['dataSize']} bytes")
        print(f"  Storage Size: {stats['storageSize']} bytes")
        
        # Display collection counts
        print("\n📈 Collection Counts:")
        for collection_name in db.list_collection_names():
            count = db[collection_name].count_documents({})
            print(f"  {collection_name}: {count} documents")
            
        return db
        
    except Exception as e:
        print(f"\n❌ Error setting up MongoDB: {e}")
        print("\nPlease ensure MongoDB is installed and running:")
        print("  1. Install MongoDB: https://www.mongodb.com/try/download/community")
        print("  2. Start MongoDB service:")
        print("     - Windows: net start MongoDB")
        print("     - Mac/Linux: sudo systemctl start mongod")
        print(f"  3. Verify connection: mongo {mongodb_uri}")
        return None

def create_backup(db, backup_dir="backups"):
    """Create a backup of the brain database"""
    import os
    import json
    from bson import json_util
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"brain_backup_{timestamp}")
    os.makedirs(backup_path)
    
    print(f"\n💾 Creating backup at: {backup_path}")
    
    for collection_name in db.list_collection_names():
        collection = db[collection_name]
        documents = list(collection.find())
        
        if documents:
            file_path = os.path.join(backup_path, f"{collection_name}.json")
            with open(file_path, 'w') as f:
                json.dump(documents, f, default=json_util.default, indent=2)
            print(f"  ✓ Backed up {collection_name}: {len(documents)} documents")
            
    print(f"\n✅ Backup complete: {backup_path}")
    return backup_path

def restore_backup(backup_path, mongodb_uri="mongodb://localhost:27017/"):
    """Restore brain database from backup"""
    import json
    from bson import json_util
    
    print(f"\n📂 Restoring from backup: {backup_path}")
    
    client = MongoClient(mongodb_uri)
    db = client['auraquant_brain']
    
    for filename in os.listdir(backup_path):
        if filename.endswith('.json'):
            collection_name = filename[:-5]  # Remove .json extension
            file_path = os.path.join(backup_path, filename)
            
            with open(file_path, 'r') as f:
                documents = json.load(f, object_hook=json_util.object_hook)
                
            if documents:
                collection = db[collection_name]
                collection.delete_many({})  # Clear existing data
                collection.insert_many(documents)
                print(f"  ✓ Restored {collection_name}: {len(documents)} documents")
                
    print("\n✅ Restore complete!")

if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup MongoDB for AuraQuant Quantum Brain')
    parser.add_argument('--uri', default='mongodb://localhost:27017/', 
                       help='MongoDB connection URI')
    parser.add_argument('--reset', action='store_true', 
                       help='Drop existing database and recreate')
    parser.add_argument('--backup', action='store_true',
                       help='Create backup after setup')
    parser.add_argument('--restore', type=str,
                       help='Restore from backup directory')
    
    args = parser.parse_args()
    
    if args.restore:
        restore_backup(args.restore, args.uri)
    else:
        db = setup_mongodb(args.uri, args.reset)
        
        if db and args.backup:
            create_backup(db)
            
    print("\n🚀 Ready to launch Quantum Brain!")