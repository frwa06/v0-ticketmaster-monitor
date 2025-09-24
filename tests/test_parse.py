import pytest
from app.monitor.parse import SectorParser

class TestSectorParser:
    """Test cases for sector parsing functionality"""
    
    def setup_method(self):
        self.parser = SectorParser()
        
    def test_normalize_sectors_with_available_aria_label(self):
        """Test sector normalization with available aria-label"""
        raw_sectors = [
            {
                'id': 'sector_1',
                'aria_label': 'Sector A - Disponible',
                'class_names': 'sector-element'
            },
            {
                'id': 'sector_2', 
                'aria_label': 'Sector B - No disponible',
                'class_names': 'sector-element'
            }
        ]
        
        result = self.parser.normalize_sectors(raw_sectors)
        
        assert len(result) == 1
        assert 'sector_1' in result
        
    def test_normalize_sectors_with_class_names(self):
        """Test sector normalization using class names"""
        raw_sectors = [
            {
                'id': 'sector_1',
                'class_names': 'sector available selectable',
                'aria_label': ''
            },
            {
                'id': 'sector_2',
                'class_names': 'sector disabled unavailable', 
                'aria_label': ''
            }
        ]
        
        result = self.parser.normalize_sectors(raw_sectors)
        
        assert len(result) == 1
        assert 'sector_1' in result
        
    def test_normalize_sectors_with_data_status(self):
        """Test sector normalization using data-status attribute"""
        raw_sectors = [
            {
                'id': 'sector_1',
                'data_status': 'available',
                'aria_label': '',
                'class_names': ''
            },
            {
                'id': 'sector_2',
                'data_status': 'sold-out',
                'aria_label': '',
                'class_names': ''
            }
        ]
        
        result = self.parser.normalize_sectors(raw_sectors)
        
        assert len(result) == 1
        assert 'sector_1' in result
        
    def test_normalize_sectors_with_color_detection(self):
        """Test sector normalization using color-based detection"""
        raw_sectors = [
            {
                'id': 'sector_1',
                'style': 'fill: blue;',
                'aria_label': '',
                'class_names': '',
                'data_status': ''
            },
            {
                'id': 'sector_2',
                'fill': '#cccccc',
                'aria_label': '',
                'class_names': '',
                'data_status': ''
            }
        ]
        
        result = self.parser.normalize_sectors(raw_sectors)
        
        assert len(result) == 1
        assert 'sector_1' in result
        
    def test_extract_sector_id_from_various_sources(self):
        """Test sector ID extraction from different sources"""
        # Test with direct ID
        sector = {'id': 'sector_123'}
        sector_id = self.parser._extract_sector_id(sector)
        assert sector_id == 'sector_123'
        
        # Test with data attribute
        sector = {'data_sector_id': 'SECTION-A1'}
        sector_id = self.parser._extract_sector_id(sector)
        assert sector_id == 'section-a1'
        
        # Test with aria-label
        sector = {'aria_label': 'Sector Premium A'}
        sector_id = self.parser._extract_sector_id(sector)
        assert sector_id == 'sector_premium_a'
        
    def test_extract_sector_id_cleanup(self):
        """Test sector ID cleanup and normalization"""
        sector = {'id': 'Sector A-1 (Premium)!'}
        sector_id = self.parser._extract_sector_id(sector)
        
        # Should remove special characters and normalize
        assert sector_id == 'sector_a-1_premium'
        
    def test_normalize_empty_sectors(self):
        """Test normalization with empty sector list"""
        result = self.parser.normalize_sectors([])
        
        assert len(result) == 0
        assert isinstance(result, set)
