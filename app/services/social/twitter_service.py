import tweepy
from app.config import Config
from app.services.social.social_provider import SocialProvider

class TwitterService(SocialProvider):
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
            print("Twitter credentials not found. TwitterService will run in DRY RUN mode.")

    @property
    def name(self) -> str:
        return "twitter"

    def publish(self, text: str) -> str | None:
        if self.client:
            try:
                response = self.client.create_tweet(text=text)
                print(f"Tweet published successfully! ID: {response.data['id']}")
                return response.data['id'] # Return ID on success
            except tweepy.errors.TooManyRequests as e:
                print(f"Rate limit exceeded (429): {e}")
                if hasattr(e, 'response'):
                    print(f"Response Headers: {e.response.headers}")
                    print(f"Response Body: {e.response.text}")
                return None
            except tweepy.errors.Forbidden as e:
                print(f"Forbidden (403): {e}")
                if hasattr(e, 'response'):
                    print(f"Response Body: {e.response.text}")
                return None
            except Exception as e:
                print(f"Error publishing tweet: {e}")
                if hasattr(e, 'response'):
                    print(f"Response Body: {e.response.text}")
                return None
        else:
            print("--------------------------------------------------")
            print(f"[DRY RUN - TWITTER]: {text}")
            print("--------------------------------------------------")
            return "dry_run_twitter_id"
