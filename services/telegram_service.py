import requests
from datetime import datetime

class TelegramService:
    """Service for sending notifications to Telegram"""
    
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, message, parse_mode='HTML'):
        """Send a message to Telegram chat"""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get('ok'):
                print(f"✅ Telegram message sent successfully")
                return True
            else:
                print(f"❌ Telegram API error: {result}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"⏱️ Telegram request timeout")
            return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Telegram request error: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ Telegram error: {str(e)}")
            return False
    
    def test_connection(self):
        """Test Telegram bot connection"""
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get('ok'):
                bot_info = result.get('result', {})
                bot_name = bot_info.get('first_name', 'Unknown')
                bot_username = bot_info.get('username', 'Unknown')
                print(f"✅ Connected to Telegram bot: {bot_name} (@{bot_username})")
                return True, f"Connected to: {bot_name} (@{bot_username})"
            else:
                return False, "Invalid bot token"
                
        except Exception as e:
            return False, str(e)
    
    def send_bounce_notification(self, email, reason, date):
        """Send bounce notification"""
        message = f"""
🚫 <b>Email Bounce Alert</b>

📧 Email: <code>{email}</code>
❌ Reason: {reason}
📅 Date: {date}

Email ini bounce dan tidak terkirim dengan baik.
"""
        return self.send_message(message.strip())
    
    def send_email_open_notification(self, email, date):
        """Send email open notification"""
        message = f"""
👁️ <b>Email Opened</b>

📧 Email: <code>{email}</code>
📅 Date: {date}

Subscriber membuka email Anda!
"""
        return self.send_message(message.strip())
    
    def send_link_click_notification(self, email, link_clicked, date):
        """Send link click notification"""
        message = f"""
🖱️ <b>Link Clicked</b>

📧 Email: <code>{email}</code>
🔗 Link: {link_clicked}
📅 Date: {date}

Subscriber mengklik link di email Anda!
"""
        return self.send_message(message.strip())
    
    def send_unsubscribe_notification(self, email, date):
        """Send unsubscribe notification"""
        message = f"""
❌ <b>Unsubscribe Alert</b>

📧 Email: <code>{email}</code>
📅 Date: {date}

Subscriber telah unsubscribe dari mailing list.
"""
        return self.send_message(message.strip())
    
    def send_new_subscriber_notification(self, email, first_name, last_name, mobile, date):
        """Send new subscriber notification"""
        full_name = f"{first_name} {last_name}".strip() or "N/A"
        message = f"""
✅ <b>New Subscriber</b>

👤 Name: {full_name}
📧 Email: <code>{email}</code>
📱 Mobile: {mobile or 'N/A'}
📅 Date: {date}

Subscriber baru telah bergabung!
"""
        return self.send_message(message.strip())
