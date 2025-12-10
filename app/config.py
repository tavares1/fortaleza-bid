import os
from dotenv import load_dotenv

load_dotenv()

def get_env_var(name, required=True, default=None):
    value = os.getenv(name, default)
    if not value and required:
        # We'll raise an error or just print a warning depending on severity.
        # For essential services like DB, it might be better to fail early if not handled elsewhere.
        print(f"Warning: Environment variable {name} not set.")
    return value

class Config:
    MONGO_URI = get_env_var('MONGO_URI', required=False, default='mongodb://localhost:27017/')
    GOOGLE_API_KEY = get_env_var('GOOGLE_API_KEY', required=True)
    
    # Twitter Credentials
    TWITTER_API_KEY = get_env_var('TWITTER_API_KEY', required=False)
    TWITTER_API_SECRET = get_env_var('TWITTER_API_SECRET', required=False)
    TWITTER_ACCESS_TOKEN = get_env_var('TWITTER_ACCESS_TOKEN', required=False)
    TWITTER_ACCESS_TOKEN_SECRET = get_env_var('TWITTER_ACCESS_TOKEN_SECRET', required=False)

    # Threads Credentials
    THREADS_USER_ID = get_env_var('THREADS_USER_ID', required=False)
    THREADS_ACCESS_TOKEN = get_env_var('THREADS_ACCESS_TOKEN', required=False)
    
    # Search Config
    SEARCH_DATE = get_env_var('SEARCH_DATE', required=False)
