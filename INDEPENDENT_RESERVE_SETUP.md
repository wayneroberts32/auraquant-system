# Independent Reserve API Configuration for AuraQuant

## API KEY SETUP ANSWERS:

### 1. API KEY Description
**Enter:** `AuraQuant Trading System`

### 2. Restrict API key to IP Address
**Answer:** `NO` - Leave this field EMPTY
- ⚠️ **DO NOT add IP restriction**

## WHY NO IP RESTRICTION?

### Cloud Deployment Reality:
- **Render.com uses dynamic IP addresses**
- IP changes every time your service restarts
- IP changes when scaling or redeploying
- Cloudflare also uses rotating IPs

### What Happens If You Restrict IP:
❌ Your bot gets blocked immediately
❌ "Unauthorized" errors on all trades
❌ System can't connect to Independent Reserve
❌ You'd need to update IP daily (impossible)

## SECURITY WITHOUT IP RESTRICTION:

### 1. Use API Permissions (SAFER):
```
✅ Read Account Information
✅ Read Orders
✅ Place Orders  
✅ Cancel Orders
✅ Read Trade History
❌ Withdraw Funds (NEVER ENABLE)
```

### 2. Additional Security Measures:
- Store API keys in Render environment variables
- Use encrypted connections (HTTPS/WSS)
- Enable 2FA on your Independent Reserve account
- Set daily trading limits in account settings
- Monitor API usage in Independent Reserve dashboard

## AFTER CREATING API KEY:

### 1. You'll receive:
- **API Key:** (public identifier)
- **API Secret:** (private key - KEEP SAFE)

### 2. Add to Render Environment Variables:
```bash
INDEPENDENT_RESERVE_API_KEY=your_api_key_here
INDEPENDENT_RESERVE_API_SECRET=your_secret_here
INDEPENDENT_RESERVE_ACCOUNT_ID=your_account_id
```

### 3. Test Connection:
After deployment, the system will automatically:
- Connect to Independent Reserve
- Verify API credentials
- Start receiving AUD crypto prices
- Enable trading for Australian users

## SUPPORTED PAIRS ON INDEPENDENT RESERVE:
- BTC/AUD (Bitcoin)
- ETH/AUD (Ethereum)
- XRP/AUD (Ripple)
- USDT/AUD (Tether)
- USDC/AUD (USD Coin)
- And more...

## INTEGRATION WITH AURAQUANT:

Your system will automatically:
1. Detect AUD pairs → Route to Independent Reserve
2. Detect USD pairs → Route to Binance/Coinbase
3. Smart order routing for best prices
4. Compliance with Australian regulations

## API RATE LIMITS:
- Independent Reserve: 1 request per second
- AuraQuant handles this automatically
- Built-in rate limiting protection

## TROUBLESHOOTING:

### If "IP not whitelisted" error:
✅ Solution: Remove IP restriction from API settings

### If "Insufficient permissions" error:
✅ Solution: Enable required permissions in API settings

### If "Invalid signature" error:
✅ Solution: Check API secret in Render environment

## IMPORTANT NOTES:
1. **NEVER share your API Secret**
2. **NEVER enable Withdraw permission**
3. **ALWAYS use environment variables**
4. **TEST with small amounts first**

## SUMMARY:
- **Description:** `AuraQuant Trading System`
- **IP Restriction:** `NONE (leave empty)`
- **Permissions:** Trading only, NO withdrawals
- **Storage:** Render environment variables

Your Independent Reserve API is now ready for cloud deployment!