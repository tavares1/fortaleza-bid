import tweepy
from app.config import Config

class TwitterService:
    def __init__(self):
        self.api_key = Config.TWITTER_API_KEY
        self.api_secret = Config.TWITTER_API_SECRET
        self.access_token = Config.TWITTER_ACCESS_TOKEN
        self.access_token_secret = Config.TWITTER_ACCESS_TOKEN_SECRET
        
        self.client = None
        if self.api_key and self.api_secret and self.access_token and self.access_token_secret:
            try:
                self.client = tweepy.Client(
                    consumer_key=self.api_key,
                    consumer_secret=self.api_secret,
                    access_token=self.access_token,
                    access_token_secret=self.access_token_secret
                )
                print("Twitter client initialized.")
            except Exception as e:
                print(f"Error initializing Twitter client: {e}")
        else:
            print("Twitter credentials not found. TwitterService will run in DRY RUN mode (printing tweets only).")

    def publish(self, text):
        if self.client:
            try:
                response = self.client.create_tweet(text=text)
                print(f"Tweet published successfully! ID: {response.data['id']}")
                return True
            except Exception as e:
                print(f"Error publishing tweet: {e}")
                return False
        else:
            print("--------------------------------------------------")
            print(f"[DRY RUN - TWEET]: {text}")
            print("--------------------------------------------------")
            return True
