import requests
from app.config import Config
from app.services.social.social_provider import SocialProvider

class ThreadsService(SocialProvider):
    def __init__(self):
        self.user_id = Config.THREADS_USER_ID
        self.access_token = Config.THREADS_ACCESS_TOKEN
        self.base_url = "https://graph.threads.net/v1.0"
    
    @property
    def name(self) -> str:
        return "threads"

    def publish(self, text: str) -> str | None:
        if not self.user_id or not self.access_token:
            print("[ThreadsService] Missing credentials (user_id or access_token). DRY RUN.")
            print("--------------------------------------------------")
            print(f"[DRY RUN - THREADS]: {text}")
            print("--------------------------------------------------")
            return "dry_run_threads_id"

        # Step 1: Create Container
        container_id = self._create_container(text)
        if not container_id:
            return None
        
        # Step 2: Publish Container
        post_id = self._publish_container(container_id)
        return post_id

    def _create_container(self, text: str) -> str | None:
        url = f"{self.base_url}/{self.user_id}/threads"
        params = {
            "media_type": "TEXT",
            "text": text,
            "access_token": self.access_token
        }
        
        try:
            response = requests.post(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("id")
        except Exception as e:
            print(f"[ThreadsService] Error creating container: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            return None

    def _publish_container(self, container_id: str) -> str | None:
        url = f"{self.base_url}/{self.user_id}/threads_publish"
        params = {
            "creation_id": container_id,
            "access_token": self.access_token
        }
        
        try:
            response = requests.post(url, params=params)
            response.raise_for_status()
            data = response.json()
            print(f"[ThreadsService] Published successfully! ID: {data.get('id')}")
            return data.get("id")
        except Exception as e:
            print(f"[ThreadsService] Error publishing container: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            return None
