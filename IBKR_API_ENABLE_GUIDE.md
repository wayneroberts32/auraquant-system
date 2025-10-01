# IBKR API Enable Guide - Step by Step

## 📍 CURRENT STATUS
You're logged into IBKR Account Management

---

## STEP 2: NAVIGATE TO API SETTINGS

Once logged in, follow this path:
1. Click **"Settings"** (gear icon) in top menu
2. Click **"Account Settings"** 
3. On left sidebar, find **"API"**
4. Click **"API Settings"**

---

## STEP 3: ENABLE API TRADING

### Find these settings and ENABLE them:

✅ **Enable ActiveX and Socket Clients**
- Toggle: ON
- This allows external applications to connect

✅ **Download open orders on connection**
- Toggle: ON  
- Shows existing orders when connecting

✅ **Send account window updates**
- Toggle: ON
- Sends position updates to your app

✅ **Master API client ID**
- Enter: `100`
- IMPORTANT: Must be exactly 100

✅ **Create API message log file**
- Toggle: ON (helps with debugging)

❌ **Read-Only API**
- Toggle: OFF (MUST be off to place trades!)

---

## STEP 4: SOCKET PORT CONFIGURATION

Set the following:
- **Socket port for live trading:** `7496`
- **Socket port for paper trading:** `7497`
- **Allow connections from:** `Any IP` (for cloud)

⚠️ If you see "Trusted IPs only":
- Change to "Allow connections from localhost and these IPs"
- Add: `0.0.0.0` (allows any IP with authentication)

---

## STEP 5: API PRECAUTIONS

Review these settings (usually already set):

### Order Precautions:
- **Percentage change:** 5% (prevents fat finger errors)
- **Total value limit:** Set your comfort level
- **Trade size limit:** Set max shares/contracts

### These are SAFETY features - keep them!

---

## STEP 6: SAVE SETTINGS

1. Click **"Continue"** at bottom
2. Review changes
3. Click **"Save Settings"**
4. You may need to re-authenticate

---

## STEP 7: CHECK TRADING PERMISSIONS

While in Account Management, also verify:

### Go to: Settings → Account Settings → Trading Permissions

Ensure you have:
- ✅ **Stocks** - Australia (for ASX)
- ✅ **Stocks** - United States  
- ✅ **Market Data Subscriptions** - ASX Level 1

If missing ASX permissions:
1. Click "Request Trading Permissions"
2. Select "Stocks - Australia"
3. Submit request (usually instant approval)

---

## STEP 8: MARKET DATA SUBSCRIPTIONS

### Go to: Settings → User Settings → Market Data Subscriptions

Subscribe to (if not already):
- **ASX Level 1** (~$11/month) - Basic quotes
- **ASX Level 2** (~$38/month) - Full depth (optional)

💡 Start with Level 1, upgrade if needed

---

## STEP 9: NOTE YOUR ACCOUNT DETAILS

Find and save these:
- **Account Number:** (e.g., U1234567 or DU1234567)
- **Username:** (for IB Gateway login)
- Paper Account (if available): Usually DU prefix

---

## STEP 10: DOWNLOAD IB GATEWAY

Now download IB Gateway:
1. Go to: https://www.interactivebrokers.com/en/trading/ibgateway-stable.php
2. Download **"IB Gateway Stable"** for Windows
3. Install with default settings

---

## 🎯 SETTINGS SUMMARY

After completing all steps, you should have:
```
✅ API Trading: ENABLED
✅ Socket Clients: ENABLED  
✅ Master Client ID: 100
✅ Read-Only: DISABLED (OFF)
✅ Socket Port (Live): 7496
✅ Socket Port (Paper): 7497
✅ ASX Permissions: ENABLED
✅ Market Data: ASX Level 1
```

---

## 🚀 NEXT STEPS

### For Testing (Recommended):
1. Install IB Gateway on your PC
2. Login with PAPER account (if available)
3. Test connection locally first

### For Production:
1. Get a VPS ($5-20/month)
2. Install IB Gateway on VPS
3. Configure for 24/7 operation

---

## ⚠️ IMPORTANT NOTES

1. **Changes take 24 hours** - Some settings may need overnight processing
2. **Paper Account** - If you have one (DU prefix), test there first
3. **Minimum Balance** - IBKR requires $10,000 USD minimum (or equivalent)
4. **Monthly Fees** - $10/month if balance < $100,000 (waived if > $10 commissions)

---

## 🆘 TROUBLESHOOTING

### "API not enabled" error:
- Wait 24 hours after enabling
- Log out and back into account management
- Clear browser cache

### "No market data" error:
- Check ASX subscription active
- Verify account funded
- Market data takes 15 min to activate

### "Connection refused":
- Check IB Gateway is running
- Verify port numbers (7496 vs 7497)
- Check firewall settings

---

## 📞 SUPPORT

IBKR Australia Support: +61 2 9024 8817
Hours: Monday-Friday, 8:00 AM - 6:00 PM Sydney time

---

Your IBKR API is being configured! Continue with the steps above.