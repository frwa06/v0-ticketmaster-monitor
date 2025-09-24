import os
from typing import List

class Config:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///ticketmaster_monitor.db")
    
    # Twilio SMS
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")
    
    # Monitoring settings
    POLL_INTERVAL_MIN = int(os.getenv("POLL_INTERVAL_MIN", "90"))
    POLL_INTERVAL_MAX = int(os.getenv("POLL_INTERVAL_MAX", "150"))
    
    # Browser settings
    HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
    PAGE_TIMEOUT = int(os.getenv("PAGE_TIMEOUT", "30000"))
    USER_AGENT = os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    # Events to monitor
    EVENTS = [
        {"id": "pq23", "url": "https://www.ticketmaster.co/event/bad-bunny-pq23"},
        {"id": "pq24", "url": "https://www.ticketmaster.co/event/bad-bunny-pq24"},
        {"id": "pq25", "url": "https://www.ticketmaster.co/event/bad-bunny-pq25"},
    ]
    
    # Web server
    WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
    WEB_PORT = int(os.getenv("WEB_PORT", "8000"))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Contact info for user-agent
    CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "admin@example.com")
    
    @property
    def full_user_agent(self):
        return f"{self.USER_AGENT} (Contact: {self.CONTACT_EMAIL})"

config = Config()
