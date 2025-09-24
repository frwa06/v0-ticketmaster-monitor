import pytest
from unittest.mock import Mock, patch
from app.alerts.sms import SMSAlertService
from app.storage.db import Database

class TestSMSAlertService:
    """Test cases for SMS alert functionality"""
    
    def setup_method(self):
        # Use in-memory database for testing
        self.db = Database("sqlite:///:memory:")
        self.sms_service = SMSAlertService(self.db)
        
    def test_validate_phone_number_e164_format(self):
        """Test phone number validation with E.164 format"""
        valid, normalized = self.sms_service.validate_phone_number("+573001234567")
        
        assert valid
        assert normalized == "+573001234567"
        
    def test_validate_phone_number_local_format(self):
        """Test phone number validation with local Colombian format"""
        valid, normalized = self.sms_service.validate_phone_number("3001234567")
        
        assert valid
        assert normalized == "+573001234567"
        
    def test_validate_phone_number_with_spaces(self):
        """Test phone number validation with spaces and formatting"""
        valid, normalized = self.sms_service.validate_phone_number("+57 300 123 4567")
        
        assert valid
        assert normalized == "+573001234567"
        
    def test_validate_phone_number_invalid(self):
        """Test phone number validation with invalid format"""
        valid, normalized = self.sms_service.validate_phone_number("123")
        
        assert not valid
        assert normalized == "123"
        
    def test_validate_phone_number_too_long(self):
        """Test phone number validation with too many digits"""
        valid, normalized = self.sms_service.validate_phone_number("+5730012345678901234")
        
        assert not valid
        
    @pytest.mark.asyncio
    async def test_register_phone_number_success(self):
        """Test successful phone number registration"""
        result = await self.sms_service.register_phone_number("3001234567")
        
        assert result['success']
        assert result['phone'] == "+573001234567"
        assert "registered successfully" in result['message']
        
    @pytest.mark.asyncio
    async def test_register_phone_number_duplicate(self):
        """Test registering duplicate phone number"""
        # Register first time
        await self.sms_service.register_phone_number("3001234567")
        
        # Try to register again
        result = await self.sms_service.register_phone_number("3001234567")
        
        assert not result['success']
        assert "already registered" in result['error']
        
    @pytest.mark.asyncio
    async def test_register_phone_number_invalid(self):
        """Test registering invalid phone number"""
        result = await self.sms_service.register_phone_number("123")
        
        assert not result['success']
        assert "Invalid phone number format" in result['error']
        
    @pytest.mark.asyncio
    async def test_unregister_phone_number(self):
        """Test phone number unregistration"""
        # Register first
        await self.sms_service.register_phone_number("3001234567")
        
        # Then unregister
        result = await self.sms_service.unregister_phone_number("+573001234567")
        
        assert result['success']
        assert "unregistered successfully" in result['message']
        
    @pytest.mark.asyncio
    async def test_unregister_nonexistent_phone(self):
        """Test unregistering non-existent phone number"""
        result = await self.sms_service.unregister_phone_number("+573001234567")
        
        assert not result['success']
        assert "not found" in result['error']
