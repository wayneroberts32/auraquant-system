"""
AuraQuant Notification Manager
The Infinity Money Synthetic Intelligence System
Multi-channel notification system: Telegram, Discord, SMS, Email
"""

import os
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

class NotificationManager:
    """
    Manages all notification channels for AuraQuant
    Telegram, Discord, SMS (via Twilio), Email
    """
    
    def __init__(self):
        # Telegram Configuration - AuraQuant Trading Bot
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '8186673555:AAEZx3hK7kOYOXPQMqOw3ciZlXG2BW_WJnI')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID', '6995384125')
        
        # Discord Configuration
        self.discord_webhook_url = os.getenv('DISCORD_WEBHOOK_URL', '')
        
        # Twilio SMS Configuration
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID', '')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN', '')
        self.twilio_from_number = os.getenv('TWILIO_FROM_NUMBER', '')
        self.twilio_to_numbers = os.getenv('TWILIO_TO_NUMBERS', '').split(',')
        
        # Email Configuration
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.email_from = os.getenv('EMAIL_FROM', 'auraquant@notifications.com')
        self.email_to = os.getenv('EMAIL_TO', '').split(',')
        
        self.session = None
        
    async def initialize(self):
        """Initialize async session"""
        self.session = aiohttp.ClientSession()
        print("✅ AuraQuant Notification Manager initialized")
        
    async def close(self):
        """Close async session"""
        if self.session:
            await self.session.close()
    
    async def send_telegram(self, message: str, parse_mode: str = "HTML") -> bool:
        """Send notification via Telegram"""
        if not self.telegram_bot_token or not self.telegram_chat_id:
            print("⚠️ Telegram not configured")
            return False
            
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            data = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    print("✅ Telegram notification sent")
                    return True
                else:
                    print(f"❌ Telegram error: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Telegram exception: {e}")
            return False
    
    async def send_discord(self, message: str, embed: Optional[Dict] = None) -> bool:
        """Send notification via Discord webhook"""
        if not self.discord_webhook_url:
            print("⚠️ Discord not configured")
            return False
            
        try:
            data = {"content": message}
            if embed:
                data["embeds"] = [embed]
            
            async with self.session.post(self.discord_webhook_url, json=data) as response:
                if response.status in [200, 204]:
                    print("✅ Discord notification sent")
                    return True
                else:
                    print(f"❌ Discord error: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Discord exception: {e}")
            return False
    
    async def send_sms(self, message: str) -> bool:
        """Send SMS via Twilio"""
        if not all([self.twilio_account_sid, self.twilio_auth_token, self.twilio_from_number]):
            print("⚠️ Twilio SMS not configured")
            return False
            
        try:
            from twilio.rest import Client
            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            
            for to_number in self.twilio_to_numbers:
                if to_number:
                    message = client.messages.create(
                        body=message,
                        from_=self.twilio_from_number,
                        to=to_number.strip()
                    )
                    print(f"✅ SMS sent to {to_number}: {message.sid}")
            return True
        except Exception as e:
            print(f"❌ SMS exception: {e}")
            return False
    
    def send_email(self, subject: str, message: str, html: bool = False) -> bool:
        """Send email notification"""
        if not all([self.smtp_user, self.smtp_password, self.email_to]):
            print("⚠️ Email not configured")
            return False
            
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_from
            msg['To'] = ', '.join(self.email_to)
            
            if html:
                part = MIMEText(message, 'html')
            else:
                part = MIMEText(message, 'plain')
            msg.attach(part)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            print(f"✅ Email sent to {self.email_to}")
            return True
        except Exception as e:
            print(f"❌ Email exception: {e}")
            return False
    
    async def send_trading_alert(
        self,
        alert_type: str,
        symbol: str,
        action: str,
        price: float,
        quantity: int,
        reason: str,
        profit_loss: Optional[float] = None
    ):
        """Send trading alert to all channels"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Format message for different channels
        telegram_msg = f"""
<b>🚨 AuraQuant Trading Alert</b>
<b>Type:</b> {alert_type}
<b>Symbol:</b> {symbol}
<b>Action:</b> {action}
<b>Price:</b> ${price:.2f}
<b>Quantity:</b> {quantity}
<b>Reason:</b> {reason}
{f'<b>P/L:</b> ${profit_loss:.2f}' if profit_loss else ''}
<b>Time:</b> {timestamp}
"""
        
        discord_embed = {
            "title": "🚨 AuraQuant Trading Alert",
            "color": 0x00ff88 if profit_loss and profit_loss > 0 else 0xff4444,
            "fields": [
                {"name": "Type", "value": alert_type, "inline": True},
                {"name": "Symbol", "value": symbol, "inline": True},
                {"name": "Action", "value": action, "inline": True},
                {"name": "Price", "value": f"${price:.2f}", "inline": True},
                {"name": "Quantity", "value": str(quantity), "inline": True},
                {"name": "Reason", "value": reason, "inline": False}
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if profit_loss:
            discord_embed["fields"].append({
                "name": "P/L", "value": f"${profit_loss:.2f}", "inline": True
            })
        
        sms_msg = f"AuraQuant: {action} {quantity} {symbol} @ ${price:.2f}. {reason}"
        if profit_loss:
            sms_msg += f" P/L: ${profit_loss:.2f}"
        
        email_subject = f"AuraQuant Trading Alert: {action} {symbol}"
        
        # Send to all channels
        tasks = [
            self.send_telegram(telegram_msg),
            self.send_discord("", discord_embed),
            self.send_sms(sms_msg),
            asyncio.to_thread(self.send_email, email_subject, telegram_msg.replace('<b>', '').replace('</b>', ''))
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for r in results if r is True)
        print(f"📨 Alert sent to {success_count}/4 channels")
        
        return success_count > 0
    
    async def send_system_alert(self, level: str, message: str, details: Optional[Dict] = None):
        """Send system-level alerts"""
        emoji_map = {
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "SUCCESS": "✅",
            "CRITICAL": "🔴"
        }
        
        emoji = emoji_map.get(level, "📢")
        
        formatted_msg = f"{emoji} AuraQuant System Alert [{level}]\n{message}"
        
        if details:
            formatted_msg += "\nDetails: " + json.dumps(details, indent=2)
        
        tasks = [
            self.send_telegram(formatted_msg),
            self.send_discord(formatted_msg)
        ]
        
        if level in ["ERROR", "CRITICAL"]:
            tasks.append(self.send_sms(f"AuraQuant {level}: {message[:100]}"))
            tasks.append(asyncio.to_thread(
                self.send_email, 
                f"AuraQuant {level} Alert", 
                formatted_msg
            ))
        
        await asyncio.gather(*tasks, return_exceptions=True)

# Singleton instance
notification_manager = NotificationManager()

async def get_notification_manager():
    """Get notification manager instance"""
    if not notification_manager.session:
        await notification_manager.initialize()
    return notification_manager