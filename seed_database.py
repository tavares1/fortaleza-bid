import time
from datetime import datetime, timedelta
from app.services.cbf_service import CBFService
from app.services.gemini_service import GeminiService
from app.models.contract_repository import ContractRepository

def generate_date_range(start_date_str, end_date_str):
    start_date = datetime.strptime(start_date_str, "%d/%m/%Y")
    end_date = datetime.strptime(end_date_str, "%d/%m/%Y")
    
    delta = end_date - start_date
    
    date_list = []
    for i in range(delta.days + 1):
        day = start_date + timedelta(days=i)
        date_list.append(day.strftime("%d/%m/%Y"))
    return date_list

def main():
    start_date = "01/11/2025"
    end_date = "09/12/2025"
    
    print(f"Starting seed process from {start_date} to {end_date}...")
    
    dates = generate_date_range(start_date, end_date)
    print(f"Total dates to process: {len(dates)}")
    
    cbf_service = CBFService()
    gemini_service = GeminiService()
    repository = ContractRepository()
    
    # Initialize session once
    cbf_service.initialize_session()
    
    for i, date_str in enumerate(dates):
        print(f"\nProcessing date: {date_str} ({i+1}/{len(dates)})")
        
        try:
            # 1. Fetch Captcha
            print("Fetching captcha...")
            base64_str = cbf_service.get_captcha_base64()
            
            # 2. Solve Captcha
            print("Solving captcha...")
            captcha_text = gemini_service.solve_captcha(base64_str)
            print(f"CAPTCHA SOLVED: {captcha_text}")
            
            # 3. Perform Search with specific date
            print(f"Searching for contracts on {date_str}...")
            results = cbf_service.perform_search(captcha_text, search_date=date_str)
            
            # 4. Save Results
            if results:
                print(f"Found {len(results)} items.")
                repository.save_contracts(results)
            else:
                print("No results found or search failed.")
                
        except Exception as e:
            print(f"Error processing {date_str}: {e}")
            
        if i < len(dates) - 1:
            print("Waiting 1 minute to respect rate limits...")
            time.sleep(60)
            
    print("\nSeed process completed!")

if __name__ == "__main__":
    main()
