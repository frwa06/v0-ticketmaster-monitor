from typing import List, Dict, Set
import re
import logging

logger = logging.getLogger(__name__)

class SectorParser:
    """Parses and normalizes sector data from Ticketmaster pages"""
    
    def __init__(self):
        self.available_indicators = [
            "disponible",
            "available", 
            "selectable",
            "enabled"
        ]
        
        self.unavailable_indicators = [
            "no disponible",
            "unavailable",
            "disabled",
            "sold out",
            "agotado"
        ]
    
    def normalize_sectors(self, raw_sectors: List[Dict]) -> Set[str]:
        """
        Normalize raw sector data to a set of available sector identifiers
        
        Args:
            raw_sectors: List of dicts with sector info from DOM
            
        Returns:
            Set of available sector identifiers
        """
        available_sectors = set()
        
        for sector in raw_sectors:
            if self._is_sector_available(sector):
                sector_id = self._extract_sector_id(sector)
                if sector_id:
                    available_sectors.add(sector_id)
        
        logger.info(f"Normalized {len(raw_sectors)} sectors to {len(available_sectors)} available")
        return available_sectors
    
    def _is_sector_available(self, sector: Dict) -> bool:
        """Check if a sector is available based on various indicators"""
        
        # Check aria-label
        aria_label = sector.get('aria_label', '').lower()
        if any(indicator in aria_label for indicator in self.available_indicators):
            return True
        if any(indicator in aria_label for indicator in self.unavailable_indicators):
            return False
            
        # Check class names
        class_names = sector.get('class_names', '').lower()
        if 'available' in class_names or 'selectable' in class_names:
            return True
        if 'disabled' in class_names or 'unavailable' in class_names:
            return False
            
        # Check data attributes
        data_status = sector.get('data_status', '').lower()
        if data_status in ['available', 'enabled', 'selectable']:
            return True
        if data_status in ['unavailable', 'disabled', 'sold-out']:
            return False
            
        # Check styles (color-based detection)
        style = sector.get('style', '').lower()
        fill = sector.get('fill', '').lower()
        
        # Blue typically indicates available
        if any(color in style or color in fill for color in ['blue', '#0066cc', '#007bff']):
            return True
            
        # Gray typically indicates unavailable  
        if any(color in style or color in fill for color in ['gray', 'grey', '#cccccc', '#999999']):
            return False
            
        # Default to unavailable if unclear
        return False
    
    def _extract_sector_id(self, sector: Dict) -> str:
        """Extract a unique identifier for the sector"""
        
        # Try various ID sources in order of preference
        sector_id = (
            sector.get('id') or
            sector.get('data_sector_id') or 
            sector.get('data_section') or
            sector.get('aria_label') or
            sector.get('title') or
            sector.get('text_content', '').strip()
        )
        
        if sector_id:
            # Clean up the ID
            sector_id = re.sub(r'[^\w\s-]', '', str(sector_id))
            sector_id = re.sub(r'\s+', '_', sector_id.strip())
            return sector_id.lower()
            
        return None
