import ytmusicapi
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from dotenv import load_dotenv
import os
from typing import List, Dict, Any
import database

load_dotenv()

# Global service instance
_service_instance = None

def get_playlist_service():
    global _service_instance
    if _service_instance is None:
        _service_instance = PlaylistService()
    return _service_instance

class PlaylistService:
    def __init__(self):
        self.ytmusic = ytmusicapi.YTMusic('browser.json')
        self.spotify_client = spotipy.Spotify(
            client_credentials_manager=SpotifyClientCredentials(
                client_id=os.getenv("SPOTIFY_CLIENT_ID"),
                client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
            )
        )
        
        self.spotify_user = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=os.getenv("SPOTIFY_CLIENT_ID"),
                client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
                redirect_uri="http://localhost:8888/callback",
                scope="playlist-modify-public playlist-modify-private user-library-read"
            )
        )
    
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
        results = self.spotify_client.playlist_tracks(playlist_id)
        playlist_info = self.spotify_client.playlist(playlist_id)
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
    
    async def convert_to_spotify(self, songs: List[Dict]) -> str:
        try:
            # 1. Get user's Spotify ID
            user_profile = self.spotify_user.current_user()
            user_id = user_profile['id']
            
            # 2. Create new playlist
            playlist_name = f"Converted Playlist - {len(songs)} songs"
            playlist = self.spotify_user.user_playlist_create(
                user_id, 
                name=playlist_name,
                public=True,
                description="Converted via Playlist Converter API"
            )
            playlist_id = playlist['id']
            
            # 3. Find Spotify URIs for each song
            track_uris = []
            for song in songs[:100]:  # Spotify limit
                query = f"track:{song['title']} artist:{song['artist']}"
                results = self.spotify_user.search(q=query, type='track', limit=1)
                
                if results['tracks']['items']:
                    track_uris.append(results['tracks']['items'][0]['uri'])
                    print(f"✓ Found: {song['title']} - {song['artist']}")
                else:
                    print(f"✗ Not found: {song['title']} - {song['artist']}")
            
            # 4. Add tracks to playlist (100 max per request)
            if track_uris:
                self.spotify_user.playlist_add_items(playlist_id, track_uris)
                print(f"Added {len(track_uris)} songs to Spotify")
            
            return f"https://open.spotify.com/playlist/{playlist_id}"
            
        except Exception as e:
            raise Exception(f"Spotify conversion failed: {str(e)}")
    
    async def convert_to_ytmusic(self, songs: List[Dict]) -> str:
        try:
            # 1. Create new playlist
            playlist_id = self.ytmusic.create_playlist(
                "Converted Playlist",
                "Converted via Playlist Converter API",
                privacy_status="PRIVATE"
            )
            #playlist_id = playlist_info['playlistId']
            
            # 2. Search and add songs
            video_ids = []
            for song in songs[:50]:  # YTMusic limit
                search_results = self.ytmusic.search(
                    f"{song['title']} {song['artist']}",
                    filter="songs",
                    limit=1
                )
                
                if search_results:
                    video_id = search_results[0].get('videoId')
                    if video_id:
                        video_ids.append(video_id)
                        print(f"✓ Found: {song['title']} - {song['artist']}")
            
            # 3. Add videos to playlist
            if video_ids:
                self.ytmusic.add_playlist_items(playlist_id, video_ids)
                print(f"Added {len(video_ids)} songs to YouTube Music")
            
            return f"https://music.youtube.com/playlist?list={playlist_id}"
            
        except Exception as e:
            raise Exception(f"YouTube Music conversion failed: {str(e)}")
    
    async def extract_playlist(self, platform: str, playlist_id: str) -> Dict[str, Any]:
        if platform.lower() == "youtube":
            return await self._extract_ytmusic(playlist_id)
        elif platform.lower() == "spotify":
            return await self._extract_spotify(playlist_id)
        else:
            raise ValueError("Platform must be 'youtube' or 'spotify'")
    
    async def convert_playlist(self, playlist_name: str, target_platform: str) -> str:
        # FIXED: Use async database call
        playlist_doc = await database.db.get_playlist(playlist_name)
        if not playlist_doc:
            raise ValueError("Playlist not found")
        
        songs = playlist_doc['songs']
        
        if target_platform.lower() == "youtube":
            return await self.convert_to_ytmusic(songs)
        elif target_platform.lower() == "spotify":
            return await self.convert_to_spotify(songs)
        else:
            raise ValueError("Target platform must be 'youtube' or 'spotify'")