from app.models.contract_repository import ContractRepository
from app.services.gemini_service import GeminiService
from app.services.twitter_service import TwitterService
import time

def main():
    print("Initializing services...")
    repository = ContractRepository()
    gemini_service = GeminiService()
    twitter_service = TwitterService()

    print("Fetching pending tweets...")
    pending = repository.get_pending_tweets(limit=5)
    
    if not pending:
        print("No pending tweets found in MongoDB.")
        return

    print(f"Found {len(pending)} pending tweets. Testing the first one...")
    
    # Process only the first one for testing/validation to avoid spam/rate limits during this manual test
    contract = pending[0]
    
    print(f"--- Processing: {contract.get('nome', 'Unknown')} ---")
    
    try:
        print("Generating tweet text...")
        tweet_text = gemini_service.generate_tweet_text(contract)
        print(f"Generated Text:\n{tweet_text}\n")
        
        print("Publishing to Twitter...")
        # Note: If rate limited previously, this might fail with 429
        tweet_id = twitter_service.publish(tweet_text)
        
        if tweet_id:
            print(f"SUCCESS! Tweet published. ID: {tweet_id}")
            repository.mark_as_tweeted(contract['_id'], tweet_id)
            print("Marked as tweeted in DB.")
        else:
            print("FAILED to publish tweet (Check logs/rate limits).")

    except Exception as e:
        print(f"An error occurred during testing: {e}")

if __name__ == "__main__":
    main()
