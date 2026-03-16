"""Spotify API клиент для работы с Spotify."""
import os
from typing import Optional, List, Dict
import spotipy
from spotipy.oauth_manager import ClientCredentialsManager


class SpotifyClient:
    """Клиент для взаимодействия с Spotify API."""
    
    def __init__(self):
        """Инициализация клиента с аутентификацией."""
        # Пробуем получить из переменных окружения
        self.client_id = os.environ.get("CLIENT_ID") or os.getenv("CLIENT_ID")
        self.client_secret = os.environ.get("CLIENT_SECRET") or os.getenv("CLIENT_SECRET")
        
        if not self.client_id or not self.client_secret:
            raise ValueError("CLIENT_ID и CLIENT_SECRET должны быть установлены")
        
        self.manager = ClientCredentialsManager(
            client_id=self.client_id,
            client_secret=self.client_secret
        )
        self.sp = spotipy.Spotify(auth_manager=self.manager)
    
    def search_track(self, query: str, limit: int = 10) -> List[Dict]:
        """Поиск треков по запросу."""
        results = self.sp.search(q=query, limit=limit, type='track')
        tracks = []
        for item in results['tracks']['items']:
            tracks.append(self._format_track(item))
        return tracks
    
    def get_track(self, track_id: str) -> Dict:
        """Получить информацию о треке по ID."""
        track = self.sp.track(track_id)
        return self._format_track(track)
    
    def get_playlist(self, playlist_id: str) -> List[Dict]:
        """Получить все треки из плейлиста."""
        results = self.sp.playlist_items(playlist_id)
        tracks = []
        while results:
            for item in results['items']:
                if item['track']:
                    tracks.append(self._format_track(item['track']))
            if results['next']:
                results = self.sp.next(results)
            else:
                results = None
        return tracks
    
    def get_user_playlists(self, limit: int = 50) -> List[Dict]:
        """Получить плейлисты текущего пользователя."""
        results = self.sp.current_user_playlists(limit=limit)
        playlists = []
        for item in results['items']:
            playlists.append({
                'id': item['id'],
                'name': item['name'],
                'description': item.get('description', ''),
                'tracks_count': item['tracks']['total'],
                'image': item['images'][0]['url'] if item['images'] else None
            })
        return playlists
    
    def get_recommendations(self, seed_tracks: List[str], limit: int = 20) -> List[Dict]:
        """Получить рекомендации на основе треков."""
        results = self.sp.recommendations(seed_tracks=seed_tracks[:5], limit=limit)
        tracks = []
        for item in results['tracks']:
            tracks.append(self._format_track(item))
        return tracks
    
    def get_track_preview_url(self, track_id: str) -> Optional[str]:
        """Получить URL превью трека (30 секунд)."""
        track = self.sp.track(track_id)
        return track.get('preview_url')
    
    def _format_track(self, track: Dict) -> Dict:
        """Форматирование данных трека."""
        artists = [artist['name'] for artist in track['artists']]
        return {
            'id': track['id'],
            'name': track['name'],
            'artist': ', '.join(artists),
            'album': track['album']['name'],
            'duration_ms': track['duration_ms'],
            'preview_url': track.get('preview_url'),
            'external_urls': track['external_urls'],
            'image': track['album']['images'][0]['url'] if track['album']['images'] else None
        }
    
    def create_radio_playlist(self, seed_track_id: str, name: str = "Radio Mix", limit: int = 50) -> List[Dict]:
        """Создать радио-плейлист на основе трека (рекомендации)."""
        recommendations = self.get_recommendations([seed_track_id], limit)
        return recommendations
