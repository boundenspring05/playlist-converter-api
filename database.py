from pymongo import MongoClient
from dotenv import load_dotenv
import os
from typing import Optional
from models import Song

load_dotenv()

class Database:
    def __init__(self):
        self.client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
        self.db = self.client.playlist_db
        self.playlists = self.db.playlists
        
        self.playlists.create_index("name")
        self.playlists.create_index("platform")
        self.playlists.create_index("songs.title")
    
    def get_playlist(self, name: str) -> Optional[dict]:
        return self.playlists.find_one({"name": name})
    
    def store_playlist(self, playlist: dict):
        self.playlists.update_one(
            {"name": playlist["name"]}, 
            {"$set": playlist}, 
            upsert=True
        )
    
    def get_all_playlists(self) -> list:
        cursor = self.playlists.find({}, {"name": 1, "platform": 1, "_id": 0})
        return list(cursor)
    
    def add_song(self, playlist_name: str, song: dict):
        self.playlists.update_one(
            {"name": playlist_name},
            {"$push": {"songs": song}}
        )
    
    def remove_song(self, playlist_name: str, song_title: str):
        result = self.playlists.update_one(
            {"name": playlist_name},
            {"$pull": {"songs": {"title": song_title}}}
        )
        return result.modified_count > 0

db = Database()
