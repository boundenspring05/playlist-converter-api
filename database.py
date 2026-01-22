import motor.motor_asyncio
from dotenv import load_dotenv
import os
from typing import Optional
from models import Song

load_dotenv()

class Database:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGO_URI"))
        self.db = self.client.playlist_db
        self.playlists = self.db.playlists
        
    
    async def create_indexes(self):
        await self.playlists.create_index("name")
        await self.playlists.create_index("platform")
        await self.playlists.create_index("songs.title")
    
    async def get_playlist(self, name: str) -> Optional[dict]:
        return await self.playlists.find_one({"name": name})
    
    async def get_playlist_song_count(self, playlist_name: str) -> int:
        doc = await self.get_playlist(playlist_name)
        return len(doc.get("songs", [])) if doc else 0

    async def store_playlist(self, playlist: dict):
        await self.playlists.update_one(
            {"name": playlist["name"]}, 
            {"$set": playlist}, 
            upsert=True
        )
    
    async def get_all_playlists(self) -> list:
        cursor = self.playlists.find({}, {"name": 1, "platform": 1, "_id": 0})
        return await cursor.to_list(length=None)
    
    async def add_song(self, playlist_name: str, song: dict):
        await self.playlists.update_one(
            {"name": playlist_name},
            {"$push": {"songs": song}}
        )
    
    async def remove_song(self, playlist_name: str, song_title: str):
        result = await self.playlists.update_one(
            {"name": playlist_name},
            {"$pull": {"songs": {"title": song_title}}}
        )
        return result.modified_count > 0

db = Database()
