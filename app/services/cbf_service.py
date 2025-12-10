import requests
import re
import sys
import json
from datetime import datetime
from app.config import Config

class CBFService:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = 'https://bid.cbf.com.br/'

    def initialize_session(self):
        print("Visiting home page to initialize session and get CSRF token...")
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            
            match = re.search(r'<meta name="csrf-token" content="([^"]+)">', response.text)
            if match:
                csrf_token = match.group(1)
                print(f"CSRF Token found: {csrf_token}")
                self.session.headers.update({'X-CSRF-TOKEN': csrf_token})
            else:
                print("Warning: Could not find CSRF token in homepage.")
                
        except Exception as e:
            print(f"Error visiting homepage: {e}")

    def get_captcha_base64(self):
        url = f'{self.base_url}get-captcha-base64'
        
        headers = {
            'Accept': '*/*',
            'Accept-Language': 'pt-BR,pt;q=0.7',
            'Connection': 'keep-alive',
            'Referer': self.base_url,
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
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            
            new_token = response.headers.get('X-CSRF-TOKEN')
            if new_token:
                print(f"New CSRF Token received in captcha response: {new_token}")
                self.session.headers.update({'X-CSRF-TOKEN': new_token})
            
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching captcha: {e}")
            sys.exit(1)

    def perform_search(self, captcha_text, search_date=None):
        url = f'{self.base_url}busca-json'
        
        current_date = search_date or Config.SEARCH_DATE or datetime.now().strftime('%d/%m/%Y')
        
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
            'Referer': self.base_url,
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
            response = self.session.post(url, headers=headers, data=payload)
            response.raise_for_status()
            
            data = response.json()
            
            if isinstance(data, dict):
                print(f"Search response is a dictionary with keys: {list(data.keys())}")
                
                # Check for explicit failure
                if data.get('status') is False:
                    print(f"Search failed with messages: {data.get('messages')}")
                    return None

                # Common CBF pattern: list might be in 'objects' or similar
                if 'objects' in data:
                    print(f"Found 'objects' key with {len(data['objects'])} items. Using that.")
                    return data['objects']
                
                # Log content if it's small or error-like
                print(f"Response content (partial): {str(data)[:200]}")
                
            elif isinstance(data, list):
                print(f"Search response is a list of {len(data)} items.")
            else:
                print(f"Search response is of type {type(data)}")

            return data

        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error performing search: {e}")
            try:
                print(f"Response text: {e.response.text}")
            except:
                pass
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error performing search: {e}")
            return None
        except json.JSONDecodeError:
            print("Error decoding JSON response.")
            return None

    def get_atleta_historico(self, codigo_atleta, captcha_text):
        url = f'{self.base_url}atleta-historico-json'
        
        headers = {
            'Accept': '*/*',
            'Accept-Language': 'pt-BR,pt;q=0.7',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://bid.cbf.com.br',
            'Referer': f'https://bid.cbf.com.br/atleta-competicoes/{codigo_atleta}',
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

        payload = {
            'codigo_atleta': codigo_atleta,
            'captcha': captcha_text
        }

        print(f"Fetching history for athlete {codigo_atleta}...")

        try:
            response = self.session.post(url, headers=headers, data=payload)
            response.raise_for_status()
            
            data = response.json()
            # The response seems to be the 'historico' object directly or contained within.
            # Based on user payload: "historico": { "2025": [...], ... }
            # Let's assume the response IS the structure that goes into "historico" or similar.
            # Actually, typically these endpoints return the data structure directly. 
            # If the user says: "O endpoint busca-json será responsável por trazer o array de items como é hoje... E o novo model... historico: { ... }"
            # It implies we take the response of this endpoint and put it into 'historico' key.
            return data

        except requests.exceptions.RequestException as e:
            print(f"Error fetching athlete history: {e}")
            return None
        except json.JSONDecodeError:
            print("Error decoding JSON history response.")
            return None
