import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from app.config import config
from app.storage.db import Database, PhoneNumber, SMSLog

logger = logging.getLogger(__name__)

class SMSAlertService:
    """Handles SMS alerts via Twilio"""
    
    ALERT_MESSAGE = "Hay cambios en la plataforma"
    DEDUPLICATION_WINDOW_MINUTES = 5  # Don't send duplicate alerts within 5 minutes
    
    def __init__(self, db: Database):
        self.db = db
        self.client = None
        self._initialize_twilio()
        
    def _initialize_twilio(self):
        """Initialize Twilio client"""
        if not all([config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN, config.TWILIO_FROM_NUMBER]):
            logger.warning("Twilio credentials not configured. SMS alerts will be disabled.")
            return
            
        try:
            self.client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
            logger.info("Twilio client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {e}")
            
    def is_configured(self) -> bool:
        """Check if SMS service is properly configured"""
        return self.client is not None
        
    async def send_change_alert(self, event_id: str, new_sectors: List[str], dry_run: bool = False) -> Dict:
        """
        Send SMS alert for detected changes
        
        Args:
            event_id: ID of the event with changes
            new_sectors: List of newly available sectors
            dry_run: If True, don't actually send SMS, just log
            
        Returns:
            Dict with send results
        """
        if not self.is_configured():
            logger.error("SMS service not configured. Cannot send alerts.")
            return {"success": False, "error": "SMS service not configured"}
            
        # Check for recent alerts to avoid spam
        if self._should_skip_due_to_deduplication(event_id):
            logger.info(f"Skipping SMS alert for {event_id} due to recent alert")
            return {"success": True, "skipped": True, "reason": "deduplication"}
            
        # Get active phone numbers
        active_phones = self._get_active_phone_numbers()
        if not active_phones:
            logger.warning("No active phone numbers registered for alerts")
            return {"success": True, "skipped": True, "reason": "no_phones"}
            
        logger.info(f"Sending SMS alerts to {len(active_phones)} numbers for event {event_id}")
        logger.info(f"New sectors detected: {new_sectors}")
        
        results = {
            "success": True,
            "total_phones": len(active_phones),
            "sent_count": 0,
            "failed_count": 0,
            "errors": [],
            "dry_run": dry_run
        }
        
        for phone in active_phones:
            try:
                if dry_run:
                    logger.info(f"[DRY RUN] Would send SMS to {phone}: {self.ALERT_MESSAGE}")
                    self._log_sms_attempt(phone, self.ALERT_MESSAGE, True, None)
                    results["sent_count"] += 1
                else:
                    success, error = await self._send_sms_to_phone(phone, self.ALERT_MESSAGE)
                    if success:
                        results["sent_count"] += 1
                        logger.info(f"SMS sent successfully to {phone}")
                    else:
                        results["failed_count"] += 1
                        results["errors"].append(f"{phone}: {error}")
                        logger.error(f"Failed to send SMS to {phone}: {error}")
                        
            except Exception as e:
                results["failed_count"] += 1
                results["errors"].append(f"{phone}: {str(e)}")
                logger.error(f"Exception sending SMS to {phone}: {e}")
                
        # Log the alert batch
        self._log_alert_batch(event_id, new_sectors, results)
        
        logger.info(f"SMS alert batch completed: {results['sent_count']} sent, {results['failed_count']} failed")
        return results
        
    async def _send_sms_to_phone(self, phone: str, message: str) -> tuple[bool, Optional[str]]:
        """
        Send SMS to a single phone number
        
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            message_obj = self.client.messages.create(
                body=message,
                from_=config.TWILIO_FROM_NUMBER,
                to=phone
            )
            
            # Log successful send
            self._log_sms_attempt(phone, message, True, None)
            return True, None
            
        except TwilioException as e:
            error_msg = f"Twilio error: {e.msg}"
            self._log_sms_attempt(phone, message, False, error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self._log_sms_attempt(phone, message, False, error_msg)
            return False, error_msg
            
    def _get_active_phone_numbers(self) -> List[str]:
        """Get list of active phone numbers from database"""
        try:
            session = self.db.get_session()
            phones = session.query(PhoneNumber).filter(PhoneNumber.active == True).all()
            return [phone.phone for phone in phones]
        except Exception as e:
            logger.error(f"Failed to get active phone numbers: {e}")
            return []
            
    def _should_skip_due_to_deduplication(self, event_id: str) -> bool:
        """Check if we should skip sending due to recent alerts"""
        try:
            session = self.db.get_session()
            cutoff_time = datetime.utcnow() - timedelta(minutes=self.DEDUPLICATION_WINDOW_MINUTES)
            
            recent_logs = session.query(SMSLog).filter(
                SMSLog.timestamp > cutoff_time,
                SMSLog.success == True,
                SMSLog.message == self.ALERT_MESSAGE
            ).first()
            
            return recent_logs is not None
            
        except Exception as e:
            logger.error(f"Error checking deduplication: {e}")
            return False
            
    def _log_sms_attempt(self, phone: str, message: str, success: bool, error_message: Optional[str]):
        """Log SMS attempt to database"""
        try:
            session = self.db.get_session()
            sms_log = SMSLog(
                phone=phone,
                message=message,
                success=success,
                error_message=error_message
            )
            session.add(sms_log)
            session.commit()
        except Exception as e:
            logger.error(f"Failed to log SMS attempt: {e}")
            
    def _log_alert_batch(self, event_id: str, new_sectors: List[str], results: Dict):
        """Log the alert batch for monitoring purposes"""
        logger.info(f"Alert batch summary for {event_id}:")
        logger.info(f"  New sectors: {len(new_sectors)} - {new_sectors}")
        logger.info(f"  Total phones: {results['total_phones']}")
        logger.info(f"  Sent: {results['sent_count']}")
        logger.info(f"  Failed: {results['failed_count']}")
        if results['errors']:
            logger.info(f"  Errors: {results['errors']}")
            
    def validate_phone_number(self, phone: str) -> tuple[bool, str]:
        """
        Validate phone number format (E.164)
        
        Returns:
            Tuple of (is_valid: bool, normalized_phone: str)
        """
        import re
        
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', phone)
        
        # Check if it starts with + and has 10-15 digits
        if re.match(r'^\+\d{10,15}$', cleaned):
            return True, cleaned
            
        # Try to add Colombia country code if it looks like a local number
        if re.match(r'^\d{10}$', cleaned):
            normalized = f"+57{cleaned}"
            return True, normalized
            
        return False, phone
        
    async def register_phone_number(self, phone: str) -> Dict:
        """
        Register a new phone number for alerts
        
        Returns:
            Dict with registration result
        """
        # Validate phone number
        is_valid, normalized_phone = self.validate_phone_number(phone)
        if not is_valid:
            return {
                "success": False,
                "error": "Invalid phone number format. Use E.164 format (+573001234567)"
            }
            
        try:
            session = self.db.get_session()
            
            # Check if phone already exists
            existing = session.query(PhoneNumber).filter(
                PhoneNumber.phone == normalized_phone
            ).first()
            
            if existing:
                if existing.active:
                    return {
                        "success": False,
                        "error": "Phone number already registered and active"
                    }
                else:
                    # Reactivate existing phone
                    existing.active = True
                    existing.registered_at = datetime.utcnow()
                    session.commit()
                    return {
                        "success": True,
                        "message": "Phone number reactivated successfully",
                        "phone": normalized_phone
                    }
            else:
                # Add new phone number
                new_phone = PhoneNumber(phone=normalized_phone)
                session.add(new_phone)
                session.commit()
                return {
                    "success": True,
                    "message": "Phone number registered successfully",
                    "phone": normalized_phone
                }
                
        except Exception as e:
            logger.error(f"Failed to register phone number: {e}")
            return {
                "success": False,
                "error": "Database error occurred"
            }
            
    async def unregister_phone_number(self, phone: str) -> Dict:
        """
        Unregister (deactivate) a phone number
        
        Returns:
            Dict with unregistration result
        """
        is_valid, normalized_phone = self.validate_phone_number(phone)
        if not is_valid:
            return {
                "success": False,
                "error": "Invalid phone number format"
            }
            
        try:
            session = self.db.get_session()
            phone_record = session.query(PhoneNumber).filter(
                PhoneNumber.phone == normalized_phone
            ).first()
            
            if not phone_record:
                return {
                    "success": False,
                    "error": "Phone number not found"
                }
                
            phone_record.active = False
            session.commit()
            
            return {
                "success": True,
                "message": "Phone number unregistered successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to unregister phone number: {e}")
            return {
                "success": False,
                "error": "Database error occurred"
            }
            
    def get_registered_phones_count(self) -> int:
        """Get count of active registered phone numbers"""
        try:
            session = self.db.get_session()
            count = session.query(PhoneNumber).filter(PhoneNumber.active == True).count()
            return count
        except Exception as e:
            logger.error(f"Failed to get phone count: {e}")
            return 0
