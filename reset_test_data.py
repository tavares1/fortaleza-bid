from pymongo import MongoClient
from app.config import Config

def reset_one_for_threads():
    print("Connecting to MongoDB...")
    client = MongoClient(Config.MONGO_URI)
    db = client['cbf_data']
    collection = db['contracts']

    # Find one contract that has marked as posted on threads (or any contract)
    # We want to set social_status.threads.posted = False
    
    # Try to find one that was already posted to reset it
    target = collection.find_one({'social_status.threads.posted': True})
    
    if not target:
        print("No posted contracts found. Picking any contract...")
        target = collection.find_one({})
    
    if target:
        print(f"Resetting threads status for: {target.get('nome')} ({target.get('_id')})")
        collection.update_one(
            {'_id': target['_id']},
            {'$set': {'social_status.threads.posted': False}}
        )
        print("Reset complete. Modified 1 document.")
    else:
        print("No contracts found to reset.")

if __name__ == "__main__":
    reset_one_for_threads()
