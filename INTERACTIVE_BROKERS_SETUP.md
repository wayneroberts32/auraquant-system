# Interactive Brokers Setup for AuraQuant Trading System

## 🎯 OVERVIEW
Interactive Brokers (IB) will handle your ASX stock trading. This requires TWO components:
1. **IB Gateway** or **TWS** (runs locally or on cloud)
2. **API Connection** (from AuraQuant to IB)

---

## STEP 1: ACCOUNT REQUIREMENTS

### You Need:
- ✅ Interactive Brokers account (Individual or LLC)
- ✅ Trading permissions for ASX enabled
- ✅ API Trading enabled in account settings
- ✅ Market data subscriptions (ASX Level 1 minimum)

### Enable API Trading:
1. Log into IB Account Management
2. Go to Settings → API → Settings
3. Enable: "Enable ActiveX and Socket Clients"
4. Enable: "Download open orders on connection"
5. Enable: "Send account window updates"
6. IMPORTANT: Set "Master API client ID" to: 100

---

## STEP 2: CHOOSE YOUR CONNECTION METHOD

### OPTION A: IB Gateway (RECOMMENDED for 24/7)
**Best for:** Automated trading, runs headless
```
Download: https://www.interactivebrokers.com/en/trading/ibgateway-stable.php
```

### OPTION B: Trader Workstation (TWS)
**Best for:** Manual monitoring + automation
```
Download: https://www.interactivebrokers.com/en/trading/tws.php
```

---

## STEP 3: IB GATEWAY CONFIGURATION

### Installation Settings:
1. Install IB Gateway
2. During setup, choose:
   - **API Settings:** Enable socket connections
   - **Port:** 7497 (Paper) or 7496 (Live)
   - **Read-Only API:** NO (uncheck)
   - **Master Client ID:** 100

### Login Configuration:
```
Username: [Your IB Username]
Password: [Your IB Password]
Trading Mode: Live (or Paper for testing)
```

### API Settings in Gateway:
1. Configure → Settings → API → Settings
2. Settings to apply:
```
✅ Enable ActiveX and Socket EClients
✅ Socket port: 7497 (paper) or 7496 (live)
✅ Allow connections from localhost only: NO (for cloud)
✅ Master API client ID: 100
✅ Create API message log file: YES
✅ Include market data in API log: YES
❌ Read-Only API: NO (must be unchecked)
```

---

## STEP 4: CLOUD DEPLOYMENT SETUP

### For Render Deployment:

#### Option 1: IB Gateway on Separate VPS (BEST)
1. Get a small VPS (DigitalOcean, AWS, etc.)
2. Install IB Gateway on VPS
3. Configure security group:
```
Inbound Rules:
- Port 7496 (Live API)
- Port 7497 (Paper API)
- Source: Your Render service IP (or 0.0.0.0/0 with auth)
```

#### Option 2: Docker Container (Advanced)
```dockerfile
FROM ubuntu:20.04
# Install IB Gateway
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    xvfb \
    default-jre
    
# Download and setup IB Gateway
COPY ibgateway-stable-standalone-linux-x64.sh .
RUN sh ibgateway-stable-standalone-linux-x64.sh -q

EXPOSE 7496 7497
```

---

## STEP 5: ENVIRONMENT VARIABLES FOR RENDER

Add these to your Render service:

```bash
# Interactive Brokers Configuration
IB_HOST=your-vps-ip-address  # Or localhost if using Docker
IB_PORT=7496                  # 7496 for live, 7497 for paper
IB_CLIENT_ID=100             # Must match Gateway setting
IB_ACCOUNT=DU1234567         # Your IB account number

# Optional - for auto-login (encrypted)
IB_USERNAME=your-username
IB_PASSWORD=encrypted-password
IB_TRADING_MODE=live         # or 'paper'

# Market Data
IB_MARKET_DATA_TYPE=1        # 1=Live, 2=Frozen, 3=Delayed, 4=Delayed+Frozen
```

---

## STEP 6: ASX MARKET DATA SUBSCRIPTIONS

### Required Subscriptions:
1. Log into IB Account Management
2. Go to: Settings → User Settings → Market Data Subscriptions
3. Subscribe to:
   - **ASX Total** (for all ASX stocks) ~$38.50/month
   - OR **ASX Level I** (for basic quotes) ~$11.00/month
   - **ASX BookTrader** (optional, for depth) ~$11.00/month

### Important ASX Trading Hours:
```
Pre-Market: 7:00 AM - 10:00 AM Sydney Time
Regular: 10:00 AM - 4:00 PM Sydney Time
Post: 4:00 PM - 5:00 PM Sydney Time
```

---

## STEP 7: CONNECTION TEST

### Test from AuraQuant:
```python
from ib_insync import *

# Connect to IB
ib = IB()
ib.connect('your-vps-ip', 7496, clientId=100)

# Test ASX stock
contract = Stock('BHP', 'ASX', 'AUD')
ticker = ib.reqMktData(contract)
print(f"BHP Price: {ticker.marketPrice()}")

# Place test order (PAPER ACCOUNT ONLY!)
order = MarketOrder('BUY', 100)
trade = ib.placeOrder(contract, order)
```

---

## STEP 8: AURAQUANT INTEGRATION

Your AuraQuant system will automatically:
1. **Detect ASX symbols** (ending in .AX)
2. **Route to Interactive Brokers**
3. **Use IB data feed** for charts
4. **Execute through IB API**
5. **Handle Australian regulations**

### Symbol Format:
- AuraQuant: `BHP.AX`
- IB API: `BHP` (exchange: ASX, currency: AUD)

---

## SECURITY CONSIDERATIONS

### DO's:
✅ Use separate VPS for IB Gateway
✅ Enable 2FA on IB account
✅ Set daily loss limits in IB
✅ Use read-only API for testing
✅ Encrypt credentials in environment
✅ Monitor API connections in IB

### DON'Ts:
❌ Expose Gateway directly to internet
❌ Store IB password in plain text
❌ Share Master Client ID
❌ Disable security features
❌ Use production credentials for testing

---

## TROUBLESHOOTING

### "No security definition found"
- Solution: Check market data subscriptions
- Ensure ASX data is subscribed

### "Not connected"
- Check VPS firewall rules
- Verify Gateway is running
- Check port numbers (7496 vs 7497)

### "Order rejected"
- Check account permissions
- Verify trading hours
- Check buying power

### "No market data"
- Subscribe to ASX data feed
- Check market data type setting
- Verify symbol format

---

## COSTS BREAKDOWN

### Monthly Costs:
- IB Account: $0 (if > $100k balance) or $10/month
- ASX Market Data: ~$11-38/month
- VPS for Gateway: ~$5-20/month
- Total: ~$16-68/month

### Per Trade:
- ASX Stocks: 0.08% (min $6 AUD)
- US Stocks: $0.005 per share (min $1 USD)

---

## QUICK START CHECKLIST

1. ✅ IB account with API enabled
2. ✅ ASX trading permissions
3. ✅ Market data subscriptions
4. ✅ IB Gateway installed (VPS or local)
5. ✅ Port 7496/7497 accessible
6. ✅ Environment variables in Render
7. ✅ Test connection successful
8. ✅ Paper trading tested first

---

## SUPPORT CONTACTS

- IB Technical Support: +61 2 9024 8817 (Australia)
- API Support: api@interactivebrokers.com
- Documentation: https://interactivebrokers.github.io/tws-api/

---

Your Interactive Brokers setup is ready for ASX trading with AuraQuant!