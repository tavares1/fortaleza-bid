
import os
import sys
import base64
import requests
import json
from datetime import datetime
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pymongo import MongoClient

# Load environment variables
load_dotenv()

def get_env_var(name, required=True):
    value = os.getenv(name)
    if not value and required:
        print(f"Error: Environment variable {name} not set.")
        # Don't exit immediately if it's MONGO_URI, handled later or default
    return value

def get_mongo_client():
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    try:
        client = MongoClient(mongo_uri)
        # Test connection
        client.admin.command('ping')
        print("Connected to MongoDB.")
        return client
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None

def get_captcha_base64(session):
    url = 'https://bid.cbf.com.br/get-captcha-base64'
    
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'pt-BR,pt;q=0.7',
        'Connection': 'keep-alive',
        'Referer': 'https://bid.cbf.com.br/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-GPC': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'sec-ch-ua': '"Brave";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"'
    }

    try:
        # Session handles cookies automatically
        response = session.get(url, headers=headers)
        response.raise_for_status()
        
        # Check for X-CSRF-TOKEN in response headers (token rotation)
        new_token = response.headers.get('X-CSRF-TOKEN')
        if new_token:
            print(f"New CSRF Token received in captcha response: {new_token}")
            session.headers.update({'X-CSRF-TOKEN': new_token})
        
        # Print received cookies for debugging
        if session.cookies:
            print("Cookies received from captcha endpoint:")
            for name, value in session.cookies.items():
                print(f"{name}: {value}")
        
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching captcha: {e}")
        sys.exit(1)

def solve_captcha_with_gemini(base64_image_str):
    api_key = get_env_var('GOOGLE_API_KEY')
    
    client = genai.Client(api_key=api_key)

    # Decode base64 to ensure it is valid image data
    clean_base64 = base64_image_str.strip('"').strip()
    
    try:
        image_bytes = base64.b64decode(clean_base64)
    except Exception as e:
        print(f"Error decoding base64: {e}")
        sys.exit(1)
    
    prompt = "What is the text in this captcha image? Return ONLY the text."

    import time
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=[
                    types.Part.from_text(text=prompt),
                    types.Part.from_bytes(data=image_bytes, mime_type="image/png")
                ]
            )
            return response.text.strip()
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                print(f"Quota exceeded (429). Retrying in 10 seconds... (Attempt {attempt+1}/{max_retries})")
                time.sleep(10)
            else:
                print(f"Error calling Gemini: {e}")
                sys.exit(1)

def perform_search(session, captcha_text):
    url = 'https://bid.cbf.com.br/busca-json'
    
    # Dynamic date: Current date formatted as DD/MM/YYYY
    # Allow overriding via environment variable, default to today
    current_date = os.getenv('SEARCH_DATE', datetime.now().strftime('%d/%m/%Y'))
    
    payload = {
        'data': current_date,
        'uf': 'CE',
        'codigo_clube': '63238',
        'captcha': captcha_text
    }
    
    print(f"Performing search with payload: {payload}")

    
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'pt-BR,pt;q=0.7',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://bid.cbf.com.br',
        'Referer': 'https://bid.cbf.com.br/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-GPC': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'sec-ch-ua': '"Brave";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    

    try:
        response = session.post(url, headers=headers, data=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error performing search: {e}")
        try:
            error_json = e.response.json()
            if 'message' in error_json:
                print(f"Server Message: {error_json.get('message')}")
            if 'errors' in error_json:
                print(f"Validation Errors: {error_json.get('errors')}")
        except:
            print(f"Response content: {e.response.text[:500]}...")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error performing search: {e}")
        return None
    except json.JSONDecodeError:
        print("Error decoding JSON response. Response was not valid JSON.")
        print(f"Response text: {response.text[:500]}...")
        return None

def save_results(results):
    if not results:
        print("No results to save.")
        return

    client = get_mongo_client()
    if not client:
        print("Skipping DB save due to connection error.")
        return

    db = client['cbf_data']
    collection = db['contracts']

    saved_count = 0
    for item in results:
        contract_id = item.get('id_contrato')
        if not contract_id:
            continue
        
        # Check if exists
        exists = collection.find_one({'id_contrato': contract_id})
        if not exists:
            collection.insert_one(item)
            saved_count += 1
            print(f"Saved new contract: {item.get('nome')} ({contract_id})")
        else:
            # Optional: Update if needed? User said "save results that are different".
            # Assuming 'different' means 'new' for now, or we could diff fields.
            # Simple approach: if ID exists, ignore.
            pass
            
    print(f"Total new items saved: {saved_count}")

def main():
    session = requests.Session()
    
    # 1. Hit main page to get initial cookies and CSRF token
    print("Visiting home page to initialize session and get CSRF token...")
    try:
        response = session.get('https://bid.cbf.com.br/')
        response.raise_for_status()
        
        # Extract CSRF token
        import re
        match = re.search(r'<meta name="csrf-token" content="([^"]+)">', response.text)
        if match:
            csrf_token = match.group(1)
            print(f"CSRF Token found: {csrf_token}")
            # Set the token in session headers so it's sent with every subsequent request
            session.headers.update({'X-CSRF-TOKEN': csrf_token})
        else:
            print("Warning: Could not find CSRF token in homepage.")
            
    except Exception as e:
        print(f"Error visiting homepage: {e}")

    # 2. Fetch Captcha
    print("Fetching captcha...")
    base64_str = get_captcha_base64(session)
    
    print("Captcha fetched (length: {}). Solving...".format(len(base64_str)))
    
    # 3. Solve Captcha
    captcha_text = solve_captcha_with_gemini(base64_str)
    print(f"CAPTCHA SOLVED: {captcha_text}")
    
    # 4. Perform Search
    print("Performing search...")
    # remove captcha_text from perform_search call if deemed unnecessary or refactor perform_search to just use session headers
    # but the implementation of perform_search uses session, so it will inherit the header.
    results = perform_search(session, captcha_text)
    
    if results:
        print(f"Search successful. Found {len(results)} items.")
        
        # 5. Save Results
        save_results(results)
    else:
        print("Search failed or returned no results.")

if __name__ == "__main__":
    main()