"""Аудио-движок для потоковой передачи музыки."""
import os
import asyncio
import aiohttp
from typing import Optional, List, Dict
from pathlib import Path
import yt_dlp
import tempfile


class AudioEngine:
    """Движок для загрузки и воспроизведения аудио."""
    
    def __init__(self, cache_dir: str = None):
        """Инициализация аудио-движка."""
        self.cache_dir = Path(cache_dir or tempfile.gettempdir()) / "spotify_radio_cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        self.ytdl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'cache': True,
        }
        
        self.current_track: Optional[Dict] = None
        self.queue: List[Dict] = []
        self.is_playing = False
    
    async def get_audio_url(self, track_name: str, artist: str) -> Optional[str]:
        """Получить URL аудио для трека через YouTube."""
        query = f"{track_name} {artist} audio"
        
        loop = asyncio.get_event_loop()
        
        def _search():
            with yt_dlp.YoutubeDL(self.ytdl_opts) as ydl:
                info = ydl.extract_info(
                    f"ytsearch1:{query}",
                    download=False
                )
                if info and info.get('entries'):
                    return info['entries'][0]['url']
                return None
        
        try:
            url = await loop.run_in_executor(None, _search)
            return url
        except Exception as e:
            print(f"Error searching: {e}")
            return None
    
    async def download_track(self, track: Dict) -> Optional[str]:
        """Скачать трек в кэш."""
        cache_file = self.cache_dir / f"{track['id']}.mp3"
        
        if cache_file.exists():
            return str(cache_file)
        
        if not track.get('preview_url'):
            audio_url = await self.get_audio_url(track['name'], track['artist'])
            if not audio_url:
                return None
        else:
            audio_url = track['preview_url']
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(audio_url) as response:
                    if response.status == 200:
                        content = await response.read()
                        with open(cache_file, 'wb') as f:
                            f.write(content)
                        return str(cache_file)
        except Exception as e:
            print(f"Download error: {e}")
            return None
        
        return None
    
    def add_to_queue(self, track: Dict):
        """Добавить трек в очередь."""
        self.queue.append(track)
    
    def get_next_track(self) -> Optional[Dict]:
        """Получить следующий трек из очереди."""
        if self.queue:
            return self.queue.pop(0)
        return None
    
    def clear_queue(self):
        """Очистить очередь."""
        self.queue.clear()
    
    def format_duration(self, ms: int) -> str:
        """Форматировать длительность."""
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"
    
    async def create_radio_stream(self, tracks: List[Dict], shuffle: bool = True) -> List[Dict]:
        """Создать радио-поток из списка треков."""
        import random
        
        radio_tracks = tracks.copy()
        if shuffle:
            random.shuffle(radio_tracks)
        
        return radio_tracks
