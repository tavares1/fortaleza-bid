from app.services.cbf_service import CBFService
from app.services.gemini_service import GeminiService
from app.services.social.twitter_service import TwitterService
from app.services.social.threads_service import ThreadsService
from app.models.contract_repository import ContractRepository
from app.use_cases.search_bid import SearchBidUseCase
from app.use_cases.enrich_athlete import EnrichAthleteUseCase
from app.use_cases.sync_social import SyncSocialUseCase
import time

class BidController:
    def __init__(self):
        # Initialize Services
        self.cbf_service = CBFService()
        self.gemini_service = GeminiService()
        self.twitter_service = TwitterService()
        self.threads_service = ThreadsService()
        self.repository = ContractRepository()
        
        # Initialize Use Cases
        self.search_use_case = SearchBidUseCase(self.cbf_service, self.gemini_service)
        self.enrich_use_case = EnrichAthleteUseCase(self.cbf_service, self.gemini_service, self.repository)
        
        # Sync Use Case with multiple providers
        self.sync_use_case = SyncSocialUseCase(
            self.repository, 
            self.gemini_service, 
            providers=[self.twitter_service, self.threads_service]
        )

    def run(self):
        # 1. Initialize CBF Session
        self.cbf_service.initialize_session()
        
        requests_count = 0
        max_requests_per_minute = 29
        minute_start_time = time.time()

        def check_rate_limit(count):
            nonlocal minute_start_time
            current_time = time.time()
            elapsed_time = current_time - minute_start_time
            
            if elapsed_time >= 60:
                count = 0
                minute_start_time = time.time()
                print("--- New minute started for rate limiting ---")
            
            if count >= max_requests_per_minute:
                wait_time = 60 - elapsed_time + 1
                if wait_time > 0:
                    print(f"Rate limit reaching ({count}). Waiting {wait_time:.2f}s...")
                    time.sleep(wait_time)
                count = 0
                minute_start_time = time.time()
            
            return count

        # Main Loop
        while True:
            # Rate Limit for Search Step
            requests_count = check_rate_limit(requests_count)
            requests_count += 2 # Captcha + Search estimates
            
            # --- 1. Search ---
            results = self.search_use_case.execute()
            
            # --- 2. Enrich & Save ---
            if results:
                print(f"[Controller] Found {len(results)} items. Starting enrichment...")
                for athlete in results:
                    # Rate limit for Enrichment
                    requests_count = check_rate_limit(requests_count)
                    requests_count += 2 # Captcha + History Fetch estimates
                    
                    self.enrich_use_case.execute(athlete)
            
            else:
                # If no results or failed, wait a bit before next search loop
                print("[Controller] No results or search failed. Waiting before retry...")
                time.sleep(10) # 10s delay between search attempts if empty/fail

            # --- 3. Sync Social Media ---
            # We run sync after each search cycle.
            self.sync_use_case.execute()
            
            # stability delay
            print("[Controller] Cycle complete. Waiting 60s before next search cycle...")
            time.sleep(60)
