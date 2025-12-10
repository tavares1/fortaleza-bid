import time

class EnrichAthleteUseCase:
    def __init__(self, cbf_service, gemini_service, repository):
        self.cbf_service = cbf_service
        self.gemini_service = gemini_service
        self.repository = repository

    def execute(self, athlete, max_retries=5):
        """
        Fetches history for a single athlete and saves it (upsert).
        """
        codigo_atleta = athlete.get('codigo_atleta')
        if not codigo_atleta:
            print("[EnrichUseCase] Skipping athlete without 'codigo_atleta'.")
            return False

        # Check if we already have history for this contract
        if self.repository.has_history_for_contract(athlete):
            print(f"[EnrichUseCase] Skipping enrichment for {athlete.get('nome', 'Unknown')} (already exists).")
            return True

        print(f"\n[EnrichUseCase] Enriching: {athlete.get('nome', 'Unknown')} ({codigo_atleta})...")

        history_data = None
        for attempt in range(max_retries):
            try:
                # 1. Fetch Captcha
                b64_hist = self.cbf_service.get_captcha_base64()
                cap_hist = self.gemini_service.solve_captcha(b64_hist)
                
                # 2. Fetch History
                history_resp = self.cbf_service.get_atleta_historico(codigo_atleta, cap_hist)
                
                if history_resp is not None:
                    history_data = history_resp
                    break
                else:
                    print(f"[EnrichUseCase] History fetch failed (attempt {attempt+1}). Retrying...")
                    time.sleep(1)
            except Exception as e:
                print(f"[EnrichUseCase] Error: {e}")
                time.sleep(1)
        
        if history_data:
            # Merge
            athlete['historico'] = history_data
            
            # Save
            self.repository.save_contract_with_history(athlete)
            print("[EnrichUseCase] History merged and saved.")
            return True
        else:
            print(f"[EnrichUseCase] Failed to fetch history for {codigo_atleta}.")
            return False
