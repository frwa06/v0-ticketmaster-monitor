import asyncio
import logging
import random
import signal
import sys
from datetime import datetime
from typing import Dict, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import argparse

from app.config import config
from app.storage.db import Database, Event, Snapshot, ChangeLog
from app.monitor.fetch import TicketmasterScraper
from app.monitor.diff import SnapshotComparator
from app.alerts.sms import SMSAlertService

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('ticketmaster_monitor.log')
    ]
)

logger = logging.getLogger(__name__)

class TicketmasterMonitor:
    """Main monitoring service that coordinates scraping, comparison, and alerts"""
    
    def __init__(self, dry_run: bool = False):
        self.db = Database()
        self.sms_service = SMSAlertService(self.db)
        self.comparator = SnapshotComparator()
        self.scheduler = AsyncIOScheduler()
        self.dry_run = dry_run
        self.running = False
        
        # Initialize events in database
        self._initialize_events()
        
    def _initialize_events(self):
        """Initialize events in database if they don't exist"""
        try:
            session = self.db.get_session()
            
            for event_config in config.EVENTS:
                existing_event = session.query(Event).filter(
                    Event.event_id == event_config['id']
                ).first()
                
                if not existing_event:
                    new_event = Event(
                        event_id=event_config['id'],
                        url=event_config['url'],
                        name=f"Bad Bunny - {event_config['id'].upper()}"
                    )
                    session.add(new_event)
                    logger.info(f"Added new event to database: {event_config['id']}")
                    
            session.commit()
            logger.info("Events initialized in database")
            
        except Exception as e:
            logger.error(f"Failed to initialize events: {e}")
            
    async def monitor_single_event(self, event_id: str, event_url: str) -> Dict:
        """
        Monitor a single event for changes
        
        Returns:
            Dict with monitoring results
        """
        logger.info(f"Starting monitoring cycle for event: {event_id}")
        
        result = {
            "event_id": event_id,
            "success": False,
            "sectors_found": 0,
            "changes_detected": False,
            "new_sectors": [],
            "sms_sent": False,
            "error": None
        }
        
        try:
            # Scrape current sectors
            async with TicketmasterScraper() as scraper:
                current_sectors = await scraper.scrape_event(event_url, event_id)
                
            if current_sectors is None:
                result["error"] = "Failed to scrape event"
                logger.error(f"Failed to scrape event {event_id}")
                return result
                
            result["sectors_found"] = len(current_sectors)
            current_sectors_set = set(current_sectors)
            
            # Get previous snapshot
            previous_sectors_set = self._get_previous_snapshot(event_id)
            
            # Compare snapshots
            change_info = self.comparator.detect_changes(previous_sectors_set, current_sectors_set)
            result["changes_detected"] = change_info["has_changes"]
            result["new_sectors"] = change_info["new_sectors"]
            
            # Save new snapshot
            self._save_snapshot(event_id, current_sectors)
            
            # Update event last_checked timestamp
            self._update_event_timestamp(event_id)
            
            # Send alerts if new sectors detected
            if self.comparator.should_send_alert(change_info):
                logger.info(f"New sectors detected for {event_id}: {change_info['new_sectors']}")
                
                # Log the change
                self._log_change(event_id, change_info["new_sectors"])
                
                # Send SMS alerts
                sms_result = await self.sms_service.send_change_alert(
                    event_id, 
                    change_info["new_sectors"],
                    dry_run=self.dry_run
                )
                
                result["sms_sent"] = sms_result.get("success", False)
                
                if sms_result.get("success"):
                    logger.info(f"SMS alerts sent successfully for {event_id}")
                else:
                    logger.error(f"Failed to send SMS alerts for {event_id}: {sms_result.get('error')}")
                    
            result["success"] = True
            logger.info(f"Monitoring cycle completed for {event_id}: {result['sectors_found']} sectors, changes: {result['changes_detected']}")
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error monitoring event {event_id}: {e}")
            
        return result
        
    def _get_previous_snapshot(self, event_id: str) -> set:
        """Get the most recent snapshot for an event"""
        try:
            session = self.db.get_session()
            latest_snapshot = session.query(Snapshot).filter(
                Snapshot.event_id == event_id
            ).order_by(Snapshot.timestamp.desc()).first()
            
            if latest_snapshot:
                return set(latest_snapshot.get_sectors())
            else:
                logger.info(f"No previous snapshot found for {event_id}")
                return set()
                
        except Exception as e:
            logger.error(f"Failed to get previous snapshot for {event_id}: {e}")
            return set()
            
    def _save_snapshot(self, event_id: str, sectors: list):
        """Save a new snapshot to the database"""
        try:
            session = self.db.get_session()
            snapshot = Snapshot(event_id=event_id)
            snapshot.set_sectors(sectors)
            session.add(snapshot)
            session.commit()
            logger.debug(f"Saved snapshot for {event_id} with {len(sectors)} sectors")
            
        except Exception as e:
            logger.error(f"Failed to save snapshot for {event_id}: {e}")
            
    def _log_change(self, event_id: str, new_sectors: list):
        """Log a change to the database"""
        try:
            session = self.db.get_session()
            change_log = ChangeLog(
                event_id=event_id,
                new_sectors=str(new_sectors),  # Store as string for simplicity
                sms_sent=not self.dry_run  # Mark as sent if not dry run
            )
            session.add(change_log)
            session.commit()
            logger.debug(f"Logged change for {event_id}: {new_sectors}")
            
        except Exception as e:
            logger.error(f"Failed to log change for {event_id}: {e}")
            
    def _update_event_timestamp(self, event_id: str):
        """Update the last_checked timestamp for an event"""
        try:
            session = self.db.get_session()
            event = session.query(Event).filter(Event.event_id == event_id).first()
            if event:
                event.last_checked = datetime.utcnow()
                session.commit()
                
        except Exception as e:
            logger.error(f"Failed to update timestamp for {event_id}: {e}")
            
    async def monitor_all_events(self):
        """Monitor all configured events"""
        logger.info("Starting monitoring cycle for all events")
        
        results = []
        for event_config in config.EVENTS:
            try:
                result = await self.monitor_single_event(
                    event_config['id'], 
                    event_config['url']
                )
                results.append(result)
                
                # Add random delay between events
                delay = random.uniform(5.0, 15.0)
                logger.debug(f"Waiting {delay:.1f}s before next event")
                await asyncio.sleep(delay)
                
            except Exception as e:
                logger.error(f"Error in monitoring cycle for {event_config['id']}: {e}")
                results.append({
                    "event_id": event_config['id'],
                    "success": False,
                    "error": str(e)
                })
                
        # Log summary
        successful = sum(1 for r in results if r["success"])
        total_changes = sum(1 for r in results if r.get("changes_detected", False))
        total_sms = sum(1 for r in results if r.get("sms_sent", False))
        
        logger.info(f"Monitoring cycle completed: {successful}/{len(results)} successful, {total_changes} changes, {total_sms} SMS sent")
        
        return results
        
    def start_scheduler(self):
        """Start the background scheduler"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
            
        # Calculate random interval
        min_interval = config.POLL_INTERVAL_MIN
        max_interval = config.POLL_INTERVAL_MAX
        
        logger.info(f"Starting scheduler with interval {min_interval}-{max_interval} seconds")
        
        # Add job with random interval
        self.scheduler.add_job(
            self.monitor_all_events,
            trigger=IntervalTrigger(
                seconds=random.randint(min_interval, max_interval)
            ),
            id='monitor_events',
            replace_existing=True,
            max_instances=1  # Prevent overlapping runs
        )
        
        self.scheduler.start()
        self.running = True
        logger.info("Scheduler started successfully")
        
    def stop_scheduler(self):
        """Stop the background scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            self.running = False
            logger.info("Scheduler stopped")
            
    async def run_once(self, event_id: Optional[str] = None):
        """Run monitoring once (for testing)"""
        if event_id:
            # Monitor specific event
            event_config = next((e for e in config.EVENTS if e['id'] == event_id), None)
            if not event_config:
                logger.error(f"Event {event_id} not found in configuration")
                return
                
            result = await self.monitor_single_event(event_config['id'], event_config['url'])
            logger.info(f"Single event monitoring result: {result}")
        else:
            # Monitor all events
            results = await self.monitor_all_events()
            logger.info(f"All events monitoring results: {results}")

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Ticketmaster Monitor')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--event', type=str, help='Monitor specific event (use with --once)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no SMS sent)')
    parser.add_argument('--simulate-delta', action='store_true', help='Simulate changes for testing')
    
    args = parser.parse_args()
    
    # Initialize monitor
    monitor = TicketmasterMonitor(dry_run=args.dry_run)
    
    if args.simulate_delta:
        # Simulate changes for testing
        logger.info("Simulating delta changes for testing")
        fake_new_sectors = ["sector_a1", "sector_b2", "sector_c3"]
        sms_result = await monitor.sms_service.send_change_alert(
            "pq23", 
            fake_new_sectors,
            dry_run=args.dry_run
        )
        logger.info(f"Simulation result: {sms_result}")
        return
        
    if args.once:
        # Run once and exit
        logger.info("Running in single-shot mode")
        await monitor.run_once(args.event)
        return
        
    # Run continuous monitoring
    logger.info("Starting continuous monitoring service")
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        monitor.stop_scheduler()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start scheduler
    monitor.start_scheduler()
    
    # Keep the main thread alive
    try:
        while True:
            await asyncio.sleep(60)  # Check every minute
            if not monitor.running:
                break
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
    finally:
        monitor.stop_scheduler()
        monitor.db.close()

if __name__ == "__main__":
    asyncio.run(main())
