from pymongo import MongoClient
from dotenv import load_dotenv
import os
load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client.playlist_db
playlists = db.playlists


from pydantic import BaseModel
class Song(BaseModel):
    title: str
    artist: str
    url: str
class Playlist(BaseModel):
    name: str
    platform: str
    songs: list[Song]
