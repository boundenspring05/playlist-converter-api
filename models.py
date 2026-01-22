from pydantic import BaseModel
from typing import List, Optional

class Song(BaseModel):
    title: str
    artist: str
    url: str

class Playlist(BaseModel):
    name: str
    platform: str
    songs: List[Song]
