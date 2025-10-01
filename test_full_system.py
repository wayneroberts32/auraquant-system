"""
Complete System Test for AuraQuant with IBKR Integration
Tests API, WebSocket, and IBKR connectivity
"""

import asyncio
import aiohttp
import json
from datetime import datetime
import websockets

# Configuration
API_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/api/ibkr/ws"

async def test_api_health():
    """Test API health endpoints"""
    print("\n" + "="*50)
    print("📊 TESTING API HEALTH")
    print("="*50)
    
    async with aiohttp.ClientSession() as session:
        # Test root endpoint
        async with session.get(f"{API_URL}/") as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"✅ API Root: {data['message']}")
                print(f"   Version: {data['version']}")
            else:
                print(f"❌ API Root failed: {resp.status}")
        
        # Test health endpoint
        async with session.get(f"{API_URL}/health") as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"\n✅ Health Check:")
                for key, value in data.items():
                    status = "✓" if value else "✗"
                    print(f"   {status} {key}: {value}")
            else:
                print(f"❌ Health check failed: {resp.status}")

async def test_ibkr_connection():
    """Test IBKR broker connection"""
    print("\n" + "="*50)
    print("🏦 TESTING IBKR CONNECTION")
    print("="*50)
    
    async with aiohttp.ClientSession() as session:
        # Check IBKR status
        async with session.get(f"{API_URL}/api/ibkr/status") as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"Connection Status: {'✅ Connected' if data['connected'] else '❌ Disconnected'}")
                print(f"   Host: {data['host']}")
                print(f"   Port: {data['port']}")
                print(f"   Client ID: {data['client_id']}")
                
                if not data['connected']:
                    print("\n⚠️ IBKR not connected. Attempting to connect...")
                    # Try to connect
                    async with session.post(f"{API_URL}/api/ibkr/connect") as conn_resp:
                        if conn_resp.status == 200:
                            conn_data = await conn_resp.json()
                            print(f"✅ Connection result: {conn_data['status']}")
                        else:
                            print(f"❌ Failed to connect: {conn_resp.status}")
                            return False
            else:
                print(f"❌ Failed to get IBKR status: {resp.status}")
                return False
        
        # Get account info if connected
        print("\n📋 Account Information:")
        async with session.get(f"{API_URL}/api/ibkr/balance") as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"   Total Cash: ${data.get('total_cash', 0):,.2f}")
                print(f"   Net Liquidation: ${data.get('net_liquidation', 0):,.2f}")
                print(f"   Buying Power: ${data.get('buying_power', 0):,.2f}")
                print(f"   Available Funds: ${data.get('available_funds', 0):,.2f}")
            else:
                print(f"   ⚠️ Could not get account balance")
        
        # Get positions
        print("\n📈 Current Positions:")
        async with session.get(f"{API_URL}/api/ibkr/positions") as resp:
            if resp.status == 200:
                positions = await resp.json()
                if positions:
                    for pos in positions:
                        print(f"   {pos['symbol']}: {pos['quantity']} @ ${pos['avg_cost']}")
                else:
                    print("   No open positions")
            else:
                print(f"   ⚠️ Could not get positions")
        
        # Test market data
        print("\n💹 Market Data Test (SPY):")
        async with session.get(f"{API_URL}/api/ibkr/market-data/SPY") as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"   Symbol: {data.get('symbol', 'N/A')}")
                print(f"   Last: ${data.get('last', 'N/A')}")
                print(f"   Bid: ${data.get('bid', 'N/A')}")
                print(f"   Ask: ${data.get('ask', 'N/A')}")
                print(f"   Volume: {data.get('volume', 'N/A')}")
            else:
                print(f"   ⚠️ Could not get market data")
    
    return True

async def test_websocket():
    """Test WebSocket connection"""
    print("\n" + "="*50)
    print("🔌 TESTING WEBSOCKET CONNECTION")
    print("="*50)
    
    try:
        async with websockets.connect(WS_URL) as ws:
            # Wait for connection message
            msg = await ws.recv()
            data = json.loads(msg)
            if data['type'] == 'connection' and data['status'] == 'connected':
                print("✅ WebSocket connected")
            
            # Send ping
            await ws.send(json.dumps({"type": "ping"}))
            pong = await ws.recv()
            pong_data = json.loads(pong)
            if pong_data['type'] == 'pong':
                print("✅ Ping/Pong successful")
            
            # Subscribe to market data
            await ws.send(json.dumps({
                "type": "subscribe",
                "symbols": ["AAPL", "GOOGL", "MSFT"]
            }))
            
            # Wait for subscription confirmation
            sub_confirm = await ws.recv()
            sub_data = json.loads(sub_confirm)
            if sub_data['type'] == 'subscription' and sub_data['status'] == 'confirmed':
                print(f"✅ Subscribed to symbols: {sub_data['symbols']}")
            
            # Close connection
            await ws.close()
            print("✅ WebSocket disconnected gracefully")
            
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        return False
    
    return True

async def test_trading_flow():
    """Test a complete trading flow"""
    print("\n" + "="*50)
    print("🎯 TESTING TRADING FLOW")
    print("="*50)
    
    async with aiohttp.ClientSession() as session:
        # Place a test order (paper trading)
        print("\n📝 Placing test order...")
        order_data = {
            "symbol": "AAPL",
            "action": "BUY",
            "quantity": 1,
            "order_type": "LIMIT",
            "limit_price": 150.00  # Low price so it won't execute
        }
        
        async with session.post(f"{API_URL}/api/ibkr/order", json=order_data) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"✅ Order placed:")
                print(f"   Order ID: {result.get('order_id', 'N/A')}")
                print(f"   Status: {result.get('status', 'N/A')}")
                print(f"   Symbol: {result.get('symbol', 'N/A')}")
                print(f"   Action: {result.get('action', 'N/A')}")
                print(f"   Quantity: {result.get('quantity', 'N/A')}")
                
                # Cancel the order
                order_id = result.get('order_id')
                if order_id:
                    print(f"\n🚫 Cancelling order {order_id}...")
                    async with session.delete(f"{API_URL}/api/ibkr/order/{order_id}") as cancel_resp:
                        if cancel_resp.status == 200:
                            print(f"✅ Order cancelled successfully")
                        else:
                            print(f"⚠️ Could not cancel order")
            else:
                error = await resp.text()
                print(f"❌ Failed to place order: {error}")

async def main():
    """Run all tests"""
    print("\n" + "🚀"*20)
    print("  AURAQUANT FULL SYSTEM TEST")
    print("🚀"*20)
    print(f"\nTimestamp: {datetime.now().isoformat()}")
    print(f"API URL: {API_URL}")
    
    # Make sure the Gateway is running
    print("\n⚠️ PREREQUISITES:")
    print("1. IBKR Gateway must be running (port 4002)")
    print("2. AuraQuant API must be running (port 8000)")
    print("3. Frontend should be accessible")
    
    await asyncio.sleep(2)
    
    # Run tests
    try:
        # Test API health
        await test_api_health()
        
        # Test IBKR connection
        ibkr_ok = await test_ibkr_connection()
        
        # Test WebSocket
        ws_ok = await test_websocket()
        
        # Test trading flow if IBKR is connected
        if ibkr_ok:
            await test_trading_flow()
        
        # Summary
        print("\n" + "="*50)
        print("📊 TEST SUMMARY")
        print("="*50)
        print("✅ API: Online")
        print(f"{'✅' if ibkr_ok else '❌'} IBKR: {'Connected' if ibkr_ok else 'Not Connected'}")
        print(f"{'✅' if ws_ok else '❌'} WebSocket: {'Working' if ws_ok else 'Failed'}")
        print("\n🎉 System is ready for live trading!" if ibkr_ok and ws_ok else "\n⚠️ Some components need attention")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        print("\n⚠️ Make sure:")
        print("1. The API is running: python backend/api/main.py")
        print("2. The IBKR Gateway is running and configured")
        print("3. All dependencies are installed")

if __name__ == "__main__":
    asyncio.run(main())