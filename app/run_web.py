"""
Separate script to run the web server alongside the monitoring service
"""
import asyncio
import logging
import signal
import sys
from threading import Thread
import uvicorn
from app.config import config
from app.main import TicketmasterMonitor

logger = logging.getLogger(__name__)

class WebServerRunner:
    """Runs both the web server and monitoring service"""
    
    def __init__(self):
        self.monitor = None
        self.web_server = None
        self.running = False
        
    def start_web_server(self):
        """Start the web server in a separate thread"""
        def run_server():
            uvicorn.run(
                "app.web.server:app",
                host=config.WEB_HOST,
                port=config.WEB_PORT,
                log_level=config.LOG_LEVEL.lower(),
                access_log=True
            )
            
        web_thread = Thread(target=run_server, daemon=True)
        web_thread.start()
        logger.info(f"Web server started on http://{config.WEB_HOST}:{config.WEB_PORT}")
        
    async def start_monitor(self):
        """Start the monitoring service"""
        self.monitor = TicketmasterMonitor()
        self.monitor.start_scheduler()
        logger.info("Monitoring service started")
        
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            self.shutdown()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
    def shutdown(self):
        """Shutdown both services"""
        if self.monitor:
            self.monitor.stop_scheduler()
            self.monitor.db.close()
        self.running = False
        logger.info("Services shut down")
        
    async def run(self):
        """Run both services"""
        logger.info("Starting Ticketmaster Monitor with Web Interface")
        
        # Setup signal handlers
        self.setup_signal_handlers()
        
        # Start web server
        self.start_web_server()
        
        # Start monitoring service
        await self.start_monitor()
        
        self.running = True
        
        # Keep running
        try:
            while self.running:
                await asyncio.sleep(60)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self.shutdown()

async def main():
    runner = WebServerRunner()
    await runner.run()

if __name__ == "__main__":
    asyncio.run(main())
