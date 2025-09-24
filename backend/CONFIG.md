# Backend Configuration Guide

## Overview
The backend uses a consolidated configuration system based on Pydantic Settings. All configuration is managed in `app/config.py`.

## Database Configuration

### Supabase Connection
The system is configured to use your Supabase database:

```python
DATABASE_URL = "postgresql://postgres:godoflaw@#2002G@db.rpnbdoamiobuxazedaoe.supabase.co:5432/postgres"
```

**To update with your own Supabase credentials:**
1. Edit `app/config.py`
2. Replace the `DATABASE_URL` in the `DATABASE_URL` property
3. Update `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_ROLE_KEY` if needed

## Environment Settings

### Development vs Production
- **Development**: SQL query logging enabled, smaller connection pool
- **Production**: Optimized settings, connection validation, recycling

Set environment with:
```bash
export ENVIRONMENT=production
```

## Optimization Parameters

### Fleet Constraints
```python
ACTIVE_MIN = 7        # Minimum active trains
ACTIVE_MAX = 9        # Maximum active trains
STANDBY_MIN = 1       # Minimum standby reserve
```

### Service Schedule
```python
SERVICE_HOURS = 16.5      # Daily service hours
NIGHT_START_HOUR = 21     # IBL window start
NIGHT_END_HOUR = 5        # IBL window end
IBL_TIME_STEP_MIN = 10    # IBL scheduling resolution
```

### Optimization Weights
```python
W_RISK = 1.0      # Safety and reliability
W_BRAND = 0.6     # Branding commitments
W_MILEAGE = 0.2   # Fleet balancing
W_CLEAN = 0.4     # Maintenance scheduling
W_SHUNT = 0.15    # Operational efficiency
W_OVERRIDE = 3.0  # Manual override penalty
```

## CORS Settings
```python
CORS_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]
```

Add your frontend URLs here.

## Data Directories
```python
DATA_DIR = "data"           # Root data directory
CSV_UPLOAD_DIR = "data/input"  # CSV upload location
```

## Usage Examples

### In Code
```python
from app.config import settings

# Access settings
db_url = settings.DATABASE_URL
is_dev = settings.is_development()
log_level = settings.get_log_level()

# Check environment
if settings.is_production():
    # Production-specific logic
    pass
```

### Environment Variables
You can override any setting with environment variables:
```bash
export ACTIVE_MIN=8
export ENVIRONMENT=production
export SUPABASE_URL=https://your-project.supabase.co
```

## File Structure
```
backend/
├── app/
│   ├── config.py          # Main configuration
│   ├── database.py        # Database setup
│   └── models/            # All data models
├── data/                  # Data files
│   ├── input/            # CSV uploads
│   └── processed/        # Processed data
└── requirements.txt      # Python dependencies
```

## Database Setup
1. Ensure your Supabase database is running
2. Run the database schema: `database/db.sql`
3. Test connection: `python setup_data.py`

## Troubleshooting
- **Connection errors**: Check DATABASE_URL in config.py
- **Permission errors**: Verify Supabase credentials
- **Pool errors**: Adjust pool settings in database.py
- **CORS errors**: Add your frontend URL to CORS_ORIGINS
