from app.models.contract_repository import ContractRepository
from app.services.gemini_service import GeminiService
from app.services.social.twitter_service import TwitterService
from app.services.social.threads_service import ThreadsService
from app.use_cases.sync_social import SyncSocialUseCase
import time

def main():
    print("Initializing services for SOCIAL SYNC TEST...")
    repository = ContractRepository()
    gemini_service = GeminiService()
    
    # Initialize Providers
    twitter_service = TwitterService()
    threads_service = ThreadsService()

    # Manual Dependency Injection
    sync_use_case = SyncSocialUseCase(
        repository,
        gemini_service,
        providers=[twitter_service, threads_service]
    )

    print("Fetching pending posts (Checking generic pending for both providers via use case logic)...")
    
    # We will let the use case allow fetching from DB.
    # Logic in use case iterates providers.
    
    try:
        sync_use_case.execute(limit=1, delay_seconds=5) 
        # Limit 1 per provider to be quick. Delay 5s to be quick.
    except Exception as e:
        print(f"Error during test: {e}")

if __name__ == "__main__":
    main()
