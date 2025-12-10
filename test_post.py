import tweepy
from app.config import Config
import time

def test_post():
    print("Initializing Twitter Client for simple post test...")
    client = tweepy.Client(
        consumer_key=Config.TWITTER_API_KEY,
        consumer_secret=Config.TWITTER_API_SECRET,
        access_token=Config.TWITTER_ACCESS_TOKEN,
        access_token_secret=Config.TWITTER_ACCESS_TOKEN_SECRET
    )

    text = f"Test tweet from API {int(time.time())}"
    print(f"Attempting to post: {text}")

    try:
        response = client.create_tweet(text=text)
        print(f"SUCCESS. ID: {response.data['id']}")
    except tweepy.errors.TooManyRequests as e:
        print(f"429 Limit Exceeded: {e}")
        if hasattr(e, 'response'):
            print(f"Headers: {e.response.headers}")
            print(f"Body: {e.response.text}")
    except Exception as e:
        print(f"Error: {e}")
        if hasattr(e, 'response'):
            print(f"Body: {e.response.text}")

if __name__ == "__main__":
    test_post()
