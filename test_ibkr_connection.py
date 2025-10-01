"""
Test IBKR Gateway Connection
Tests connection to Interactive Brokers Gateway
"""

from ib_insync import *
import asyncio
from datetime import datetime

def test_connection():
    """Test connection to IBKR Gateway"""
    
    # Create IB connection object
    ib = IB()
    
    print("\n" + "="*50)
    print("🔧 TESTING IBKR GATEWAY CONNECTION")
    print("="*50)
    
    # Test Paper Trading first (safer)
    print("\n📊 Attempting to connect to PAPER TRADING...")
    print("   Port: 4002")
    print("   Host: 127.0.0.1")
    
    try:
        # Connect to paper trading gateway
        ib.connect('127.0.0.1', 4002, clientId=1)
        
        print("\n✅ CONNECTION SUCCESSFUL!")
        print("-"*40)
        
        # Get account info
        account = ib.accountSummary()
        if account:
            print("\n📋 ACCOUNT INFORMATION:")
            for item in account[:5]:  # Show first 5 items
                print(f"   {item.tag}: {item.value}")
        
        # Get positions
        positions = ib.positions()
        print(f"\n📈 POSITIONS: {len(positions)} open positions")
        
        # Test market data - SPY
        contract = Stock('SPY', 'SMART', 'USD')
        ticker = ib.reqMktData(contract)
        ib.sleep(2)  # Wait for data
        
        if ticker.last:
            print(f"\n💹 MARKET DATA TEST (SPY):")
            print(f"   Last Price: ${ticker.last}")
            print(f"   Bid: ${ticker.bid}")
            print(f"   Ask: ${ticker.ask}")
        
        print("\n" + "="*50)
        print("✅ ALL TESTS PASSED! Gateway is working!")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ CONNECTION FAILED!")
        print(f"   Error: {e}")
        print("\n🔍 TROUBLESHOOTING:")
        print("   1. Is the Gateway running and showing 'Ready'?")
        print("   2. Is port 4002 correct for paper trading?")
        print("   3. Did you uncheck 'localhost only'?")
        print("   4. Try restarting the Gateway")
        
    finally:
        if ib.isConnected():
            ib.disconnect()
            print("\n📤 Disconnected from Gateway")

if __name__ == "__main__":
    # Run the test
    test_connection()
    
    print("\n💡 Next steps:")
    print("   1. If successful, test with LIVE account (port 4001)")
    print("   2. Integrate into your AuraQuant backend")
    print("   3. Set up data streaming for your dashboard")