"""
AuraQuant Discord Configuration
The Infinity Money Synthetic Intelligence System
"""

import os

# Discord Application Configuration
DISCORD_APPLICATION_ID = "1406810615099428894"
DISCORD_PUBLIC_KEY = "f05a07c58a82fafde4d51d68ebc2f746e6d08e2e26f457aaa47bd4e384947a83"
DISCORD_CLIENT_ID = "1406810615099428894"

# Discord Webhook URL (to be set in environment or here)
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '')

# Discord Bot Token (if using bot instead of webhook)
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN', '')

# Discord Channel IDs for different alert types
DISCORD_CHANNELS = {
    'trading': os.getenv('DISCORD_TRADING_CHANNEL', ''),
    'alerts': os.getenv('DISCORD_ALERTS_CHANNEL', ''),
    'system': os.getenv('DISCORD_SYSTEM_CHANNEL', ''),
    'profit': os.getenv('DISCORD_PROFIT_CHANNEL', '')
}

# Discord Embed Colors (matching AuraQuant color scheme)
DISCORD_COLORS = {
    'profit': 0x00ff88,  # Neon green for profits
    'loss': 0xff4444,    # Bright red for losses
    'info': 0x131722,    # Dark navy for info
    'warning': 0xffa500,  # Orange for warnings
    'error': 0xff0000,    # Red for errors
    'success': 0x00ff88   # Green for success
}