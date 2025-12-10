from app.services.cbf_service import CBFService
from app.services.gemini_service import GeminiService
from app.services.twitter_service import TwitterService
from app.models.contract_repository import ContractRepository

class BidController:
    def __init__(self):
        self.cbf_service = CBFService()
        self.gemini_service = GeminiService()
        self.twitter_service = TwitterService()
        self.repository = ContractRepository()

    def run(self):
        import time
        
        # 1. Initialize CBF Session
        self.cbf_service.initialize_session()
        
        requests_count = 0
        max_requests_per_minute = 29
        minute_start_time = time.time()

        while True:
            # Rate Limiting Check
            current_time = time.time()
            elapsed_time = current_time - minute_start_time
            
            if elapsed_time >= 60:
                # Reset counter if a minute has passed
                requests_count = 0
                minute_start_time = time.time()
                print("--- New minute started for rate limiting ---")
            
            if requests_count >= max_requests_per_minute:
                # Wait for the rest of the minute
                wait_time = 60 - elapsed_time + 1 # +1 buffer
                print(f"Rate limit reached ({requests_count}/{max_requests_per_minute}). Waiting {wait_time:.2f} seconds...")
                time.sleep(wait_time)
                # Reset after waiting
                requests_count = 0
                minute_start_time = time.time()
            
            requests_count += 1
            print(f"\nAttempt {requests_count} in current minute...")

            try:
                # 2. Fetch Captcha
                print("Fetching captcha...")
                base64_str = self.cbf_service.get_captcha_base64()
                
                # 3. Solve Captcha
                print("Solving captcha...")
                captcha_text = self.gemini_service.solve_captcha(base64_str)
                print(f"CAPTCHA SOLVED: {captcha_text}")

                # 4. Perform Search
                print("Performing search...")
                results = self.cbf_service.perform_search(captcha_text)

                # Check if results is not None (None means error/invalid captcha)
                # Empty list [] is a valid result (search success but no items found)
                if results is not None:
                    print("Search successful!")
                    break  # Success! Exit loop.
                else:
                    print("Search failed (likely invalid captcha). Retrying...")
                    # Optimization: Short sleep to prevent slam if not strictly rate limited by minute logic
                    time.sleep(1) 
                    
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(1)

        # 5. Process Results (outside loop, as we only get here on success)
        if results:
            print(f"Found {len(results)} items.")
            
            # Save Results
            new_contracts = self.repository.save_contracts(results)
            print(f"Total new items saved: {len(new_contracts)}")

            # 6. Tweet new contracts
            if new_contracts:
                print("Publishing new contracts to Twitter...")
                for contract in new_contracts:
                    tweet_text = self.gemini_service.generate_tweet_text(contract)
                    self.twitter_service.publish(tweet_text)
                    
        else:
            print("Search returned no items (empty).")
