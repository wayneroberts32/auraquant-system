"""
Trading Journal Routes
Handles trading journal entries and history
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import pandas as pd
import io
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import db_config
from core.auth import get_current_user

router = APIRouter()

class JournalEntry(BaseModel):
    symbol: str
    side: str  # buy, sell
    entry_price: float
    exit_price: Optional[float] = None
    size: float
    pnl: Optional[float] = None
    strategy: Optional[str] = ""
    notes: Optional[str] = ""
    tags: List[str] = []
    emotions: Optional[str] = ""  # calm, anxious, confident, fearful
    
class JournalFilter(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    symbol: Optional[str] = None
    strategy: Optional[str] = None
    side: Optional[str] = None
    min_pnl: Optional[float] = None
    max_pnl: Optional[float] = None

@router.post("/add")
async def add_journal_entry(
    entry: JournalEntry,
    current_user: dict = Depends(get_current_user)
):
    """Add a new journal entry"""
    try:
        client = AsyncIOMotorClient(db_config.mongodb_uri)
        db = client[db_config.database_name]
        
        # Prepare journal entry
        journal_doc = entry.dict()
        journal_doc["user_id"] = current_user["user_id"]
        journal_doc["timestamp"] = datetime.utcnow()
        
        # Calculate P&L if not provided
        if entry.exit_price and not entry.pnl:
            if entry.side == "buy":
                journal_doc["pnl"] = (entry.exit_price - entry.entry_price) * entry.size
            else:  # sell
                journal_doc["pnl"] = (entry.entry_price - entry.exit_price) * entry.size
        
        # Add performance metrics
        journal_doc["win"] = journal_doc.get("pnl", 0) > 0 if journal_doc.get("pnl") is not None else None
        
        # Insert entry
        result = await db.trading_journal.insert_one(journal_doc)
        
        # Update user statistics
        await update_user_stats(db, current_user["user_id"])
        
        return {
            "success": True,
            "message": "Journal entry added successfully",
            "entry_id": str(result.inserted_id)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        client.close()

@router.get("/list")
async def list_journal_entries(
    current_user: dict = Depends(get_current_user),
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    sort: str = Query("timestamp", regex="^(timestamp|pnl|symbol)$"),
    order: int = Query(-1, ge=-1, le=1)
):
    """List user's journal entries"""
    try:
        client = AsyncIOMotorClient(db_config.mongodb_uri)
        db = client[db_config.database_name]
        
        # Query user's entries
        cursor = db.trading_journal.find(
            {"user_id": current_user["user_id"]}
        ).sort(sort, order).skip(skip).limit(limit)
        
        entries = await cursor.to_list(limit)
        
        # Convert ObjectId to string
        for entry in entries:
            entry["_id"] = str(entry["_id"])
        
        # Get total count
        total = await db.trading_journal.count_documents(
            {"user_id": current_user["user_id"]}
        )
        
        return {
            "success": True,
            "entries": entries,
            "total": total,
            "page": skip // limit + 1,
            "pages": (total + limit - 1) // limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        client.close()

@router.post("/filter")
async def filter_journal_entries(
    filter_params: JournalFilter,
    current_user: dict = Depends(get_current_user),
    limit: int = Query(100, ge=1, le=1000)
):
    """Filter journal entries based on criteria"""
    try:
        client = AsyncIOMotorClient(db_config.mongodb_uri)
        db = client[db_config.database_name]
        
        # Build filter query
        query = {"user_id": current_user["user_id"]}
        
        if filter_params.start_date:
            query["timestamp"] = {"$gte": filter_params.start_date}
        if filter_params.end_date:
            if "timestamp" in query:
                query["timestamp"]["$lte"] = filter_params.end_date
            else:
                query["timestamp"] = {"$lte": filter_params.end_date}
        
        if filter_params.symbol:
            query["symbol"] = filter_params.symbol
        if filter_params.strategy:
            query["strategy"] = filter_params.strategy
        if filter_params.side:
            query["side"] = filter_params.side
        
        if filter_params.min_pnl is not None:
            query["pnl"] = {"$gte": filter_params.min_pnl}
        if filter_params.max_pnl is not None:
            if "pnl" in query:
                query["pnl"]["$lte"] = filter_params.max_pnl
            else:
                query["pnl"] = {"$lte": filter_params.max_pnl}
        
        # Execute query
        cursor = db.trading_journal.find(query).sort("timestamp", -1).limit(limit)
        entries = await cursor.to_list(limit)
        
        # Convert ObjectId to string
        for entry in entries:
            entry["_id"] = str(entry["_id"])
        
        return {
            "success": True,
            "entries": entries,
            "filter_applied": filter_params.dict()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        client.close()

@router.put("/update/{entry_id}")
async def update_journal_entry(
    entry_id: str,
    entry: JournalEntry,
    current_user: dict = Depends(get_current_user)
):
    """Update a journal entry"""
    try:
        from bson import ObjectId
        
        client = AsyncIOMotorClient(db_config.mongodb_uri)
        db = client[db_config.database_name]
        
        # Update entry (only if belongs to user)
        result = await db.trading_journal.update_one(
            {
                "_id": ObjectId(entry_id),
                "user_id": current_user["user_id"]
            },
            {
                "$set": {
                    **entry.dict(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        # Update user statistics
        await update_user_stats(db, current_user["user_id"])
        
        return {
            "success": True,
            "message": "Journal entry updated successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        client.close()

@router.delete("/delete/{entry_id}")
async def delete_journal_entry(
    entry_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a journal entry"""
    try:
        from bson import ObjectId
        
        client = AsyncIOMotorClient(db_config.mongodb_uri)
        db = client[db_config.database_name]
        
        # Delete entry (only if belongs to user)
        result = await db.trading_journal.delete_one({
            "_id": ObjectId(entry_id),
            "user_id": current_user["user_id"]
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        # Update user statistics
        await update_user_stats(db, current_user["user_id"])
        
        return {
            "success": True,
            "message": "Journal entry deleted successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        client.close()

@router.get("/statistics")
async def get_journal_statistics(
    current_user: dict = Depends(get_current_user)
):
    """Get trading journal statistics"""
    try:
        client = AsyncIOMotorClient(db_config.mongodb_uri)
        db = client[db_config.database_name]
        
        # Get user's entries
        entries = await db.trading_journal.find(
            {"user_id": current_user["user_id"]}
        ).to_list(10000)
        
        if not entries:
            return {
                "success": True,
                "statistics": {
                    "total_trades": 0,
                    "total_pnl": 0,
                    "win_rate": 0,
                    "average_win": 0,
                    "average_loss": 0,
                    "profit_factor": 0,
                    "best_trade": 0,
                    "worst_trade": 0,
                    "trading_days": 0
                }
            }
        
        # Calculate statistics
        df = pd.DataFrame(entries)
        
        total_trades = len(df)
        total_pnl = df['pnl'].sum() if 'pnl' in df else 0
        
        wins = df[df['pnl'] > 0] if 'pnl' in df else pd.DataFrame()
        losses = df[df['pnl'] < 0] if 'pnl' in df else pd.DataFrame()
        
        win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0
        average_win = wins['pnl'].mean() if len(wins) > 0 else 0
        average_loss = losses['pnl'].mean() if len(losses) > 0 else 0
        
        gross_profit = wins['pnl'].sum() if len(wins) > 0 else 0
        gross_loss = abs(losses['pnl'].sum()) if len(losses) > 0 else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf') if gross_profit > 0 else 0
        
        best_trade = df['pnl'].max() if 'pnl' in df else 0
        worst_trade = df['pnl'].min() if 'pnl' in df else 0
        
        # Trading days
        if 'timestamp' in df:
            df['date'] = pd.to_datetime(df['timestamp']).dt.date
            trading_days = df['date'].nunique()
        else:
            trading_days = 0
        
        statistics = {
            "total_trades": int(total_trades),
            "total_pnl": float(total_pnl),
            "win_rate": float(win_rate),
            "average_win": float(average_win),
            "average_loss": float(average_loss),
            "profit_factor": float(profit_factor) if profit_factor != float('inf') else 999,
            "best_trade": float(best_trade),
            "worst_trade": float(worst_trade),
            "trading_days": int(trading_days)
        }
        
        return {"success": True, "statistics": statistics}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        client.close()

@router.get("/export/csv")
async def export_journal_csv(
    current_user: dict = Depends(get_current_user)
):
    """Export journal entries as CSV"""
    try:
        client = AsyncIOMotorClient(db_config.mongodb_uri)
        db = client[db_config.database_name]
        
        # Get all user's entries
        entries = await db.trading_journal.find(
            {"user_id": current_user["user_id"]}
        ).sort("timestamp", -1).to_list(10000)
        
        if not entries:
            raise HTTPException(status_code=404, detail="No entries to export")
        
        # Convert to DataFrame
        df = pd.DataFrame(entries)
        
        # Select columns to export
        export_columns = [
            'timestamp', 'symbol', 'side', 'entry_price', 'exit_price',
            'size', 'pnl', 'strategy', 'notes', 'tags', 'emotions'
        ]
        
        # Keep only existing columns
        export_columns = [col for col in export_columns if col in df.columns]
        df = df[export_columns]
        
        # Convert to CSV
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        # Create response
        return StreamingResponse(
            io.BytesIO(csv_buffer.getvalue().encode()),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=trading_journal_{datetime.now().strftime('%Y%m%d')}.csv"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        client.close()

async def update_user_stats(db, user_id: str):
    """Update user trading statistics"""
    try:
        # Calculate aggregate stats
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": "$user_id",
                "total_trades": {"$sum": 1},
                "total_pnl": {"$sum": "$pnl"},
                "winning_trades": {
                    "$sum": {"$cond": [{"$gt": ["$pnl", 0]}, 1, 0]}
                },
                "losing_trades": {
                    "$sum": {"$cond": [{"$lt": ["$pnl", 0]}, 1, 0]}
                }
            }}
        ]
        
        result = await db.trading_journal.aggregate(pipeline).to_list(1)
        
        if result:
            stats = result[0]
            win_rate = (stats['winning_trades'] / stats['total_trades'] * 100) if stats['total_trades'] > 0 else 0
            
            # Update user profile with latest stats
            await db.user_profiles.update_one(
                {"user_id": user_id},
                {"$set": {
                    "trading_stats": {
                        "total_trades": stats['total_trades'],
                        "total_pnl": stats['total_pnl'],
                        "win_rate": win_rate,
                        "winning_trades": stats['winning_trades'],
                        "losing_trades": stats['losing_trades'],
                        "last_updated": datetime.utcnow()
                    }
                }}
            )
    except Exception as e:
        print(f"Error updating user stats: {e}")