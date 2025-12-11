import tweepy
from app.config import Config
import time
import os

def test_twitter_connection():
    print("--------------------------------------------------")
    print("         Twitter Connection Test Utility          ")
    print("--------------------------------------------------")

    # 1. Check Credentials Loading
    print("\n[1] Checking Credentials...")
    api_key = Config.TWITTER_API_KEY
    api_secret = Config.TWITTER_API_SECRET
    access_token = Config.TWITTER_ACCESS_TOKEN
    access_token_secret = Config.TWITTER_ACCESS_TOKEN_SECRET

    if not all([api_key, api_secret, access_token, access_token_secret]):
        print("❌ ERROR: Missing one or more Twitter credentials in .env")
        return

    # Print masked credentials for verification
    print(f"  API Key: {api_key[:4]}...{api_key[-4:] if api_key else 'None'}")
    print(f"  Access Token: {access_token[:4]}...{access_token[-4:] if access_token else 'None'}")
    print("✅ Credentials loaded.")

    # 2. Initialize Client
    print("\n[2] Initializing Tweepy Client...")
    try:
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )
        print("✅ Client initialized.")
    except Exception as e:
        print(f"❌ Error initializing client: {e}")
        return

    # 3. Test Authentication (Get Me - Read Only)
    print("\n[3] Testing Authentication (Read Permission)...")
    try:
        me = client.get_me()
        user_data = me.data
        if user_data:
            print(f"✅ SUCCESS: Authenticated as @{user_data['username']} (ID: {user_data['id']})")
        else:
            print("❌ ERROR: Authenticated but returned no data.")
    except tweepy.errors.Unauthorized as e:
        print(f"❌ 401 Unauthorized: Credentials are invalid. {e}")
        return
    except tweepy.errors.Forbidden as e:
        print(f"❌ 403 Forbidden: App might be suspended or lacking Read permissions. {e}")
        return
    except Exception as e:
        print(f"❌ Error during Auth check: {e}")
        return

    # 4. Test Posting (Write Permission)
    print("\n[4] Testing Posting (Write Permission)...")
    variants = [
        {
            "name": "NO FOOTER (No hashtags/footer emojis)",
            "text": """🦁 ATENÇÃO, TORCIDA!

✍️ O FortalezaEC oficializou a contratação de Leticia Lino!

🆕 A jovem atleta assina contrato até 2028 e chega para reforçar as categorias de base do Leão."""
        },
        {
            "name": "SHORT (Headline only)",
            "text": """🦁 ATENÇÃO, TORCIDA!

✍️ O FortalezaEC oficializou a contratação de Leticia Lino!"""
        },
        {
             "name": "NO EMOJIS (Plain text)",
             "text": """ATENCAO, TORCIDA!

O FortalezaEC oficializou a contratação de Leticia Lino!

A jovem atleta assina contrato até 2028 e chega para reforçar as categorias de base do Leão.

#FortalezaEC #BID #LeaoDoPici"""
        },
        {
            "name": "FOOTER ONLY (Test footer toxicity)",
            "text": """Test Footer Toxicity
            
🔴🔵⚪ #FortalezaEC #BID #LeãoDoPici"""
        }
    ]

    for variant in variants:
        print(f"\n--- Testing usage of: {variant['name']} ---")
        try:
            print(f"  Text: {variant['text'][:50]}...")
            response = client.create_tweet(text=variant['text'])
            print(f"✅ SUCCESS: Tweet posted! ID: {response.data['id']}")
        except tweepy.errors.Forbidden as e:
            print(f"❌ 403 Forbidden: {e}")
            if hasattr(e, 'response'):
                print(f"Response Body: {e.response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        time.sleep(2) # Brief pause
        
    return # End after variants
    
    try:
        # Original single post block (commented out or removed)
        pass
        print(f"  Attempting to post: '{text}'")
        response = client.create_tweet(text=text)
        if response.data and 'id' in response.data:
            print(f"✅ SUCCESS: Tweet posted! ID: {response.data['id']}")
            print("  (You can delete this tweet manually if you wish)")
        else:
            print("❓ Unknown response format.")
    except tweepy.errors.Forbidden as e:
        print(f"❌ 403 Forbidden: {e}")
        print("  !!! This usually means your App settings in Twitter Developer Portal are set to 'Read' instead of 'Read and Write'.")
        print("  !!! Go to https://developer.twitter.com/ -> User authentication settings -> App permissions -> Change to 'Read and Write'.")
        print("  !!! IMPORTANT: After changing permissions, you MUST regenerate Access Token and Secret and update .env.")
    except tweepy.errors.TooManyRequests as e:
        print(f"❌ 429 Too Many Requests: {e}")
    except Exception as e:
        print(f"❌ Error during Post check: {e}")

if __name__ == "__main__":
    test_twitter_connection()
