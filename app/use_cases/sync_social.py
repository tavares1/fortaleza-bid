import time
from app.services.social.social_provider import SocialProvider

class SyncSocialUseCase:
    def __init__(self, repository, gemini_service, providers: list[SocialProvider]):
        self.repository = repository
        self.gemini_service = gemini_service
        self.providers = providers

    def execute(self, limit=5, delay_seconds=65):
        """
        Processes pending posts for all registered social providers.
        """
        print("\n[SyncSocialUseCase] Syncing Pending Posts for all providers ---")
        
        for provider in self.providers:
            platform_name = provider.name
            print(f"\n--- Checking {platform_name} ---")
            
            pending = self.repository.get_pending_posts(platform_name, limit=limit)
             
            if not pending:
                print(f"No pending posts for {platform_name}.")
                continue

            print(f"Found {len(pending)} pending posts for {platform_name}. Processing...")
            
            for i, contract in enumerate(pending):
                try:
                    print(f"Posting {i+1}/{len(pending)}: {contract.get('nome', 'Unknown')} to {platform_name}...")
                    
                    # Generate text - reusing the same logic for all platforms for now
                    # Ideally we might want platform-specific prompts later.
                    post_text = self.gemini_service.generate_tweet_text(contract)
                    
                    post_id = provider.publish(post_text)
                    
                    if post_id:
                        self.repository.mark_as_posted(contract['_id'], platform_name, post_id)
                        print(f"Marked as posted on {platform_name}.")
                        
                        # Rate limit delay between posts on the same platform
                        if i < len(pending) - 1:
                            print(f"Waiting {delay_seconds}s for rate limit safety on {platform_name}...")
                            time.sleep(delay_seconds)
                    else:
                        print(f"Failed to post to {platform_name}.")
                        # Continue to next item or break? 
                        # If simple failure, maybe break to avoid spamming errors if service is down.
                        break
    
                except Exception as e:
                    print(f"Error executing sync for {platform_name}: {e}")
                    break
