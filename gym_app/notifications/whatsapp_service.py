import requests
import logging

logger = logging.getLogger(__name__)

class WhatsAppService:
    # ── PASTE YOUR ULTRAMSG CREDENTIALS HERE ──
    INSTANCE_ID = os.getenv("ULTRAMSG_INSTANCE_ID")
    API_TOKEN = os.getenv("ULTRAMSG_API_TOKEN")
    
    # The standard UltraMsg endpoint
    API_URL = f"https://api.ultramsg.com/{INSTANCE_ID}/messages/chat"

    @staticmethod
    def send_welcome_message(phone_number: str, member_name: str) -> bool:
        """Sends a welcome message instantly via API."""
        return WhatsAppService._send_message(
            phone=phone_number,
            text=f"Hi {member_name}, Welcome to The Iron Temple GYM! 🏋️‍♂️\n\nWe are thrilled to have you start your fitness journey with us."
        )

    @staticmethod
    def send_payment_reminder(phone_number: str, member_name: str) -> bool:
        """Sends a gentle payment reminder to defaulters."""
        return WhatsAppService._send_message(
            phone=phone_number,
            text=f"Hi {member_name}, this is a gentle reminder from The Iron Temple GYM. 🏋️‍♂️\n\nYour membership plan has expired. Please renew at the front desk to continue your fitness journey without interruption!"
        )

    @staticmethod
    def _send_message(phone: str, text: str) -> bool:
        """Internal helper to handle the actual HTTP request."""
        # APIs expect the number with the country code but NO '+' symbol
        clean_phone = phone.replace("+", "").strip()
        
        # Ensure it has the India country code if missing
        if len(clean_phone) == 10:
            clean_phone = f"91{clean_phone}"

        payload = {
            "token": WhatsAppService.API_TOKEN,
            "to": clean_phone,
            "body": text
        }
        
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        try:
            response = requests.post(WhatsAppService.API_URL, data=payload, headers=headers, timeout=10)
            response.raise_for_status() 
            logger.info(f"WhatsApp API: Message sent to {clean_phone}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"WhatsApp API Error: Failed to send to {clean_phone} - {e}")
            return False