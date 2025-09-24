from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import logging
from typing import Dict
from app.storage.db import Database
from app.alerts.sms import SMSAlertService
from app.config import config

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Ticketmaster Monitor",
    description="Monitor Ticketmaster events for seat availability changes",
    version="1.0.0"
)

# Initialize database and SMS service
db = Database()
sms_service = SMSAlertService(db)

# Setup templates
templates = Jinja2Templates(directory="app/web/templates")

# Health check endpoint
@app.get("/healthz")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "sms_configured": sms_service.is_configured(),
        "registered_phones": sms_service.get_registered_phones_count()
    }

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Basic metrics endpoint"""
    try:
        session = db.get_session()
        
        # Get basic counts from database
        from app.storage.db import PhoneNumber, SMSLog, ChangeLog, Snapshot
        
        phone_count = session.query(PhoneNumber).filter(PhoneNumber.active == True).count()
        total_sms_sent = session.query(SMSLog).filter(SMSLog.success == True).count()
        total_changes = session.query(ChangeLog).count()
        total_snapshots = session.query(Snapshot).count()
        
        return {
            "active_phones": phone_count,
            "total_sms_sent": total_sms_sent,
            "total_changes_detected": total_changes,
            "total_snapshots": total_snapshots,
            "sms_service_configured": sms_service.is_configured()
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return {"error": "Failed to get metrics"}

# Main registration page
@app.get("/", response_class=HTMLResponse)
async def registration_page(request: Request):
    """Main page with phone registration form"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "registered_count": sms_service.get_registered_phones_count(),
        "sms_configured": sms_service.is_configured()
    })

# Register phone number endpoint
@app.post("/register")
async def register_phone(phone: str = Form(...)):
    """Register a phone number for SMS alerts"""
    try:
        result = await sms_service.register_phone_number(phone)
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": result["message"],
                    "phone": result.get("phone", phone)
                }
            )
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": result["error"]
                }
            )
            
    except Exception as e:
        logger.error(f"Error registering phone: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal server error"
            }
        )

# Unregister phone number endpoint
@app.post("/unregister")
async def unregister_phone(phone: str = Form(...)):
    """Unregister a phone number from SMS alerts"""
    try:
        result = await sms_service.unregister_phone_number(phone)
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": result["message"]
                }
            )
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": result["error"]
                }
            )
            
    except Exception as e:
        logger.error(f"Error unregistering phone: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal server error"
            }
        )

# Status page
@app.get("/status", response_class=HTMLResponse)
async def status_page(request: Request):
    """Status page showing system information"""
    try:
        session = db.get_session()
        from app.storage.db import PhoneNumber, SMSLog, ChangeLog, Event
        
        # Get recent activity
        recent_changes = session.query(ChangeLog).order_by(ChangeLog.timestamp.desc()).limit(10).all()
        recent_sms = session.query(SMSLog).order_by(SMSLog.timestamp.desc()).limit(10).all()
        active_phones = session.query(PhoneNumber).filter(PhoneNumber.active == True).all()
        events = session.query(Event).all()
        
        return templates.TemplateResponse("status.html", {
            "request": request,
            "recent_changes": recent_changes,
            "recent_sms": recent_sms,
            "active_phones": active_phones,
            "events": events,
            "sms_configured": sms_service.is_configured()
        })
        
    except Exception as e:
        logger.error(f"Error loading status page: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Failed to load status information"
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.web.server:app",
        host=config.WEB_HOST,
        port=config.WEB_PORT,
        log_level=config.LOG_LEVEL.lower()
    )
