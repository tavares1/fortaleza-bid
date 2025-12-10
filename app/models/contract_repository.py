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

    def has_history_for_contract(self, contract_data):
        """
        Checks if the contract already exists in the DB and has history data.
        """
        if self.collection is None:
            return False

        query = {}
        if 'contrato_numero' in contract_data:
            query['contrato_numero'] = contract_data['contrato_numero']
        elif 'id_contrato' in contract_data:
            query['id_contrato'] = contract_data['id_contrato']
        else:
            if 'codigo_atleta' in contract_data and 'codigo_clube' in contract_data:
                 query = {
                     'codigo_atleta': contract_data['codigo_atleta'],
                     'codigo_clube': contract_data['codigo_clube']
                 }
            else:
                return False
        
        try:
            # Check for existence AND non-empty 'historico'
            existing = self.collection.find_one(query, {'historico': 1})
            if existing and existing.get('historico'):
                return True
            return False
        except Exception as e:
            print(f"Error checking history existence: {e}")
            return False

    def save_contract_with_history(self, contract_data):
        """
        Saves a single contract with its history.
        Uses upsert to update if exists.
        """
        if self.collection is None:
            print("Database not connected. Skipping save.")
            return False

        if not isinstance(contract_data, dict):
            print(f"Skipping invalid item (not a dict): {contract_data}")
            return False

        # Determine unique identifier
        # User example has 'contrato_numero', existing code used 'id_contrato'
        # we try to use a unique combination.
        
        query = {}
        if 'contrato_numero' in contract_data:
            query['contrato_numero'] = contract_data['contrato_numero']
        elif 'id_contrato' in contract_data:
            query['id_contrato'] = contract_data['id_contrato']
        else:
            # Fallback to athlete code + club? Might not be unique for contract but good enough?
            # Or just skip
            if 'codigo_atleta' in contract_data and 'codigo_clube' in contract_data:
                 query = {
                     'codigo_atleta': contract_data['codigo_atleta'],
                     'codigo_clube': contract_data['codigo_clube']
                 }
            else:
                print(f"Skipping item without ID fields: {contract_data}")
                return False
        
        try:
            # Check if it exists first to know if we are inserting
            existing = self.collection.find_one(query)
            
            # Prepare update data
            update_data = {'$set': contract_data}
            
            # If new, ensure tweeted is False (if not present)
            if not existing:
                if 'tweeted' not in contract_data:
                     update_data['$setOnInsert'] = {'tweeted': False}
                print(f"Inserted new contract/history for {contract_data.get('nome', 'Unknown')}")
            else:
                # If updating, we don't reset tweeted unless we want to re-tweet updates?
                # Usually no.
                print(f"Updated existing contract/history for {contract_data.get('nome', 'Unknown')}")

            result = self.collection.update_one(
                query,
                update_data,
                upsert=True
            )
            
            return True
        except Exception as e:
            print(f"Error saving to MongoDB: {e}")
            return False

    def get_pending_posts(self, platform_name: str, limit=10):
        """
        Retrieves contracts that have not been posted to the specified platform yet.
        """
        if self.collection is None:
            return []
            
        try:
            # check if social_status.{platform_name}.posted is not True
            # We treat missing as not posted.
            query = {
                f'social_status.{platform_name}.posted': {'$ne': True}
            }
            return list(self.collection.find(query).limit(limit))
        except Exception as e:
            print(f"Error fetching pending posts for {platform_name}: {e}")
            return []

    def mark_as_posted(self, contract_id, platform_name: str, post_id=None):
        """
        Marks a contract as posted on a specific platform.
        """
        if self.collection is None:
            return False
            
        try:
            self.collection.update_one(
                {'_id': contract_id},
                {
                    '$set': {
                        f'social_status.{platform_name}.posted': True,
                        f'social_status.{platform_name}.post_id': post_id,
                        f'social_status.{platform_name}.posted_at': Config.SEARCH_DATE # or current time
                    }
                }
            )
            return True
        except Exception as e:
            print(f"Error marking as posted on {platform_name}: {e}")
            return False
