import os
import requests
from requests_oauthlib import OAuth1
from app.config import Config
import json
import datetime
import base64

def check_limits():
    print("Checking Twitter API Limits...")
    
    api_key = Config.TWITTER_API_KEY
    api_secret = Config.TWITTER_API_SECRET
    
    if not api_key or not api_secret:
        print("Error: Missing Twitter API Key/Secret.")
        return

    # 1. Get Bearer Token (App-Only Auth)
    bearer_token = None
    try:
        print("--- Authenticating (App-Only) ---")
        # specific logic to get bearer token
        credentials = f"{api_key}:{api_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        token_url = "https://api.twitter.com/oauth2/token"
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
        }
        data = {"grant_type": "client_credentials"}
        
        resp = requests.post(token_url, headers=headers, data=data)
        if resp.status_code == 200:
            bearer_token = resp.json().get("access_token")
            print("Bearer Token obtained successfully.")
        else:
            print(f"Failed to get Bearer Token: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"Error getting bearer token: {e}")

    # 2. Check Usage Endpoint with Bearer Token
    if bearer_token:
        usage_url = "https://api.twitter.com/2/usage/tweets"
        print(f"\n--- Requesting {usage_url} ---")
        try:
            headers = {"Authorization": f"Bearer {bearer_token}"}
            response = requests.get(usage_url, headers=headers)
            print(f"Status Code: {response.status_code}")
            
            # Print headers of interest
            print("Headers:")
            for k, v in response.headers.items():
                if 'rate-limit' in k.lower():
                    print(f"  {k}: {v}")
            
            if response.status_code == 200:
                data = response.json()
                print("\nUsage Data:")
                print(json.dumps(data, indent=2))
            else:
                print(f"\nResponse Body: {response.text}")
                
        except Exception as e:
            print(f"Error accessing usage endpoint: {e}")
    else:
        print("Skipping usage check due to missing Bearer Token.")

if __name__ == "__main__":
    check_limits()
