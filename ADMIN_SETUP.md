# AuraQuant Admin & System Configuration

## 1. ADMIN USER SETUP
After deployment, you'll need to set yourself as admin:

### MongoDB Admin User Creation
```javascript
// Add this to your MongoDB database
{
  username: "wayneroberts32",
  email: "wayneroberts32@gmail.com",
  role: "ADMIN",
  permissions: ["ALL"],
  isActive: true,
  createdAt: new Date(),
  settings: {
    defaultBroker: "INTERACTIVE_BROKERS",
    defaultMarket: "ASX",
    theme: "dark",
    multiTabEnabled: true
  }
}
```

### First Login Credentials
- Username: wayneroberts32
- Default Password: AuraQuant2025! (change immediately)
- Admin Access Code: AURAQUANT-MASTER-2025

## 2. BROKER CONFIGURATION & CHARTS

### Default Broker Hierarchy
The system selects brokers based on symbol:
- **ASX Symbols** (e.g., BHP.AX, CBA.AX) → Interactive Brokers
- **Crypto** (e.g., BTC-USDT, ETH-USDT) → Binance/Coinbase
- **Meme Coins** → Uniswap/PancakeSwap
- **US Stocks** → Alpaca/Interactive Brokers

### Chart Data Sources
```python
# Priority order in backend/data_feeds/market_data_manager.py
1. Live broker data (when API keys configured)
2. Backup data providers (Yahoo Finance, Alpha Vantage)
3. TradingView widget (fallback only)
```

### Broker API Configuration
Add these to Render environment variables:
```
# Interactive Brokers (PRIMARY - LIVE & PAPER)
IBKR_ACCOUNT_LIVE=U21613612
IBKR_ACCOUNT_PAPER=DUM547451
IBKR_HOST=127.0.0.1  # Will use tunnel/VPS IP for cloud
IBKR_PORT_LIVE=4001
IBKR_PORT_PAPER=4002  # Currently active for testing
IBKR_CLIENT_ID=1
IBKR_GATEWAY_STATUS=CONFIGURED_AND_TESTED ✅

# Independent Reserve (Crypto)
IR_API_KEY=ec3c43d7-bb41-4da8-b5cd-c464e754ccec
IR_SECRET=aa988d4eede6431591ebbad1f18fb1c1

# Binance (Crypto)
BINANCE_API_KEY=t2IeL6n2H05aSYJiCizIoReqlQU9cThwltCSvTpBfchWGUo79dK5LJtJhbbfQa70
BINANCE_SECRET=uMsThZIQzn08Nnveyilham0qJYGIZwCTs89SvRF8yce12gUmDsS1bQRwLvYrfhys

# Coinbase
COINBASE_API_KEY=cxakp_wKsNoGbJx4sephpsFZ71vV
COINBASE_API_SECRET=PZjohZuyqRx5VsjMqtN9k9

# Alpaca (US Stocks backup)
ALPACA_API_ENDPOINT=https://paper-api.alpaca.markets/v2
ALPACA_API_KEY=PKKU0X6TZ1QEUUTX0RVQ
ALPACA_SECRET_KEY=cbwy35qhIGILXIY0GRme739c52E6Sk84uJPXrRTA

# Telagram:
t.me/Wayno_Rob_TradingBot
API=8186673555:AAEZx3hK7kOYOXPQMqOw3ciZlXG2BW_WJnI
TELEGRAM_CHAT_ID=6995384125

# Discord:
API=1406810615099428894
Public Key: f05a07c58a82fafde4d51d68ebc2f746e6d08e2e26f457aaa47bd4e384947a83
Client ID: 1406810615099428894

```

## 3. TECHNICAL INDICATORS (RSI, MACD, etc.)

### ✅ ALL INDICATORS PRESERVED
Your system includes all indicators in:
- `backend/indicators/technical_indicators.py`
- `backend/indicators/extended_indicators.py`

### Available Indicators:
- **Momentum**: RSI, MACD, Stochastic, Williams %R, ROC
- **Trend**: Moving Averages (SMA, EMA, WMA), ADX, Parabolic SAR
- **Volatility**: Bollinger Bands, ATR, Keltner Channels
- **Volume**: OBV, Volume Profile, VWAP
- **Custom**: Your proprietary indicators

### Indicator Display Control
```javascript
// frontend/pages/main-trading-dashboard.html
indicatorSettings: {
  RSI: { enabled: true, period: 14, overbought: 70, oversold: 30 },
  MACD: { enabled: true, fast: 12, slow: 26, signal: 9 },
  BollingerBands: { enabled: true, period: 20, std: 2 },
  // Add any indicator
}
```

## 4. TRADINGVIEW AS FALLBACK

### Data Source Priority
```javascript
// System automatically selects:
1. Live Broker Data (PRIMARY)
   - Real-time from connected brokers
   - Lowest latency
   - Most accurate

2. Direct API Data (SECONDARY)  
   - Yahoo Finance for ASX
   - CCXT for Crypto
   - Alpha Vantage for US

3. TradingView Widget (FALLBACK ONLY)
   - Used when APIs unavailable
   - Display-only mode
   - No execution through widget
```

### Force Broker Data Mode
```javascript
// In frontend settings
dataSourceMode: "BROKER_ONLY"  // Never use TradingView
dataSourceMode: "AUTO"          // Smart selection (default)
dataSourceMode: "TRADINGVIEW"   // Force TradingView (testing only)
```

## 5. POST-DEPLOYMENT SETUP CHECKLIST

### Immediate Actions (After Deploy):
1. ✅ Access admin panel: https://auraquant-frontend.pages.dev/pages/admin-users.html
2. ✅ Create your admin account
3. ✅ Add broker API keys in Render environment
4. ✅ Configure default broker preferences
5. ✅ Set up 2FA for admin account
6. ✅ Test emergency kill switch

### Broker Setup Order:
1. **Interactive Brokers** (for ASX) - Primary
2. **Binance** (for Crypto) - Primary
3. **Alpaca** (for US stocks) - Optional
4. **Coinbase** (crypto backup) - Optional

### Chart Configuration:
- Charts auto-switch data source based on symbol
- ASX symbols → IB data
- Crypto symbols → Binance/CCXT data
- Fallback to TradingView only if APIs fail

## 6. RISK MANAGEMENT & SAFETY

### ⚠️ ZERO BALANCE PROTECTION
The system includes **AUTOMATIC PROTECTION** against trading with insufficient funds:

```python
# Built-in Risk Manager Features:
1. ❌ BLOCKS all trades if balance = $0
2. ❌ BLOCKS trades if balance < $100 (configurable)
3. ❌ BLOCKS trades exceeding 10% of portfolio
4. ❌ BLOCKS trades after 2% daily loss
5. ⚠️ WARNS on 3+ consecutive losses
6. ⚠️ WARNS on high concentration (>20% in one symbol)
7. ❌ EMERGENCY STOP available (manual trigger)
```

### Risk Settings (Configurable)
```bash
# Risk Management Settings
MIN_ACCOUNT_BALANCE=100  # Minimum to trade
MAX_POSITION_SIZE_PCT=0.10  # 10% max per position
MAX_DAILY_LOSS_PCT=0.02  # 2% daily loss limit
MAX_TRADES_PER_DAY=50  # Daily trade limit
MAX_LEVERAGE=2.0  # Maximum leverage
ENABLE_RISK_MANAGER=true  # Always keep enabled!
```

### Paper Trading Mode (SAFE TESTING)
```bash
# Currently configured for PAPER TRADING
IBKR_PORT=4002  # Paper trading port
IBKR_ACCOUNT=DUM547451  # Paper account
PAPER_TRADING_BALANCE=$1,003,755.62  # Your test balance
```

## 7. DEPLOYMENT TO RENDER

### Step 1: Local Setup (REQUIRED FIRST)
```bash
1. Start IBKR Gateway (paper mode, port 4002) ✅ DONE
2. Test locally: python start_api.py
3. Verify connection: python test_ibkr_connection.py ✅ DONE
4. Check balance > $0 in paper account ✅ DONE ($1M+)
```

### Step 2: Deploy to Render
```bash
# Push to GitHub
git add .
git commit -m "IBKR integration with risk management"
git push origin main

# Render will auto-deploy
```

### Step 3: Bridge Local Gateway ↔ Cloud
Since IBKR Gateway must run locally:

**Option A: ngrok (Quick Testing)**
```bash
ngrok tcp 4002
# Copy the URL (e.g., tcp://2.tcp.ngrok.io:12345)
# Update IBKR_HOST in Render to this URL
```

**Option B: VPS (Production)**
```bash
# Get a Windows VPS
# Install IBKR Gateway on VPS
# Use VPS IP as IBKR_HOST in Render
```

## 8. ADMIN ENVIRONMENT VARIABLES

Add these to Render AFTER deployment:
```bash
# Admin Configuration
ADMIN_EMAIL=wayneroberts32@gmail.com
ADMIN_USERNAME=wayneroberts32
MASTER_KEY=generate-secure-key-here
JWT_SECRET=generate-another-secure-key

# Default Settings
DEFAULT_BROKER=INTERACTIVE_BROKERS
DEFAULT_MARKET=ASX
ENABLE_PAPER_TRADING=true
ENABLE_LIVE_TRADING=false  # Enable after testing

# Data Sources
USE_TRADINGVIEW_FALLBACK=true
PRIMARY_DATA_SOURCE=BROKER
```

## IMPORTANT NOTES:
- Admin account creation happens AFTER deployment
- Broker APIs are configured in Render environment
- Charts automatically select appropriate data source
- All technical indicators are included and active
- TradingView is fallback only, not primary source