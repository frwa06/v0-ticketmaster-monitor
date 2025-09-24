#!/bin/bash

echo "🧪 Running Ticketmaster Monitor Test Suite..."

# Ensure container is running
if ! docker-compose ps | grep -q "ticketmaster-monitor.*Up"; then
    echo "⚠️  Container not running. Starting services..."
    docker-compose up -d
    sleep 10
fi

echo ""
echo "1️⃣ Running unit tests..."
docker-compose exec ticketmaster-monitor python -m pytest tests/ -v --tb=short

echo ""
echo "2️⃣ Testing phone number validation..."
docker-compose exec ticketmaster-monitor python -c "
from app.alerts.sms import SMSAlertService
from app.storage.db import Database

db = Database('sqlite:///:memory:')
sms = SMSAlertService(db)

# Test cases
test_cases = [
    '+573001234567',
    '3001234567', 
    '+57 300 123 4567',
    '123',
    '+5730012345678901234'
]

for phone in test_cases:
    valid, normalized = sms.validate_phone_number(phone)
    print(f'{phone:20} -> Valid: {valid:5} | Normalized: {normalized}')
"

echo ""
echo "3️⃣ Testing snapshot comparison..."
docker-compose exec ticketmaster-monitor python -c "
from app.monitor.diff import SnapshotComparator

comp = SnapshotComparator()

# Test scenarios
scenarios = [
    ({'a', 'b'}, {'a', 'b'}, 'No changes'),
    ({'a', 'b'}, {'a', 'b', 'c'}, 'New sector added'),
    ({'a', 'b', 'c'}, {'a'}, 'Sectors removed'),
    (set(), {'a', 'b'}, 'First run')
]

for prev, curr, desc in scenarios:
    result = comp.detect_changes(prev, curr)
    print(f'{desc:20} -> Changes: {result[\"has_changes\"]:5} | New: {len(result[\"new_sectors\"]):2} | Removed: {len(result[\"removed_sectors\"]):2}')
"

echo ""
echo "4️⃣ Testing sector parsing..."
docker-compose exec ticketmaster-monitor python -c "
from app.monitor.parse import SectorParser

parser = SectorParser()

# Mock sector data
mock_sectors = [
    {'id': 'sector_1', 'aria_label': 'Sector A - Disponible'},
    {'id': 'sector_2', 'aria_label': 'Sector B - No disponible'},
    {'id': 'sector_3', 'class_names': 'sector available'},
    {'id': 'sector_4', 'data_status': 'sold-out'}
]

available = parser.normalize_sectors(mock_sectors)
print(f'Mock sectors processed: {len(mock_sectors)} total -> {len(available)} available')
print(f'Available sectors: {list(available)}')
"

echo ""
echo "✅ Test suite completed!"
