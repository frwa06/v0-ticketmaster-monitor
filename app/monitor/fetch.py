import asyncio
import random
import logging
from typing import Dict, List, Optional
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from app.config import config
from app.monitor.parse import SectorParser

logger = logging.getLogger(__name__)

class TicketmasterScraper:
    """Handles web scraping of Ticketmaster event pages"""
    
    def __init__(self):
        self.parser = SectorParser()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start_browser()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close_browser()
        
    async def start_browser(self):
        """Initialize browser and context"""
        try:
            self.playwright = await async_playwright().start()
            
            # Launch browser with stealth settings
            self.browser = await self.playwright.chromium.launch(
                headless=config.HEADLESS,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-images',  # Faster loading
                ]
            )
            
            # Create context with realistic settings
            self.context = await self.browser.new_context(
                user_agent=config.full_user_agent,
                viewport={'width': 1366, 'height': 768},
                locale='es-CO',
                timezone_id='America/Bogota'
            )
            
            logger.info("Browser initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise
            
    async def close_browser(self):
        """Clean up browser resources"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
            
    async def scrape_event(self, event_url: str, event_id: str) -> Optional[List[str]]:
        """
        Scrape a single event page for available sectors
        
        Args:
            event_url: URL of the event page
            event_id: Unique identifier for the event
            
        Returns:
            List of available sector IDs, or None if scraping failed
        """
        page = None
        try:
            logger.info(f"Starting scrape for event {event_id}: {event_url}")
            
            page = await self.context.new_page()
            
            # Set page timeout
            page.set_default_timeout(config.PAGE_TIMEOUT)
            
            # Navigate to event page
            await page.goto(event_url, wait_until='domcontentloaded')
            await self._add_human_delay()
            
            # Look for and click "Ver entradas" button
            await self._click_view_tickets_button(page)
            
            # Wait for interactive map to load
            await self._wait_for_map_stable(page)
            
            # Extract sector information
            sectors_data = await self._extract_sectors(page)
            
            # Parse and normalize sectors
            available_sectors = self.parser.normalize_sectors(sectors_data)
            
            logger.info(f"Successfully scraped {len(available_sectors)} available sectors for {event_id}")
            return list(available_sectors)
            
        except Exception as e:
            logger.error(f"Failed to scrape event {event_id}: {e}")
            return None
            
        finally:
            if page:
                await page.close()
                
    async def _click_view_tickets_button(self, page: Page):
        """Find and click the 'Ver entradas' button"""
        
        # Multiple possible selectors for the button
        button_selectors = [
            'button:has-text("Ver entradas")',
            'a:has-text("Ver entradas")',
            '[data-testid*="view-tickets"]',
            '[aria-label*="Ver entradas"]',
            '.btn:has-text("Ver entradas")',
            'button:has-text("View tickets")',
            'a:has-text("View tickets")'
        ]
        
        for selector in button_selectors:
            try:
                element = await page.wait_for_selector(selector, timeout=5000)
                if element:
                    await element.click()
                    logger.info(f"Clicked 'Ver entradas' button using selector: {selector}")
                    await self._add_human_delay()
                    return
            except:
                continue
                
        # If no button found, try scrolling and looking again
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        await self._add_human_delay()
        
        for selector in button_selectors:
            try:
                element = await page.wait_for_selector(selector, timeout=3000)
                if element:
                    await element.click()
                    logger.info(f"Clicked 'Ver entradas' button after scroll using: {selector}")
                    await self._add_human_delay()
                    return
            except:
                continue
                
        raise Exception("Could not find 'Ver entradas' button")
        
    async def _wait_for_map_stable(self, page: Page):
        """Wait for the interactive map to be stable and loaded"""
        
        # Wait for potential map container selectors
        map_selectors = [
            '[data-testid*="venue-map"]',
            '[class*="venue-map"]',
            '[class*="seating-map"]',
            'svg[class*="map"]',
            '.interactive-map',
            '[id*="venue-map"]',
            '[id*="seating-map"]'
        ]
        
        map_found = False
        for selector in map_selectors:
            try:
                await page.wait_for_selector(selector, timeout=10000)
                logger.info(f"Map container found with selector: {selector}")
                map_found = True
                break
            except:
                continue
                
        if not map_found:
            logger.warning("No specific map container found, waiting for network idle")
            
        # Wait for network to be idle (no requests for 2 seconds)
        try:
            await page.wait_for_load_state('networkidle', timeout=15000)
        except:
            logger.warning("Network idle timeout, proceeding anyway")
            
        # Additional wait for any animations/loading
        await asyncio.sleep(2)
        
    async def _extract_sectors(self, page: Page) -> List[Dict]:
        """Extract sector information from the page DOM"""
        
        # JavaScript to extract sector data
        extract_script = """
        () => {
            const sectors = [];
            
            // Look for various sector element patterns
            const selectors = [
                'svg path[data-section]',
                'svg path[aria-label]',
                'svg g[data-section] path',
                'svg g[aria-label] path',
                '[class*="sector"]',
                '[class*="section"]',
                '[data-testid*="section"]',
                '[data-testid*="sector"]'
            ];
            
            for (const selector of selectors) {
                const elements = document.querySelectorAll(selector);
                
                for (const element of elements) {
                    const sectorData = {
                        id: element.id || '',
                        aria_label: element.getAttribute('aria-label') || '',
                        class_names: element.className || '',
                        data_section: element.getAttribute('data-section') || '',
                        data_sector_id: element.getAttribute('data-sector-id') || '',
                        data_status: element.getAttribute('data-status') || '',
                        title: element.getAttribute('title') || '',
                        style: element.getAttribute('style') || '',
                        fill: element.getAttribute('fill') || '',
                        text_content: element.textContent?.trim() || ''
                    };
                    
                    // Only include if we have some identifying information
                    if (sectorData.id || sectorData.aria_label || sectorData.data_section || sectorData.text_content) {
                        sectors.push(sectorData);
                    }
                }
                
                // If we found sectors with this selector, break
                if (sectors.length > 0) {
                    break;
                }
            }
            
            return sectors;
        }
        """
        
        try:
            sectors_data = await page.evaluate(extract_script)
            logger.info(f"Extracted {len(sectors_data)} sector elements from DOM")
            return sectors_data
            
        except Exception as e:
            logger.error(f"Failed to extract sectors from DOM: {e}")
            return []
            
    async def _add_human_delay(self):
        """Add a random delay to mimic human behavior"""
        delay = random.uniform(1.0, 3.0)
        await asyncio.sleep(delay)
        
    async def scrape_all_events(self) -> Dict[str, Optional[List[str]]]:
        """
        Scrape all configured events
        
        Returns:
            Dict mapping event_id to list of available sectors (or None if failed)
        """
        results = {}
        
        for event in config.EVENTS:
            event_id = event['id']
            event_url = event['url']
            
            try:
                sectors = await self.scrape_event(event_url, event_id)
                results[event_id] = sectors
                
                # Add delay between events to avoid rate limiting
                await asyncio.sleep(random.uniform(2.0, 5.0))
                
            except Exception as e:
                logger.error(f"Failed to scrape event {event_id}: {e}")
                results[event_id] = None
                
        return results
