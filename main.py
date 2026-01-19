from fastapi import FastAPI, HTTPException
from typing import List, Optional
from database import db
from services.playlist_service import playlist_service
from services.trie_service import create_trie_for_playlist
from models import Playlist, Song
#import uvicorn

# FastAPI App
app = FastAPI(
    title="Music Playlist Converter",
    description="Convert playlists between YouTube Music and Spotify with Trie prefix search"
)

@app.get("/")
async def root():
    return {"message": "Music Playlist Converter API", "docs": "/docs"}

# 1. Extract and store playlist from YouTube/Spotify
@app.post("/playlists/{platform}/{playlist_id}")
async def store_playlist(platform: str, playlist_id: str):
    """
    Extract playlist from YouTube/Spotify and store in MongoDB
    POST /playlists/youtube/PLuam0fP24nWjG0z9Or
    POST /playlists/spotify/37i9dQZF1DXcBWIGoYBM5M
    """
    try:
        playlist_data = await playlist_service.extract_playlist(platform, playlist_id)
        db.store_playlist(playlist_data)
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
    playlists = db.get_all_playlists()
    return {
        "playlists": playlists,
        "total": len(playlists)
    }

# 3. Display all songs in a playlist
@app.get("/playlists/{name}", response_model=List[Song])
async def get_playlist_songs(name: str):
    """Get all songs from a stored playlist"""
    doc = db.get_playlist(name)
    if not doc:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return [Song(**song) for song in doc["songs"]]

# 4. Prefix search songs using Trie
@app.get("/playlists/{name}/search")
async def search_playlist_songs(name: str, prefix: str):
    """
    Prefix search songs in playlist using Trie data structure
    GET /playlists/myplaylist/search?prefix=beat
    """
    doc = db.get_playlist(name)
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

# 5. Add song to playlist
@app.post("/playlists/{name}/songs")
async def add_song_to_playlist(name: str, song: Song):
    """Add a song to existing playlist"""
    doc = db.get_playlist(name)
    if not doc:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    db.add_song(name, song.dict())
    return {"message": f"Song '{song.title}' added to {name}"}

# 6. Remove song from playlist
@app.delete("/playlists/{name}/songs/{title}")
async def remove_song_from_playlist(name: str, title: str):
    """Remove song by title from playlist"""
    doc = db.get_playlist(name)
    if not doc:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    if db.remove_song(name, title):
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
    doc = db.get_playlist(name)
    if not doc:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    try:
        converted_url = await playlist_service.convert_playlist(name, target_platform)
        return {
            "message": f"Converted to {target_platform}",
            "original_playlist": name,
            "target_platform": target_platform,
            "converted_playlist_url": converted_url
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Conversion failed: {str(e)}")

#if __name__ == "__main__":
    #uvicorn.run(app, host="0.0.0.0", port=8000)
