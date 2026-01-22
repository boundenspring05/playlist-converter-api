from fastapi import FastAPI, HTTPException
from typing import List
import database
from services.playlist_service import get_playlist_service
from services.trie_service import create_trie_for_playlist
from models import Playlist, Song

db = database.db

app = FastAPI(
    title="Music Playlist Converter",
    description="Convert playlists between YouTube Music and Spotify with Trie prefix search"
)


@app.get("/")
async def root():
    return {"message": "Music Playlist Converter API", "docs": "/docs"}


# 5. Add song to playlist
@app.post("/playlists/{name}/songs")
async def add_song_to_playlist(name: str, song: Song):
    """Add a song to existing playlist"""
    doc = await database.db.get_playlist(name)
    if not doc:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    song_data = {
        "title": song.title,
        "artist": song.artist,
        "url": song.url
    }

    await database.db.add_song(name, song_data)
    return {
        "message": f"Song '{song.title}' added to {name}",
        #"total_songs": await database.db.get_playlist_song_count(name)
    }


# 1. Extract and store playlist from YouTube/Spotify
@app.post("/playlists/{platform}/{playlist_id}")
async def store_playlist(platform: str, playlist_id: str):
    """
    Extract playlist from YouTube/Spotify and store in MongoDB
    POST /playlists/youtube/PLuam0fP24nWjG0z9Or
    POST /playlists/spotify/37i9dQZF1DXcBWIGoYBM5M
    """
    try:
        service = get_playlist_service()
        playlist_data = await service.extract_playlist(platform, playlist_id)
        await database.db.store_playlist(playlist_data)
        return {
            "message": "Playlist stored successfully",
            "playlist": {
                "name": playlist_data["name"],
                "platform": playlist_data["platform"],
                "song_count": len(playlist_data["songs"])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to extract playlist: {str(e)}")

# 2. List all stored playlists
@app.get("/playlists")
async def list_playlists():
    """Get all stored playlists with platform info"""
    playlists = await database.db.get_all_playlists()
    return {
        "playlists": playlists,
        "total": len(playlists)
    }


@app.get("/playlists/{name}", response_model=List[Song])
async def get_playlist_songs(name: str):
    doc = await database.db.get_playlist(name)
    if not doc:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    return doc["songs"]

# 4. Prefix search songs using Trie
@app.get("/playlists/{name}/search")
async def search_playlist_songs(name: str, prefix: str):
    """
    Prefix search songs in playlist using Trie data structure
    GET /playlists/myplaylist/search?prefix=beat
    """
    doc = await database.db.get_playlist(name)
    if not doc:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    trie = create_trie_for_playlist(doc["songs"])
    matches = trie.search_prefix(prefix)
    
    return {
        "playlist": name,
        "prefix": prefix,
        "matches": [Song(**song) for song in matches],
        "total_matches": len(matches)
    }



# 6. Remove song from playlist
@app.delete("/playlists/{name}/songs/{title}")
async def remove_song_from_playlist(name: str, title: str):
    """Remove song by title from playlist"""
    doc = await database.db.get_playlist(name)
    if not doc:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    removed = await database.db.remove_song(name, title)
    if removed:
        return {"message": f"Song '{title}' removed from {name}"}
    raise HTTPException(status_code=404, detail="Song not found in playlist")

# 7. Convert playlist to target platform
@app.post("/playlists/{name}/convert/{target_platform}")
async def convert_playlist_to_platform(name: str, target_platform: str):
    """
    Convert stored playlist to YouTube/Spotify and return link
    POST /playlists/myplaylist/convert/spotify
    POST /playlists/myplaylist/convert/youtube
    """
    doc = await database.db.get_playlist(name)
    if not doc:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    try:
        service = get_playlist_service()
        converted_url = await service.convert_playlist(name, target_platform)
        return {
            "message": f"Converted to {target_platform}",
            "original_playlist": name,
            "target_platform": target_platform,
            "converted_playlist_url": converted_url
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Conversion failed: {str(e)}")
