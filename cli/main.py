"""CLI интерфейс для Spotify Radio."""
import sys
import asyncio
from typing import Optional
from spotify.client import SpotifyClient
from audio.engine import AudioEngine


def get_input(prompt: str = "") -> Optional[str]:
    """Получить ввод с обработкой ошибок."""
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        return None


class SpotifyRadioCLI:
    """Консольный интерфейс для управления радио."""
    
    def __init__(self):
        """Инициализация CLI."""
        self.spotify = SpotifyClient()
        self.audio = AudioEngine()
        self.current_playlist = []
        self.current_index = 0
    
    async def search_and_play(self, query: str):
        """Поиск треков и воспроизведение."""
        print(f"🔍 Поиск: {query}")
        tracks = self.spotify.search_track(query, limit=10)
        
        if not tracks:
            print("❌ Треки не найдены")
            return
        
        print("\n📋 Найденные треки:")
        for i, track in enumerate(tracks, 1):
            duration = self.audio.format_duration(track['duration_ms'])
            print(f"  {i}. {track['name']} - {track['artist']} ({duration})")
        
        choice = get_input("\n🎵 Выберите трек (номер или 'r' для случайного): ")
        if choice is None:
            print("\n👋 До свидания!")
            return
        
        if choice.lower() == 'r':
            track = tracks[0]  # Берем первый для радио
            self.start_radio(track)
        elif choice.isdigit() and 1 <= int(choice) <= len(tracks):
            track = tracks[int(choice) - 1]
            self.play_track(track)
        else:
            print("❌ Неверный выбор")
    
    def play_track(self, track: dict):
        """Воспроизвести трек."""
        self.current_playlist = [track]
        self.current_index = 0
        
        print(f"\n▶ Воспроизведение: {track['name']} - {track['artist']}")
        
        if track.get('preview_url'):
            print(f"🎵 Preview URL: {track['preview_url']}")
        else:
            print("⚠️ Нет превью, используем YouTube...")
    
    def start_radio(self, seed_track: dict):
        """Начать радио на основе трека."""
        print(f"\n📻 Создание радио на основе: {seed_track['name']}")
        
        self.current_playlist = self.spotify.create_radio_playlist(
            seed_track['id'], 
            limit=50
        )
        self.current_index = 0
        
        print(f"✅ Создан плейлист из {len(self.current_playlist)} треков")
        self.show_playlist()
    
    def show_playlist(self):
        """Показать текущий плейлист."""
        if not self.current_playlist:
            print("📭 Плейлист пуст")
            return
        
        print(f"\n📋 Плейлист ({len(self.current_playlist)} треков):")
        for i, track in enumerate(self.current_playlist[:10], 1):
            marker = "▶" if i - 1 == self.current_index else " "
            duration = self.audio.format_duration(track['duration_ms'])
            print(f"  {marker} {i}. {track['name']} - {track['artist']} ({duration})")
        
        if len(self.current_playlist) > 10:
            print(f"  ... и еще {len(self.current_playlist) - 10} треков")
    
    async def run_interactive(self):
        """Запустить интерактивный режим."""
        print("=" * 50)
        print("🎧 Spotify Radio CLI")
        print("=" * 50)
        print("Команды:")
        print("  search <запрос>  - Поиск и воспроизведение")
        print("  playlist        - Показать плейлист")
        print("  next            - Следующий трек")
        print("  prev            - Предыдущий трек")
        print("  quit            - Выход")
        print("=" * 50)
        
        while True:
            try:
                cmd = get_input("\n🎵 > ")
                if cmd is None:
                    print("\n👋 До свидания!")
                    break
                
                if cmd.startswith('search '):
                    query = cmd[7:]
                    await self.search_and_play(query)
                elif cmd == 'playlist':
                    self.show_playlist()
                elif cmd == 'next':
                    self.next_track()
                elif cmd == 'prev':
                    self.prev_track()
                elif cmd in ('quit', 'exit'):
                    print("👋 До свидания!")
                    break
                else:
                    print("❌ Неизвестная команда")
            except KeyboardInterrupt:
                print("\n👋 До свидания!")
                break
            except Exception as e:
                print(f"❌ Ошибка: {e}")
    
    def next_track(self):
        """Перейти к следующему треку."""
        if not self.current_playlist:
            print("📭 Нет треков для воспроизведения")
            return
        
        self.current_index = (self.current_index + 1) % len(self.current_playlist)
        track = self.current_playlist[self.current_index]
        print(f"\n⏭ Следующий: {track['name']} - {track['artist']}")
    
    def prev_track(self):
        """Перейти к предыдущему треку."""
        if not self.current_playlist:
            print("📭 Нет треков для воспроизведения")
            return
        
        self.current_index = (self.current_index - 1) % len(self.current_playlist)
        track = self.current_playlist[self.current_index]
        print(f"\n⏮ Предыдущий: {track['name']} - {track['artist']}")


async def main():
    """Точка входа."""
    cli = SpotifyRadioCLI()
    await cli.run_interactive()


if __name__ == "__main__":
    asyncio.run(main())
