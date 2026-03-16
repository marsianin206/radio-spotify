"""Discord бот для Spotify Radio."""
import os
from dotenv import load_dotenv
load_dotenv()

from typing import Optional
import os
from pathlib import Path

import discord
from discord import ButtonStyle
from discord.ext import commands
from discord import ui
import asyncio
from spotify.client import SpotifyClient
from audio.engine import AudioEngine


# Настройки бота - читаем из переменных окружения
TOKEN = os.environ.get("DISCORD_TOKEN") or os.getenv("DISCORD_TOKEN", "")
BOT_PREFIX = "!"

# Инициализация
spotify_client = None
audio = AudioEngine()

# Настройка intents
intents = discord.Intents.default()
intents.message_content = True  # Нужен для команд
intents.voice_states = True  # Нужен для голоса

bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)


# Класс кнопок для управления плеером
class PlayerView(ui.View):
    """Кнопки управления плеером."""
    def __init__(self, guild_id):
        super().__init__(timeout=None)  # Без таймаута для persistent view
        self.guild_id = guild_id
    
    @ui.button(emoji="⏮", style=ButtonStyle.primary, custom_id="prev")
    async def prev_button(self, interaction: discord.Interaction, button: ui.Button):
        """Предыдущий трек."""
        guild_id = interaction.guild.id if interaction.guild else None
        if guild_id and guild_id in radio_servers:
            state = radio_servers[guild_id]
            if state.playlist and state.current_index > 0:
                state.current_index -= 1
                if state.voice_client:
                    state.voice_client.stop()
                await interaction.response.send_message("⏮ Предыдущий трек", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Бот не в голосовом канале", ephemeral=True)
    
    @ui.button(emoji="⏸", style=ButtonStyle.primary, custom_id="pause")
    async def pause_button(self, interaction: discord.Interaction, button: ui.Button):
        """Пауза/Продолжить."""
        guild_id = interaction.guild.id if interaction.guild else None
        if guild_id and guild_id in radio_servers:
            state = radio_servers[guild_id]
            if state.voice_client and state.voice_client.is_playing():
                state.voice_client.pause()
                state.is_paused = True
                await interaction.response.send_message("⏸ Пауза", ephemeral=True)
            elif state.voice_client and state.is_paused:
                state.voice_client.resume()
                state.is_paused = False
                await interaction.response.send_message("▶ Продолжаю", ephemeral=True)
    
    @ui.button(emoji="⏭", style=ButtonStyle.primary, custom_id="next")
    async def next_button(self, interaction: discord.Interaction, button: ui.Button):
        """Следующий трек."""
        guild_id = interaction.guild.id if interaction.guild else None
        if guild_id and guild_id in radio_servers:
            state = radio_servers[guild_id]
            if state.voice_client:
                state.voice_client.stop()
                await interaction.response.send_message("⏭ Следующий трек", ephemeral=True)
    
    @ui.button(emoji="🔀", style=ButtonStyle.secondary, custom_id="shuffle")
    async def shuffle_button(self, interaction: discord.Interaction, button: ui.Button):
        """Перемешать плейлист."""
        guild_id = interaction.guild.id if interaction.guild else None
        if guild_id and guild_id in radio_servers:
            state = radio_servers[guild_id]
            if state.playlist:
                import random
                random.shuffle(state.playlist)
                state.current_index = 0
                await interaction.response.send_message("🔀 Плейлист перемешан!", ephemeral=True)
    
    @ui.button(emoji="🔊", style=ButtonStyle.secondary, custom_id="vol_up")
    async def vol_up_button(self, interaction: discord.Interaction, button: ui.Button):
        """Увеличить громкость."""
        guild_id = interaction.guild.id if interaction.guild else None
        if guild_id and guild_id in radio_servers:
            state = radio_servers[guild_id]
            if hasattr(state, 'volume'):
                state.volume = min(1.0, state.volume + 0.1)
                if state.voice_client and hasattr(state.voice_client.source, 'volume'):
                    state.voice_client.source.volume = state.volume
            await interaction.response.send_message(f"🔊 Громкость: {int(state.volume * 100)}%", ephemeral=True)
    
    @ui.button(emoji="🔉", style=ButtonStyle.secondary, custom_id="vol_down")
    async def vol_down_button(self, interaction: discord.Interaction, button: ui.Button):
        """Уменьшить громкость."""
        guild_id = interaction.guild.id if interaction.guild else None
        if guild_id and guild_id in radio_servers:
            state = radio_servers[guild_id]
            if hasattr(state, 'volume'):
                state.volume = max(0.0, state.volume - 0.1)
                if state.voice_client and hasattr(state.voice_client.source, 'volume'):
                    state.voice_client.source.volume = state.volume
            await interaction.response.send_message(f"🔉 Громкость: {int(state.volume * 100)}%", ephemeral=True)


# Состояние радио для каждого сервера
radio_servers = {}


class RadioState:
    """Состояние радио для сервера."""
    def __init__(self):
        self.voice_client = None
        self.current_track = None
        self.playlist = []
        self.current_index = 0
        self.is_playing = False
        self.is_paused = False
        self.volume = 0.5


def get_spotify():
    """Ленивая инициализация Spotify клиента."""
    global spotify_client
    if spotify_client is None:
        spotify_client = SpotifyClient()
    return spotify_client


@bot.event
async def on_ready():
    """Событие при запуске бота."""
    print(f"✅ Бот {bot.user} запущен!")
    await bot.change_presence(
        activity=discord.Streaming(
            name="Spotify Radio",
            url="https://twitch.tv/discord"
        )
    )
    print(f"🌐 Бот доступен на {len(bot.guilds)} серверах")


@bot.command(name="ping", help="Проверить работоспособность бота")
async def ping(ctx):
    """Проверка пинга."""
    await ctx.send(f"🏓 Пинг: {round(bot.latency * 1000)}мс")


@bot.command(name="join", help="Подключиться к голосовому каналу")
async def join(ctx):
    """Подключение к голосовому каналу."""
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        vc = await channel.connect()
        
        # Сохраняем состояние
        guild_id = ctx.guild.id
        if guild_id not in radio_servers:
            radio_servers[guild_id] = RadioState()
        radio_servers[guild_id].voice_client = vc
        
        await ctx.send(f"✅ Подключился к {channel.name}. Используйте !controls для управления!")
    else:
        await ctx.send("❌ Вы не в голосовом канале")


@bot.command(name="leave", help="Отключиться от голосового канала")
async def leave(ctx):
    """Отключение от голосового канала."""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Отключился от голосового канала")
    else:
        await ctx.send("❌ Я не в голосовом канале")


@bot.command(name="play", help="Поиск и воспроизведение трека")
async def play(ctx, *, query: str):
    """Поиск трека и начало воспроизведения."""
    await ctx.send(f"🔍 Ищу: `{query}`")
    
    try:
        spotify = get_spotify()
        tracks = spotify.search_track(query, limit=5)
        
        if not tracks:
            await ctx.send("❌ Треки не найдены")
            return
        
        # Отправляем результаты
        embed = discord.Embed(
            title="🎵 Найденные треки:",
            description="Выберите номер трека (1-5) или команду !radio для создания радио",
            color=discord.Color.green()
        )
        for i, track in enumerate(tracks, 1):
            duration = audio.format_duration(track['duration_ms'])
            embed.add_field(
                name=f"{i}. {track['name']}",
                value=f"{track['artist']} ({duration})",
                inline=False
            )
        
        msg = await ctx.send(embed=embed)
        
        # Подключение к голосовому каналу
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            if ctx.voice_client:
                await ctx.voice_client.move_to(channel)
            else:
                vc = await channel.connect()
        else:
            await ctx.send("❌ Вы не в голосовом канале")
            return
        
        # Инициализация состояния радио
        guild_id = ctx.guild.id
        if guild_id not in radio_servers:
            radio_servers[guild_id] = RadioState()
        
        state = radio_servers[guild_id]
        state.voice_client = ctx.voice_client
        state.playlist = tracks
        state.current_index = 0
        
        # Воспроизведение первого трека
        await play_track(ctx, tracks[0], state)
        
    except Exception as e:
        await ctx.send(f"❌ Ошибка: {str(e)}")


async def play_track(ctx, track, state):
    """Воспроизведение трека."""
    state.current_track = track
    state.is_playing = True
    state.is_paused = False
    
    # Опции FFmpeg для максимального качества звука
    ffmpeg_options = {
        'options': '-vn -af "loudnorm=I=-16:TP=-1.5:LRA=11" -b:a 320k'
    }
    
    # Пытаемся получить preview URL или ищем на YouTube
    if track.get('preview_url'):
        source = discord.FFmpegPCMAudio(track['preview_url'], **ffmpeg_options)
    else:
        await ctx.send("⚠️ Нет превью, ищу на YouTube...")
        audio_url = await audio.get_audio_url(track['name'], track['artist'])
        if audio_url:
            source = discord.FFmpegPCMAudio(audio_url, **ffmpeg_options)
        else:
            await ctx.send("❌ Не удалось найти аудио")
            return
    
    # Без трансформера - чистый звук без изменений
    def after_playing(error):
        if error:
            print(f"Ошибка воспроизведения: {error}")
        asyncio.run_coroutine_threadsafe(play_next(ctx, state), bot.loop)
    
    state.voice_client.play(source, after=after_playing)
    
    # Создание embed с информацией о треке
    embed = discord.Embed(
        title="▶ Сейчас играет:",
        description=f"**{track['name']}**\n{track['artist']}",
        color=discord.Color.green()
    )
    if track.get('image'):
        embed.set_thumbnail(url=track['image'])
    
    await ctx.send(embed=embed)


async def play_next(ctx, state):
    """Воспроизведение следующего трека."""
    if not state.playlist:
        return
    
    state.current_index = (state.current_index + 1) % len(state.playlist)
    next_track = state.playlist[state.current_index]
    await play_track(ctx, next_track, state)


@bot.command(name="radio", help="Создать радио на основе трека")
async def radio(ctx, *, query: str):
    """Создание радио-плейлиста."""
    await ctx.send(f"📻 Создаю радио на основе: `{query}`")
    
    try:
        spotify = get_spotify()
        tracks = spotify.search_track(query, limit=1)
        
        if not tracks:
            await ctx.send("❌ Трек не найден")
            return
        
        # Создание радио
        playlist = spotify.create_radio_playlist(tracks[0]['id'], limit=50)
        
        # Подключение к голосовому
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            if ctx.voice_client:
                await ctx.voice_client.move_to(channel)
            else:
                vc = await channel.connect()
        else:
            await ctx.send("❌ Вы не в голосовом канале")
            return
        
        guild_id = ctx.guild.id
        if guild_id not in radio_servers:
            radio_servers[guild_id] = RadioState()
        
        state = radio_servers[guild_id]
        state.voice_client = ctx.voice_client
        state.playlist = playlist
        state.current_index = 0
        
        await ctx.send(f"✅ Создано радио из **{len(playlist)}** треков!")
        await play_track(ctx, playlist[0], state)
        
    except Exception as e:
        await ctx.send(f"❌ Ошибка: {str(e)}")


@bot.command(name="local", help="Воспроизвести локальный файл")
async def local_play(ctx, *, filepath: Optional[str] = None):
    """Воспроизведение локального аудио файла."""
    import os
    from pathlib import Path
    
    # Папка с музыкой
    music_folder = Path(__file__).parent.parent / 'music'
    
    if not ctx.author.voice:
        await ctx.send("❌ Сначала зайдите в голосовой канал!")
        return
    
    # Если файл не указан - показываем список файлов
    if not filepath:
        # Сканируем папку music
        audio_extensions = {'.mp3', '.wav', '.ogg', '.flac', '.m4a'}
        files = []
        if music_folder.exists():
            for f in music_folder.iterdir():
                if f.is_file() and f.suffix.lower() in audio_extensions:
                    files.append(f.name)
        
        if not files:
            await ctx.send("📁 Папка music пуста! Положите туда mp3/wav/ogg файлы.")
            return
        
        # Показываем список файлов
        embed = discord.Embed(
            title="🎵 Доступные файлы в папке music:",
            color=discord.Color.blue()
        )
        files_list = "\n".join([f"{i+1}. {f}" for i, f in enumerate(files[:10])])
        embed.add_field(name="Файлы:", value=files_list or "Нет файлов")
        embed.add_field(name="Как.play", value="`!local <имя_файла>`\nНапример: `!local song.mp3`", inline=False)
        await ctx.send(embed=embed)
        return
    
    guild_id = ctx.guild.id
    
    # Подключение к голосовому каналу
    if ctx.voice_client:
        await ctx.voice_client.move_to(ctx.author.voice.channel)
    else:
        vc = await ctx.author.voice.channel.connect()
    
    if guild_id not in radio_servers:
        radio_servers[guild_id] = RadioState()
    
    state = radio_servers[guild_id]
    state.voice_client = ctx.voice_client
    
    await ctx.send(f"📁 Воспроизвожу: {filepath}...")
    
    try:
        # Проверка существования файла
        file_path = Path(filepath)
        if not file_path.exists():
            # Ищем в папке music
            music_file = music_folder / filepath
            if music_file.exists():
                filepath = str(music_file)
            else:
                await ctx.send(f"❌ Файл не найден: {filepath}\n\nСписок файлов: `!local`")
                return
        else:
            filepath = str(file_path)
        
        # Создание источника аудио с максимальным качеством
        ffmpeg_options = {
            'options': '-vn -af "loudnorm=I=-16:TP=-1.5:LRA=11" -b:a 320k'
        }
        source = discord.FFmpegPCMAudio(filepath, **ffmpeg_options)
        
        state.is_playing = True
        state.is_paused = False
        state.current_track = {'name': os.path.basename(filepath), 'artist': 'Локальный файл'}
        
        def after_playing(error):
            if error:
                print(f"Ошибка воспроизведения: {error}")
        
        state.voice_client.play(source, after=after_playing)
        
        embed = discord.Embed(
            title="▶ Локальное воспроизведение:",
            description=f"**{os.path.basename(filepath)}**",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Ошибка: {str(e)}")


@bot.command(name="skip", help="Пропустить текущий трек")
async def skip(ctx):
    """Пропуск трека."""
    guild_id = ctx.guild.id
    if guild_id in radio_servers and radio_servers[guild_id].voice_client:
        radio_servers[guild_id].voice_client.stop()
        await ctx.send("⏭ Трек пропущен")
    else:
        await ctx.send("❌ Ничего не воспроизводится")


@bot.command(name="pause", help="Пауза")
async def pause(ctx):
    """Пауза."""
    guild_id = ctx.guild.id
    if guild_id in radio_servers and radio_servers[guild_id].voice_client:
        if radio_servers[guild_id].voice_client.is_playing():
            radio_servers[guild_id].voice_client.pause()
            radio_servers[guild_id].is_paused = True
            await ctx.send("⏸ Пауза")
        else:
            await ctx.send("❌ Ничего не воспроизводится")
    else:
        await ctx.send("❌ Ничего не воспроизводится")


@bot.command(name="resume", help="Продолжить")
async def resume(ctx):
    """Продолжить."""
    guild_id = ctx.guild.id
    if guild_id in radio_servers and radio_servers[guild_id].voice_client:
        if radio_servers[guild_id].is_paused:
            radio_servers[guild_id].voice_client.resume()
            radio_servers[guild_id].is_paused = False
            await ctx.send("▶ Продолжаю воспроизведение")
        else:
            await ctx.send("❌ Нет на паузе")
    else:
        await ctx.send("❌ Ничего не воспроизводится")


@bot.command(name="stop", help="Остановить воспроизведение")
async def stop(ctx):
    """Остановка воспроизведения."""
    guild_id = ctx.guild.id
    if guild_id in radio_servers:
        if radio_servers[guild_id].voice_client:
            await radio_servers[guild_id].voice_client.disconnect()
        del radio_servers[guild_id]
        await ctx.send("⏹ Воспроизведение остановлено")
    else:
        await ctx.send("❌ Ничего не воспроизводится")


@bot.command(name="queue", help="Показать очередь")
async def queue(ctx):
    """Показать плейлист."""
    guild_id = ctx.guild.id
    if guild_id in radio_servers and radio_servers[guild_id].playlist:
        state = radio_servers[guild_id]
        embed = discord.Embed(
            title="📋 Плейлист",
            description=f"Треков: {len(state.playlist)} | Текущий: {state.current_index + 1}",
            color=discord.Color.blue()
        )
        
        for i, track in enumerate(state.playlist[:10], 1):
            marker = "▶" if i - 1 == state.current_index else f"{i}."
            duration = audio.format_duration(track['duration_ms'])
            embed.add_field(
                name=f"{marker} {track['name']}",
                value=f"{track['artist']} ({duration})",
                inline=False
            )
        
        await ctx.send(embed=embed)
    else:
        await ctx.send("📭 Плейлист пуст")


@bot.command(name="now", help="Показать текущий трек")
async def now(ctx):
    """Показать текущий трек."""
    guild_id = ctx.guild.id
    if guild_id in radio_servers and radio_servers[guild_id].current_track:
        track = radio_servers[guild_id].current_track
        embed = discord.Embed(
            title="🎵 Сейчас играет:",
            description=f"**{track['name']}**\n{track['artist']}",
            color=discord.Color.green()
        )
        if track.get('image'):
            embed.set_thumbnail(url=track['image'])
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ Ничего не воспроизводится")


@bot.command(name="volume", help="Установить громкость (0-100)")
async def volume(ctx, vol: int):
    """Установить громкость."""
    if 0 <= vol <= 100:
        guild_id = ctx.guild.id
        if guild_id in radio_servers and radio_servers[guild_id].voice_client:
            # Сохраняем громкость в состоянии
            if not hasattr(radio_servers[guild_id], 'volume'):
                radio_servers[guild_id].volume = 0.5
            radio_servers[guild_id].volume = vol / 100
            await ctx.send(f"🔊 Громкость: {vol}%")
        else:
            await ctx.send("❌ Ничего не воспроизводится")
    else:
        await ctx.send("❌ Громкость должна быть от 0 до 100")


@bot.command(name="help_radio", help="Показать помощь")
async def help_radio(ctx):
    """Помощь по командам."""
    embed = discord.Embed(
        title="🎧 Spotify Radio - Команды",
        color=discord.Color.green()
    )
    embed.add_field(name="🎵 !play <песня>", value="Найти и играть", inline=False)
    embed.add_field(name="📻 !radio <песня/жанр>", value="Создать радио", inline=False)
    embed.add_field(name="📁 !local <файл>", value="Локальный файл", inline=False)
    embed.add_field(name="⏸ !pause / !resume", value="Пауза/Продолжить", inline=False)
    embed.add_field(name="⏭ !skip / !stop", value="Следующий/Остановить", inline=False)
    embed.add_field(name="🎛 !controls", value="Кнопки управления", inline=False)
    embed.add_field(name="📋 !queue", value="Плейлист", inline=False)
    embed.add_field(name="💿 !now", value="Что играет", inline=False)
    
    await ctx.send(embed=embed)


@bot.command(name="controls", help="Показать кнопки управления плеером")
async def controls(ctx):
    """Показать кнопки управления плеером."""
    guild_id = ctx.guild.id
    
    if guild_id not in radio_servers:
        await ctx.send("❌ Бот не в голосовом канале! Используйте `!join`")
        return
    
    view = PlayerView(guild_id)
    # Сохраняем view для обработки callback
    bot.add_view(view, message_id=None)
    
    embed = discord.Embed(
        title="🎛 Управление плеером",
        description="Нажмите кнопки для управления воспроизведением",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed, view=view)


# === ПРОСТЫЕ КОМАНДЫ (ALIASES) ===
# Автоматическое подключение при любой команде воспроизведения
@bot.command(name="стоп")
async def stop_ru(ctx):
    await stop(ctx)

@bot.command(name="пауза")
async def pause_ru(ctx):
    await pause(ctx)

@bot.command(name="продолжить")
async def resume_ru(ctx):
    await resume(ctx)

@bot.command(name="следующий")
async def next_ru(ctx):
    await skip(ctx)

@bot.command(name="плейлист")
async def queue_ru(ctx):
    await queue(ctx)

@bot.command(name="сейчас")
async def now_ru(ctx):
    await now(ctx)

@bot.command(name="очередь")
async def queue2_ru(ctx):
    await queue(ctx)


# === АВТОМАТИЧЕСКОЕ ПОДКЛЮЧЕНИЕ ===
@bot.event
async def on_message(message):
    """Автоматическое подключение к голосовому каналу."""
    # Игнорируем сообщения ботов
    if message.author.bot:
        return
    
    # Проверяем команды воспроизведения
    play_commands = ['play', 'radio', 'local', 'join']
    content = message.content.lower().strip()
    
    # Если это команда воспроизведения и пользователь в голосовом канале
    if any(content.startswith(f'!{cmd}') or content.startswith(f'/ {cmd}') for cmd in ['play', 'radio', 'local']):
        if message.author.voice and message.guild:
            guild_id = message.guild.id
            
            # Подключаем если ещё не подключены
            if guild_id not in radio_servers or not radio_servers[guild_id].voice_client:
                try:
                    vc = await message.author.voice.channel.connect()
                    if guild_id not in radio_servers:
                        radio_servers[guild_id] = RadioState()
                    radio_servers[guild_id].voice_client = vc
                    await message.channel.send(f"✅ Подключился к {message.author.voice.channel.name}")
                except Exception as e:
                    print(f"Ошибка подключения: {e}")
    
    await bot.process_commands(message)


# Запуск бота
if __name__ == "__main__":
    if TOKEN:
        print("🚀 Запуск Discord бота...")
        bot.run(TOKEN)
    else:
        print("⚠️ Введите токен бота в переменную DISCORD_TOKEN в файле .env")
        print("Для запуска: python bot/main.py")
