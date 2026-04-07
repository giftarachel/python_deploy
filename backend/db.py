"""
Database layer — uses local JSON file storage as fallback when MongoDB is unavailable.
Automatically tries MongoDB Atlas first, falls back to local storage.
"""

import json, os, uuid
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

_db = None
_use_local = False
_local_path = os.path.join(os.path.dirname(__file__), "local_db.json")


def _load_local():
    if not os.path.exists(_local_path):
        with open(_local_path, "w") as f:
            json.dump({"users": [], "simulations": []}, f)
    with open(_local_path, "r") as f:
        return json.load(f)


def _save_local(data):
    with open(_local_path, "w") as f:
        json.dump(data, f, indent=2, default=str)


class LocalCollection:
    def __init__(self, name):
        self.name = name

    def find_one(self, query):
        data = _load_local()
        for doc in data.get(self.name, []):
            if all(doc.get(k) == v for k, v in query.items()):
                return doc
        return None

    def find(self):
        return LocalCursor(self.name)

    def insert_one(self, doc):
        data = _load_local()
        doc["_id"] = str(uuid.uuid4())
        data.setdefault(self.name, []).append(doc)
        _save_local(data)
        return type("R", (), {"inserted_id": doc["_id"]})()

    def delete_one(self, query):
        data = _load_local()
        original = data.get(self.name, [])
        filtered = [d for d in original if not all(d.get(k) == str(v) for k, v in query.items())]
        deleted = len(original) - len(filtered)
        data[self.name] = filtered
        _save_local(data)
        return type("R", (), {"deleted_count": deleted})()


class LocalCursor:
    def __init__(self, name):
        self.name = name
        self._sort_key = None
        self._sort_dir = -1
        self._limit_n = None
        self._query = {}

    def find(self, query=None):
        self._query = query or {}
        return self

    def sort(self, key, direction):
        self._sort_key = key
        self._sort_dir = direction
        return self

    def limit(self, n):
        self._limit_n = n
        return self

    def __iter__(self):
        data = _load_local()
        docs = data.get(self.name, [])
        if self._query:
            docs = [d for d in docs if all(d.get(k) == v for k, v in self._query.items())]
        if self._sort_key:
            docs = sorted(docs, key=lambda d: d.get(self._sort_key, ""), reverse=(self._sort_dir == -1))
        if self._limit_n:
            docs = docs[:self._limit_n]
        return iter(docs)


class LocalDB:
    def __getitem__(self, name):
        return LocalCollection(name)

    def list_collection_names(self):
        return list(_load_local().keys())


def init_db():
    global _db, _use_local
    uri = os.getenv("MONGO_URI", "")
    if uri:
        try:
            from pymongo import MongoClient
            client = MongoClient(uri, serverSelectionTimeoutMS=4000, connectTimeoutMS=4000)
            client.admin.command("ping")
            _db = client["suspension_sim"]
            _use_local = False
            print("[DB] Connected to MongoDB Atlas")
            return
        except Exception as e:
            print(f"[DB] Atlas unavailable ({str(e)[:60]}), switching to local storage")

    _db = LocalDB()
    _use_local = True
    _load_local()
    print("[DB] Using local file storage (local_db.json)")


def get_db():
    return _db
