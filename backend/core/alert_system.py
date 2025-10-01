#!/usr/bin/env python3
"""
AuraQuant Multi-Channel Alert & Notification System
Engineer's Note: Comprehensive alert system with Telegram, Discord, Email, SMS
Handles all system alerts, trading signals, and critical notifications
"""

import os
import json
import asyncio
import smtplib
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertPriority(Enum):
    """Alert priority levels"""
    LOW = "low"           # Informational only
    MEDIUM = "medium"     # Important but not urgent
    HIGH = "high"         # Urgent attention needed
    CRITICAL = "critical" # Immediate action required
    EMERGENCY = "emergency" # System failure/critical loss

class AlertChannel(Enum):
    """Available communication channels"""
    TELEGRAM = "telegram"
    DISCORD = "discord"
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    PUSH = "push"
    ALL = "all"

@dataclass
class Alert:
    """Alert data structure"""
    id: str
    title: str
    message: str
    priority: AlertPriority
    category: str
    data: Dict[str, Any]
    timestamp: datetime
    channels: List[AlertChannel]

class TelegramNotifier:
    """Telegram notification handler"""
    
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_ids = os.getenv("TELEGRAM_CHAT_IDS", "").split(",")
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.enabled = bool(self.bot_token)
        
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert via Telegram"""
        if not self.enabled:
            logger.warning("Telegram notifications not configured")
            return False
            
        try:
            # Format message with Telegram markdown
            message = self._format_message(alert)
            
            async with aiohttp.ClientSession() as session:
                for chat_id in self.chat_ids:
                    if not chat_id:
                        continue
                        
                    url = f"{self.base_url}/sendMessage"
                    payload = {
                        "chat_id": chat_id.strip(),
                        "text": message,
                        "parse_mode": "Markdown",
                        "disable_web_page_preview": True
                    }
                    
                    async with session.post(url, json=payload) as response:
                        if response.status == 200:
                            logger.info(f"Telegram alert sent to {chat_id}")
                        else:
                            logger.error(f"Failed to send Telegram alert: {response.status}")
                            
            return True
            
        except Exception as e:
            logger.error(f"Telegram send error: {e}")
            return False
            
    def _format_message(self, alert: Alert) -> str:
        """Format alert for Telegram"""
        priority_emoji = {
            AlertPriority.LOW: "ℹ️",
            AlertPriority.MEDIUM: "⚠️",
            AlertPriority.HIGH: "🚨",
            AlertPriority.CRITICAL: "🔴",
            AlertPriority.EMERGENCY: "🆘"
        }
        
        emoji = priority_emoji.get(alert.priority, "📢")
        
        message = f"""
{emoji} *{alert.title}*

{alert.message}

📊 Category: {alert.category}
⏰ Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
🎯 Priority: {alert.priority.value.upper()}
"""
        
        # Add data if present
        if alert.data:
            message += "\n📈 *Details:*\n"
            for key, value in alert.data.items():
                message += f"• {key}: `{value}`\n"
                
        message += "\n_AuraQuant AI Trading System_"
        
        return message

class DiscordNotifier:
    """Discord notification handler"""
    
    def __init__(self):
        self.webhook_urls = os.getenv("DISCORD_WEBHOOK_URLS", "").split(",")
        self.enabled = bool(self.webhook_urls[0] if self.webhook_urls else False)
        
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert via Discord webhook"""
        if not self.enabled:
            logger.warning("Discord notifications not configured")
            return False
            
        try:
            # Create Discord embed
            embed = self._create_embed(alert)
            
            async with aiohttp.ClientSession() as session:
                for webhook_url in self.webhook_urls:
                    if not webhook_url:
                        continue
                        
                    payload = {
                        "username": "AuraQuant Bot",
                        "avatar_url": "https://example.com/auraquant-logo.png",
                        "embeds": [embed]
                    }
                    
                    async with session.post(webhook_url.strip(), json=payload) as response:
                        if response.status in [200, 204]:
                            logger.info("Discord alert sent successfully")
                        else:
                            logger.error(f"Failed to send Discord alert: {response.status}")
                            
            return True
            
        except Exception as e:
            logger.error(f"Discord send error: {e}")
            return False
            
    def _create_embed(self, alert: Alert) -> Dict:
        """Create Discord embed for alert"""
        colors = {
            AlertPriority.LOW: 0x3498db,      # Blue
            AlertPriority.MEDIUM: 0xf39c12,   # Orange
            AlertPriority.HIGH: 0xe74c3c,     # Red
            AlertPriority.CRITICAL: 0x992d22, # Dark Red
            AlertPriority.EMERGENCY: 0xff0000 # Bright Red
        }
        
        embed = {
            "title": f"🚨 {alert.title}",
            "description": alert.message,
            "color": colors.get(alert.priority, 0x00ff88),
            "timestamp": alert.timestamp.isoformat(),
            "footer": {
                "text": "AuraQuant AI Trading System"
            },
            "fields": [
                {
                    "name": "Priority",
                    "value": alert.priority.value.upper(),
                    "inline": True
                },
                {
                    "name": "Category",
                    "value": alert.category,
                    "inline": True
                }
            ]
        }
        
        # Add data fields
        if alert.data:
            for key, value in list(alert.data.items())[:5]:  # Limit to 5 fields
                embed["fields"].append({
                    "name": key.replace("_", " ").title(),
                    "value": str(value),
                    "inline": True
                })
                
        return embed

class EmailNotifier:
    """Email notification handler"""
    
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_username)
        self.to_emails = os.getenv("TO_EMAILS", "").split(",")
        self.enabled = bool(self.smtp_username and self.smtp_password)
        
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert via email"""
        if not self.enabled:
            logger.warning("Email notifications not configured")
            return False
            
        try:
            # Create email message
            msg = self._create_email(alert)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                
                for to_email in self.to_emails:
                    if not to_email:
                        continue
                        
                    msg["To"] = to_email.strip()
                    server.send_message(msg)
                    logger.info(f"Email alert sent to {to_email}")
                    
            return True
            
        except Exception as e:
            logger.error(f"Email send error: {e}")
            return False
            
    def _create_email(self, alert: Alert) -> MIMEMultipart:
        """Create email message for alert"""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[{alert.priority.value.upper()}] {alert.title}"
        msg["From"] = self.from_email
        
        # Create HTML content
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h1 style="color: #00ff88; border-bottom: 2px solid #00ff88; padding-bottom: 10px;">
                    AuraQuant Alert System
                </h1>
                
                <h2 style="color: #333;">{alert.title}</h2>
                
                <div style="background: #f9f9f9; padding: 15px; border-left: 4px solid #00ff88; margin: 20px 0;">
                    <p style="margin: 0; color: #555;">{alert.message}</p>
                </div>
                
                <table style="width: 100%; margin: 20px 0;">
                    <tr>
                        <td style="padding: 8px; background: #f0f0f0;"><strong>Priority:</strong></td>
                        <td style="padding: 8px;">{alert.priority.value.upper()}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; background: #f0f0f0;"><strong>Category:</strong></td>
                        <td style="padding: 8px;">{alert.category}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; background: #f0f0f0;"><strong>Time:</strong></td>
                        <td style="padding: 8px;">{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td>
                    </tr>
                </table>
        """
        
        if alert.data:
            html_content += """
                <h3 style="color: #333; margin-top: 20px;">Additional Details</h3>
                <table style="width: 100%; border-collapse: collapse;">
            """
            for key, value in alert.data.items():
                html_content += f"""
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background: #f9f9f9;">
                            <strong>{key.replace('_', ' ').title()}:</strong>
                        </td>
                        <td style="padding: 8px; border: 1px solid #ddd;">
                            {value}
                        </td>
                    </tr>
                """
            html_content += "</table>"
            
        html_content += """
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #999;">
                    <p>AuraQuant AI Trading System - Automated Alert</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Attach HTML content
        msg.attach(MIMEText(html_content, "html"))
        
        return msg

class SMSNotifier:
    """SMS notification handler using Twilio"""
    
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER", "")
        self.to_numbers = os.getenv("SMS_TO_NUMBERS", "").split(",")
        self.enabled = bool(self.account_sid and self.auth_token)
        
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert via SMS"""
        if not self.enabled:
            logger.warning("SMS notifications not configured")
            return False
            
        try:
            # Import Twilio client (optional dependency)
            from twilio.rest import Client
            
            client = Client(self.account_sid, self.auth_token)
            
            # Format SMS message (160 char limit)
            message = self._format_sms(alert)
            
            for to_number in self.to_numbers:
                if not to_number:
                    continue
                    
                try:
                    message = client.messages.create(
                        body=message,
                        from_=self.from_number,
                        to=to_number.strip()
                    )
                    logger.info(f"SMS alert sent to {to_number}: {message.sid}")
                except Exception as e:
                    logger.error(f"Failed to send SMS to {to_number}: {e}")
                    
            return True
            
        except ImportError:
            logger.error("Twilio library not installed. Run: pip install twilio")
            return False
        except Exception as e:
            logger.error(f"SMS send error: {e}")
            return False
            
    def _format_sms(self, alert: Alert) -> str:
        """Format alert for SMS (160 char limit)"""
        priority_symbol = {
            AlertPriority.LOW: "INFO",
            AlertPriority.MEDIUM: "WARN",
            AlertPriority.HIGH: "ALERT",
            AlertPriority.CRITICAL: "CRITICAL",
            AlertPriority.EMERGENCY: "EMERGENCY"
        }
        
        symbol = priority_symbol.get(alert.priority, "ALERT")
        
        # Truncate message if needed
        max_msg_len = 140 - len(symbol) - len(alert.title)
        truncated_msg = alert.message[:max_msg_len] + "..." if len(alert.message) > max_msg_len else alert.message
        
        return f"[{symbol}] {alert.title}: {truncated_msg}"

class AuraQuantAlertSystem:
    """
    Master alert system that manages all notification channels
    """
    
    def __init__(self):
        """Initialize all notification channels"""
        self.telegram = TelegramNotifier()
        self.discord = DiscordNotifier()
        self.email = EmailNotifier()
        self.sms = SMSNotifier()
        
        self.alert_history = []
        self.alert_queue = asyncio.Queue()
        self.running = False
        
        # Channel routing based on priority
        self.priority_routing = {
            AlertPriority.LOW: [AlertChannel.DISCORD],
            AlertPriority.MEDIUM: [AlertChannel.DISCORD, AlertChannel.TELEGRAM],
            AlertPriority.HIGH: [AlertChannel.TELEGRAM, AlertChannel.EMAIL, AlertChannel.DISCORD],
            AlertPriority.CRITICAL: [AlertChannel.ALL],
            AlertPriority.EMERGENCY: [AlertChannel.ALL]
        }
        
        # Rate limiting
        self.rate_limits = {}
        self.rate_limit_window = 60  # seconds
        self.rate_limit_max = 10  # max alerts per window
        
    async def send_alert(self, 
                        title: str, 
                        message: str,
                        priority: AlertPriority = AlertPriority.MEDIUM,
                        category: str = "System",
                        data: Dict[str, Any] = None,
                        channels: List[AlertChannel] = None) -> bool:
        """
        Send alert through specified channels
        
        Args:
            title: Alert title
            message: Alert message
            priority: Alert priority level
            category: Alert category (Trading, System, Risk, etc.)
            data: Additional data to include
            channels: Specific channels to use (None = auto-route by priority)
            
        Returns:
            Success status
        """
        
        # Check rate limiting
        if not self._check_rate_limit(category):
            logger.warning(f"Rate limit exceeded for category: {category}")
            return False
            
        # Create alert object
        alert = Alert(
            id=self._generate_alert_id(),
            title=title,
            message=message,
            priority=priority,
            category=category,
            data=data or {},
            timestamp=datetime.now(),
            channels=channels or self._get_channels_for_priority(priority)
        )
        
        # Add to queue
        await self.alert_queue.put(alert)
        
        # Process immediately if not running background processor
        if not self.running:
            return await self._process_alert(alert)
            
        return True
        
    async def _process_alert(self, alert: Alert) -> bool:
        """Process single alert through all channels"""
        success = False
        results = {}
        
        # Process through each channel
        if AlertChannel.ALL in alert.channels or AlertChannel.TELEGRAM in alert.channels:
            results['telegram'] = await self.telegram.send_alert(alert)
            
        if AlertChannel.ALL in alert.channels or AlertChannel.DISCORD in alert.channels:
            results['discord'] = await self.discord.send_alert(alert)
            
        if AlertChannel.ALL in alert.channels or AlertChannel.EMAIL in alert.channels:
            results['email'] = await self.email.send_alert(alert)
            
        if AlertChannel.ALL in alert.channels or AlertChannel.SMS in alert.channels:
            results['sms'] = await self.sms.send_alert(alert)
            
        # Store in history
        alert_record = {
            'alert': alert,
            'results': results,
            'timestamp': datetime.now()
        }
        self.alert_history.append(alert_record)
        
        # Keep history limited
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
            
        success = any(results.values())
        
        if success:
            logger.info(f"Alert sent successfully: {alert.title}")
        else:
            logger.error(f"Failed to send alert: {alert.title}")
            
        return success
        
    async def start_background_processor(self):
        """Start background alert processor"""
        self.running = True
        
        while self.running:
            try:
                # Wait for alerts with timeout
                alert = await asyncio.wait_for(self.alert_queue.get(), timeout=1.0)
                await self._process_alert(alert)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Alert processor error: {e}")
                
    def stop_background_processor(self):
        """Stop background alert processor"""
        self.running = False
        
    def _check_rate_limit(self, category: str) -> bool:
        """Check if rate limit allows sending alert"""
        now = datetime.now()
        
        if category not in self.rate_limits:
            self.rate_limits[category] = []
            
        # Remove old entries
        cutoff = now - timedelta(seconds=self.rate_limit_window)
        self.rate_limits[category] = [
            t for t in self.rate_limits[category] if t > cutoff
        ]
        
        # Check limit
        if len(self.rate_limits[category]) >= self.rate_limit_max:
            return False
            
        # Add current timestamp
        self.rate_limits[category].append(now)
        return True
        
    def _get_channels_for_priority(self, priority: AlertPriority) -> List[AlertChannel]:
        """Get default channels based on priority"""
        return self.priority_routing.get(priority, [AlertChannel.DISCORD])
        
    def _generate_alert_id(self) -> str:
        """Generate unique alert ID"""
        from uuid import uuid4
        return f"ALERT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid4())[:8]}"
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get alert system statistics"""
        total_alerts = len(self.alert_history)
        
        by_priority = {}
        by_category = {}
        by_channel = {}
        success_rate = 0
        
        if self.alert_history:
            for record in self.alert_history:
                alert = record['alert']
                results = record['results']
                
                # Count by priority
                priority = alert.priority.value
                by_priority[priority] = by_priority.get(priority, 0) + 1
                
                # Count by category
                category = alert.category
                by_category[category] = by_category.get(category, 0) + 1
                
                # Count by channel success
                for channel, success in results.items():
                    if success:
                        by_channel[channel] = by_channel.get(channel, 0) + 1
                        
            # Calculate success rate
            successful = sum(1 for r in self.alert_history if any(r['results'].values()))
            success_rate = (successful / total_alerts) * 100 if total_alerts > 0 else 0
            
        return {
            'total_alerts': total_alerts,
            'by_priority': by_priority,
            'by_category': by_category,
            'by_channel': by_channel,
            'success_rate': f"{success_rate:.1f}%",
            'channels_enabled': {
                'telegram': self.telegram.enabled,
                'discord': self.discord.enabled,
                'email': self.email.enabled,
                'sms': self.sms.enabled
            }
        }

# Predefined alert templates

class AlertTemplates:
    """Common alert templates"""
    
    @staticmethod
    async def trade_executed(alert_system: AuraQuantAlertSystem, 
                            symbol: str, 
                            side: str, 
                            quantity: float, 
                            price: float):
        """Alert for trade execution"""
        await alert_system.send_alert(
            title=f"Trade Executed: {symbol}",
            message=f"{side.upper()} {quantity} {symbol} @ ${price:.2f}",
            priority=AlertPriority.MEDIUM,
            category="Trading",
            data={
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": price,
                "total_value": quantity * price
            }
        )
        
    @staticmethod
    async def risk_alert(alert_system: AuraQuantAlertSystem,
                        risk_type: str,
                        current_value: float,
                        threshold: float):
        """Alert for risk threshold breach"""
        await alert_system.send_alert(
            title=f"Risk Alert: {risk_type}",
            message=f"{risk_type} has reached {current_value:.2f}, threshold is {threshold:.2f}",
            priority=AlertPriority.HIGH,
            category="Risk",
            data={
                "risk_type": risk_type,
                "current_value": current_value,
                "threshold": threshold,
                "breach_percentage": ((current_value - threshold) / threshold * 100)
            }
        )
        
    @staticmethod
    async def system_error(alert_system: AuraQuantAlertSystem,
                          error_type: str,
                          error_message: str,
                          component: str):
        """Alert for system errors"""
        await alert_system.send_alert(
            title=f"System Error: {component}",
            message=f"{error_type}: {error_message}",
            priority=AlertPriority.CRITICAL,
            category="System",
            data={
                "error_type": error_type,
                "component": component,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    @staticmethod
    async def ai_signal(alert_system: AuraQuantAlertSystem,
                       signal_type: str,
                       symbol: str,
                       confidence: float,
                       action: str):
        """Alert for AI trading signals"""
        await alert_system.send_alert(
            title=f"AI Signal: {signal_type}",
            message=f"{action} signal for {symbol} with {confidence:.1%} confidence",
            priority=AlertPriority.MEDIUM if confidence > 0.7 else AlertPriority.LOW,
            category="AI",
            data={
                "signal_type": signal_type,
                "symbol": symbol,
                "confidence": confidence,
                "action": action,
                "timestamp": datetime.now().isoformat()
            }
        )

# Global alert system instance
alert_system = AuraQuantAlertSystem()

# Convenience functions

async def send_alert(title: str, message: str, **kwargs):
    """Quick alert sending function"""
    return await alert_system.send_alert(title, message, **kwargs)

async def send_critical_alert(title: str, message: str, **kwargs):
    """Send critical alert to all channels"""
    return await alert_system.send_alert(
        title, 
        message, 
        priority=AlertPriority.CRITICAL,
        **kwargs
    )

if __name__ == "__main__":
    # Test the alert system
    import asyncio
    
    async def test_alerts():
        """Test alert system"""
        print("🚨 Testing AuraQuant Alert System...")
        
        # Test different priority levels
        await alert_system.send_alert(
            "Test Alert",
            "This is a test of the alert system",
            priority=AlertPriority.LOW
        )
        
        # Test trade alert
        await AlertTemplates.trade_executed(
            alert_system,
            "AAPL",
            "BUY",
            100,
            150.25
        )
        
        # Get statistics
        stats = alert_system.get_statistics()
        print(f"\n📊 Alert Statistics:")
        print(json.dumps(stats, indent=2))
        
    asyncio.run(test_alerts())
    print("\n✅ Alert System Test Complete")