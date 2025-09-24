from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

Base = declarative_base()

class Event(Base):
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True)
    event_id = Column(String(50), unique=True, nullable=False)
    url = Column(String(500), nullable=False)
    name = Column(String(200))
    last_checked = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class Snapshot(Base):
    __tablename__ = 'snapshots'
    
    id = Column(Integer, primary_key=True)
    event_id = Column(String(50), nullable=False)
    sectors_data = Column(Text)  # JSON string of available sectors
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def get_sectors(self):
        return json.loads(self.sectors_data) if self.sectors_data else []
    
    def set_sectors(self, sectors):
        self.sectors_data = json.dumps(sectors)

class ChangeLog(Base):
    __tablename__ = 'change_logs'
    
    id = Column(Integer, primary_key=True)
    event_id = Column(String(50), nullable=False)
    new_sectors = Column(Text)  # JSON string of newly available sectors
    timestamp = Column(DateTime, default=datetime.utcnow)
    sms_sent = Column(Boolean, default=False)

class PhoneNumber(Base):
    __tablename__ = 'phone_numbers'
    
    id = Column(Integer, primary_key=True)
    phone = Column(String(20), unique=True, nullable=False)
    registered_at = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)

class SMSLog(Base):
    __tablename__ = 'sms_logs'
    
    id = Column(Integer, primary_key=True)
    phone = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=False)
    error_message = Column(Text)

class Database:
    def __init__(self, db_url="sqlite:///ticketmaster_monitor.db"):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def get_session(self):
        return self.session
    
    def close(self):
        self.session.close()
