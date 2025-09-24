"""
Settings for different environments
Copy and modify these settings for your environment
"""
import os

# Production/Supabase settings
PRODUCTION_SETTINGS = {
    'DATABASE_URL': 'postgresql+asyncpg://postgres:YOUR_SUPABASE_PASSWORD@db.YOUR_PROJECT_REF.supabase.co:5432/postgres',
    'SUPABASE_URL': 'https://YOUR_PROJECT_REF.supabase.co',
    'SUPABASE_ANON_KEY': 'YOUR_SUPABASE_ANON_KEY',
    'SUPABASE_SERVICE_ROLE_KEY': 'YOUR_SUPABASE_SERVICE_ROLE_KEY',
}

# Development/Local settings
DEVELOPMENT_SETTINGS = {
    'DATABASE_URL': 'postgresql+asyncpg://user:pass@localhost:5432/metro',
    'SUPABASE_URL': None,
    'SUPABASE_ANON_KEY': None,
    'SUPABASE_SERVICE_ROLE_KEY': None,
}

# Get environment (default to development)
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development').lower()

if ENVIRONMENT == 'production':
    CURRENT_SETTINGS = PRODUCTION_SETTINGS
else:
    CURRENT_SETTINGS = DEVELOPMENT_SETTINGS

# Update config.py with these settings
def update_config_with_settings():
    """Update the Settings class with environment-specific values"""
    settings_dict = dict(CURRENT_SETTINGS)

    # Override with environment variables if they exist
    for key in CURRENT_SETTINGS.keys():
        env_var = os.getenv(key)
        if env_var:
            settings_dict[key] = env_var

    return settings_dict

# Print current environment for debugging
print(f"Running in {ENVIRONMENT} environment")
print(f"Database: {CURRENT_SETTINGS['DATABASE_URL'].replace('YOUR_SUPABASE_PASSWORD', '***').replace('YOUR_PROJECT_REF', '***')}")
