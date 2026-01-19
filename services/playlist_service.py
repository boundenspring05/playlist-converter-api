import ytmusicapi
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import os
from typing import List, Dict, Any, Optional
from models import Song
from database import db

load_dotenv()

class PlaylistService:
    def __init__(self):
        self.ytmusic = ytmusicapi.YTMusic()
        self.spotify = spotipy.Spotify(
            client_credentials_manager=SpotifyClientCredentials(
                client_id=os.getenv("SPOTIFY_CLIENT_ID"),
                client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
            )
        )
    
    async def extract_playlist(self, platform: str, playlist_id: str) -> Dict[str, Any]:
        if platform.lower() == "youtube":
            return await self._extract_ytmusic(playlist_id)
        elif platform.lower() == "spotify":
            return await self._extract_spotify(playlist_id)
        else:
            raise ValueError("Platform must be 'youtube' or 'spotify'")
    
    async def _extract_ytmusic(self, playlist_id: str) -> Dict[str, Any]:
        playlist = self.ytmusic.get_playlist(playlist_id, limit=100)
        songs = []
        
        for track in playlist['tracks']:
            if track.get('videoId'):
                song_data = {
                    "title": track.get('title', 'Unknown'),
                    "artist": track.get('artists', ['Unknown'])[0]['name'],
                    "url": f"https://music.youtube.com/watch?v={track['videoId']}"
                }
                songs.append(song_data)
        
        return {
            "name": playlist.get('title', f"youtube_{playlist_id}"),
            "platform": "youtube",
            "songs": songs
        }
    
    async def _extract_spotify(self, playlist_id: str) -> Dict[str, Any]:
        results = self.spotify.playlist_tracks(playlist_id)
        playlist_info = self.spotify.playlist(playlist_id)
        songs = []
        
        for item in results['items']:
            track = item['track']
            if track:
                song_data = {
                    "title": track['name'],
                    "artist": track['artists'][0]['name'],
                    "url": track['external_urls']['spotify']
                }
                songs.append(song_data)
        
        return {
            "name": playlist_info.get('name', f"spotify_{playlist_id}"),
            "platform": "spotify",
            "songs": songs
        }
    
    async def convert_playlist(self, playlist_name: str, target_platform: str) -> str:
        playlist_doc = db.get_playlist(playlist_name)
        if not playlist_doc:
            raise ValueError("Playlist not found")
        
        songs = playlist_doc['songs']
        
        if target_platform.lower() == "youtube":
            return await self._convert_to_ytmusic(songs)
        elif target_platform.lower() == "spotify":
            return await self._convert_to_spotify(songs)
        else:
            raise ValueError("Target platform must be 'youtube' or 'spotify'")
    
    async def _convert_to_ytmusic(self, songs: List[Dict]) -> str:
        """Convert to YouTube Music (simplified - requires user auth)"""
        # Note: Full implementation needs OAuth2 user auth
        # This is a placeholder - you'd need ytmusicapi with user auth
        search_results = []
        for song in songs[:10]:  # Limit for demo
            results = self.ytmusic.search(f"{song['title']} {song['artist']}", filter="songs", limit=1)
            if results:
                search_results.append(results[0])
        
        # In production: create_playlist() + add_playlist_items()
        return "https://music.youtube.com/playlist?list=CONVERTED_PLAYLIST_ID"
    
    async def _convert_to_spotify(self, songs: List[Dict]) -> str:
        """Convert to Spotify (simplified - requires user auth)"""
        # Note: Full implementation needs user OAuth
        track_uris = []
        for song in songs[:10]:  # Limit for demo
            results = self.spotify.search(
                q=f"track:{song['title']} artist:{song['artist']}", 
                type='track', 
                limit=1
            )
            if results['tracks']['items']:
                track_uris.append(results['tracks']['items'][0]['uri'])
        
        # In production: user_playlist_create() + playlist_add_items()
        return "https://open.spotify.com/playlist/CONVERTED_PLAYLIST_ID"

# Global service instance
playlist_service = PlaylistService()
