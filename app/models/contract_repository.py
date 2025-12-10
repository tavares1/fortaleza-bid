from pymongo import MongoClient
from app.config import Config

class ContractRepository:
    def __init__(self):
        self.client = self._get_client()
        if self.client:
            self.db = self.client['cbf_data']
            self.collection = self.db['contracts']
        else:
            self.collection = None

    def _get_client(self):
        try:
            client = MongoClient(Config.MONGO_URI)
            client.admin.command('ping')
            print("Connected to MongoDB.")
            return client
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            return None

    def save_contracts(self, contracts):
        """
        Saves a list of contracts to the database.
        Returns a list of inserted contracts (documents that were new).
        """
        if self.collection is None:
            print("Database not connected. Skipping save.")
            return []

        saved_contracts = []
        for item in contracts:
            if not isinstance(item, dict):
                print(f"Skipping invalid item (not a dict): {item}")
                continue

            contract_id = item.get('id_contrato')
            if not contract_id:
                print(f"Skipping item without 'id_contrato': {item}")
                continue
            
            # Check if exists
            exists = self.collection.find_one({'id_contrato': contract_id})
            if not exists:
                self.collection.insert_one(item)
                saved_contracts.append(item)
                print(f"Saved new contract: {item.get('nome')} ({contract_id})")
            else:
                print(f"Contract {contract_id} already exists. Skipping.")
        
        return saved_contracts
