from typing import Set, Dict, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SnapshotComparator:
    """Compares sector snapshots to detect changes"""
    
    def __init__(self):
        pass
    
    def detect_changes(self, previous_sectors: Set[str], current_sectors: Set[str]) -> Dict:
        """
        Compare two sector snapshots and detect changes
        
        Args:
            previous_sectors: Set of previously available sector IDs
            current_sectors: Set of currently available sector IDs
            
        Returns:
            Dict with change information
        """
        
        # Calculate differences
        new_sectors = current_sectors - previous_sectors
        removed_sectors = previous_sectors - current_sectors
        unchanged_sectors = current_sectors & previous_sectors
        
        change_info = {
            'has_changes': len(new_sectors) > 0 or len(removed_sectors) > 0,
            'new_sectors': list(new_sectors),
            'removed_sectors': list(removed_sectors), 
            'unchanged_sectors': list(unchanged_sectors),
            'total_previous': len(previous_sectors),
            'total_current': len(current_sectors),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Log the changes
        if change_info['has_changes']:
            logger.info(f"Changes detected:")
            logger.info(f"  New sectors: {len(new_sectors)} - {new_sectors}")
            logger.info(f"  Removed sectors: {len(removed_sectors)} - {removed_sectors}")
            logger.info(f"  Total sectors: {len(previous_sectors)} -> {len(current_sectors)}")
        else:
            logger.info(f"No changes detected. {len(current_sectors)} sectors remain available.")
            
        return change_info
    
    def should_send_alert(self, change_info: Dict) -> bool:
        """
        Determine if an alert should be sent based on change information
        
        Only send alerts for new sectors becoming available (positive delta)
        """
        return len(change_info['new_sectors']) > 0
