import pytest
from app.monitor.diff import SnapshotComparator

class TestSnapshotComparator:
    """Test cases for snapshot comparison functionality"""
    
    def setup_method(self):
        self.comparator = SnapshotComparator()
    
    def test_no_changes(self):
        """Test when there are no changes between snapshots"""
        previous = {"sector_a", "sector_b", "sector_c"}
        current = {"sector_a", "sector_b", "sector_c"}
        
        result = self.comparator.detect_changes(previous, current)
        
        assert not result['has_changes']
        assert len(result['new_sectors']) == 0
        assert len(result['removed_sectors']) == 0
        assert len(result['unchanged_sectors']) == 3
        
    def test_new_sectors_added(self):
        """Test when new sectors are added"""
        previous = {"sector_a", "sector_b"}
        current = {"sector_a", "sector_b", "sector_c", "sector_d"}
        
        result = self.comparator.detect_changes(previous, current)
        
        assert result['has_changes']
        assert set(result['new_sectors']) == {"sector_c", "sector_d"}
        assert len(result['removed_sectors']) == 0
        assert set(result['unchanged_sectors']) == {"sector_a", "sector_b"}
        
    def test_sectors_removed(self):
        """Test when sectors are removed"""
        previous = {"sector_a", "sector_b", "sector_c"}
        current = {"sector_a"}
        
        result = self.comparator.detect_changes(previous, current)
        
        assert result['has_changes']
        assert len(result['new_sectors']) == 0
        assert set(result['removed_sectors']) == {"sector_b", "sector_c"}
        assert set(result['unchanged_sectors']) == {"sector_a"}
        
    def test_mixed_changes(self):
        """Test when both sectors are added and removed"""
        previous = {"sector_a", "sector_b", "sector_c"}
        current = {"sector_a", "sector_d", "sector_e"}
        
        result = self.comparator.detect_changes(previous, current)
        
        assert result['has_changes']
        assert set(result['new_sectors']) == {"sector_d", "sector_e"}
        assert set(result['removed_sectors']) == {"sector_b", "sector_c"}
        assert set(result['unchanged_sectors']) == {"sector_a"}
        
    def test_empty_previous_snapshot(self):
        """Test when previous snapshot is empty (first run)"""
        previous = set()
        current = {"sector_a", "sector_b"}
        
        result = self.comparator.detect_changes(previous, current)
        
        assert result['has_changes']
        assert set(result['new_sectors']) == {"sector_a", "sector_b"}
        assert len(result['removed_sectors']) == 0
        assert len(result['unchanged_sectors']) == 0
        
    def test_should_send_alert_with_new_sectors(self):
        """Test alert should be sent when new sectors are available"""
        change_info = {
            'new_sectors': ['sector_a', 'sector_b'],
            'removed_sectors': []
        }
        
        assert self.comparator.should_send_alert(change_info)
        
    def test_should_not_send_alert_without_new_sectors(self):
        """Test alert should not be sent when no new sectors"""
        change_info = {
            'new_sectors': [],
            'removed_sectors': ['sector_a']
        }
        
        assert not self.comparator.should_send_alert(change_info)
