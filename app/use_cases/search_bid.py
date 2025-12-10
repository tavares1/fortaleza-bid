import time

class SearchBidUseCase:
    def __init__(self, cbf_service, gemini_service):
        self.cbf_service = cbf_service
        self.gemini_service = gemini_service

    def execute(self, max_retries=10):
        """
        Executes the search process: Fetch Captcha -> Solve -> Search.
        Returns a list of results (athletes) or None if search failed after retries.
        """
        print("\n[SearchUseCase] Starting search process...")
        
        for i in range(max_retries):
            # We can let the controller handle rate limiting, or handle it here?
            # Ideally the use case just does "one attempt" or "one logical operation".
            # But since "searching" implies "beating the captcha", the retry loop fits here.
            
            try:
                print(f"[SearchUseCase] Attempt {i+1}/{max_retries}...")
                
                # 1. Fetch Captcha
                base64_str = self.cbf_service.get_captcha_base64()
                
                # 2. Solve Captcha
                captcha_text = self.gemini_service.solve_captcha(base64_str)
                print(f"[SearchUseCase] Captcha Solved: {captcha_text}")
                
                # 3. Perform Search
                results = self.cbf_service.perform_search(captcha_text)
                
                if results is not None:
                    print(f"[SearchUseCase] Success! Found {len(results)} items.")
                    return results
                else:
                    print("[SearchUseCase] Search failed (invalid captcha). Retrying...")
                    time.sleep(1)
            
            except Exception as e:
                print(f"[SearchUseCase] Error: {e}")
                time.sleep(1)
        
        print("[SearchUseCase] Failed to get valid results after max retries.")
        return []
