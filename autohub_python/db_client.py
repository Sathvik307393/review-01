import os
import json
import uuid
from threading import Lock

class LocalCollection:
    def __init__(self, filename):
        self.filepath = filename
        self.lock = Lock()
        if not os.path.exists(self.filepath):
            self.save([])

    def load(self):
        with self.lock:
            try:
                if os.path.exists(self.filepath):
                    with open(self.filepath, 'r') as f:
                        return json.load(f)
            except Exception as e:
                print(f"Error loading {self.filepath}: {e}")
            return []

    def save(self, data):
        with self.lock:
            try:
                with open(self.filepath, 'w') as f:
                    json.dump(data, f, indent=2)
            except Exception as e:
                print(f"Error saving {self.filepath}: {e}")

    def insert_one(self, document):
        if "_id" not in document:
            document["_id"] = str(uuid.uuid4())
        data = self.load()
        data.append(document)
        self.save(data)
        return document

    def find(self, filter_dict=None):
        data = self.load()
        if not filter_dict:
            return data
        results = []
        for doc in data:
            match = True
            for k, v in filter_dict.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                results.append(doc)
        return results

    def find_one(self, filter_dict):
        data = self.load()
        for doc in data:
            match = True
            for k, v in filter_dict.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                return doc
        return None

    def update_one(self, filter_dict, update_dict):
        data = self.load()
        updated = False
        for doc in data:
            match = True
            for k, v in filter_dict.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                set_data = update_dict.get("$set", update_dict)
                for uk, uv in set_data.items():
                    doc[uk] = uv
                updated = True
                break
        if updated:
            self.save(data)
        return updated

    def delete_one(self, filter_dict):
        data = self.load()
        index_to_delete = -1
        for i, doc in enumerate(data):
            match = True
            for k, v in filter_dict.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                index_to_delete = i
                break
        if index_to_delete != -1:
            data.pop(index_to_delete)
            self.save(data)
            return True
        return False

    def count_documents(self, filter_dict=None):
        return len(self.find(filter_dict))


class MongoCollectionWrapper:
    def __init__(self, collection):
        self.collection = collection

    def find(self, filter_dict=None):
        if filter_dict is None:
            filter_dict = {}
        cursor = self.collection.find(filter_dict)
        results = []
        for doc in cursor:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results

    def find_one(self, filter_dict):
        doc = self.collection.find_one(filter_dict)
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return doc

    def insert_one(self, document):
        if "_id" not in document:
            import uuid
            document["_id"] = str(uuid.uuid4())
        self.collection.insert_one(document)
        return document

    def update_one(self, filter_dict, update_dict):
        result = self.collection.update_one(filter_dict, update_dict)
        return result.modified_count > 0 or result.matched_count > 0

    def delete_one(self, filter_dict):
        result = self.collection.delete_one(filter_dict)
        return result.deleted_count > 0

    def count_documents(self, filter_dict=None):
        if filter_dict is None:
            filter_dict = {}
        return self.collection.count_documents(filter_dict)


class DBClient:
    def __init__(self):
        self.mongo_uri = os.environ.get("MONGO_URI")
        self.client = None
        self.db = None
        self.use_mongo = False

        if self.mongo_uri:
            try:
                import pymongo
                self.client = pymongo.MongoClient(self.mongo_uri, serverSelectionTimeoutMS=2000)
                # Quick test connection
                self.client.server_info()
                self.db = self.client.get_database("autohub")
                self.use_mongo = True
                print("Connected to AWS/Remote MongoDB successfully.")
            except Exception as e:
                print(f"MongoDB connection failed: {e}. Falling back to file-based database.")
        else:
            print("No MONGO_URI specified. Using persistent local JSON files as database.")

    def get_collection(self, name):
        if self.use_mongo:
            # Wrap standard PyMongo collection wrapper to ensure compatible API
            return MongoCollectionWrapper(self.db[name])
        else:
            filename = f"db_{name}.json"
            return LocalCollection(filename)

# Global DB instance
db_client = DBClient()

def get_db_collection(name):
    return db_client.get_collection(name)
