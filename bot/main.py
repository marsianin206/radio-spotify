"""Discord бот для Spotify Radio."""
import os
import discord
from discord.ext import commands
import asyncio
from spotify.client import SpotifyClient
from audio.engine import AudioEngine


# Настройки бота - читаем из переменных окружения
TOKEN = os.environ.get("DISCORD_TOKEN") or os.getenv("DISCORD_TOKEN", "")
BOT_PREFIX = "!"

# Инициализация
spotify = SpotifyClient()
audio = AudioEngine()

# Настройка intents
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)


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


@bot.event
async def on_ready():
    """Событие при запуске бота."""
    print(f"✅ Бот {bot.user} запущен!")
    await bot.change_presence(activity=discord.Game("Spotify Radio"))


@bot.command(name="play", help="Поиск и воспроизведение трека")
async def play(ctx, *, query: str):
    """Поиск трека и начало воспроизведения."""
    await ctx.send(f"🔍 Ищу: {query}")
    
    try:
        tracks = spotify.search_track(query, limit=5)
        
        if not tracks:
            await ctx.send("❌ Треки не найдены")
            return
        
        # Отправляем результаты
        embed = discord.Embed(title="🎵 Найденные треки:", color=discord.Color.green())
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
    
    # Пытаемся получить preview URL или ищем на YouTube
    if track.get('preview_url'):
        source = discord.FFmpegPCMAudio(track['preview_url'])
    else:
        await ctx.send("⚠️ Нет превью, ищу на YouTube...")
        audio_url = await audio.get_audio_url(track['name'], track['artist'])
        if audio_url:
            source = discord.FFmpegPCMAudio(audio_url)
        else:
            await ctx.send("❌ Не удалось найти аудио")
            return
    
    # Создание трансформатора для управления
    state.voice_client.play(
        discord.PCMVolumeTransformer(source),
        after=lambda e: asyncio.run_coroutine_threadsafe(
            play_next(ctx, state), bot.loop
        ) if e is None else print(f"Ошибка: {e}")
    )
    
    embed = discord.Embed(
        title="▶ Сейчас играет:",
        description=f"**{track['name']}** - {track['artist']}",
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
    await ctx.send(f"📻 Создаю радио на основе: {query}")
    
    try:
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
        
        await ctx.send(f"✅ Создано радио из {len(playlist)} треков!")
        await play_track(ctx, playlist[0], state)
        
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
            color=discord.Color.blue()
        )
        
        for i, track in enumerate(state.playlist[:10], 1):
            marker = "▶" if i - 1 == state.current_index else " "
            embed.add_field(
                name=f"{marker} {i}. {track['name']}",
                value=track['artist'],
                inline=False
            )
        
        await ctx.send(embed=embed)
    else:
        await ctx.send("📭 Плейлист пуст")


@bot.command(name="help_radio", help="Показать помощь")
async def help_radio(ctx):
    """Помощь по командам."""
    embed = discord.Embed(
        title="🎧 Spotify Radio - Команды",
        color=discord.Color.green()
    )
    embed.add_field(name="!play <запрос>", value="Поиск и воспроизведение", inline=False)
    embed.add_field(name="!radio <запрос>", value="Создать радио на основе трека", inline=False)
    embed.add_field(name="!skip", value="Пропустить трек", inline=False)
    embed.add_field(name="!stop", value="Остановить воспроизведение", inline=False)
    embed.add_field(name="!queue", value="Показать плейлист", inline=False)
    
    await ctx.send(embed=embed)


# Запуск бота
if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("⚠️ Введите токен бота в переменную TOKEN")
        print("Для запуска: python bot/main.py")
