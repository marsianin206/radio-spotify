"""Веб-интерфейс Spotify Radio для Vercel."""
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify, Response, send_from_directory

# HTML шаблон (встроенный для Vercel совместимости)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Spotify Radio</title>
    <script>
        window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };
    </script>
    <script defer src="/_vercel/insights/script.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #1DB954 0%, #191414 100%); min-height: 100vh; color: white; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        header { text-align: center; padding: 40px 0; }
        h1 { font-size: 3rem; margin-bottom: 10px; }
        .tabs { display: flex; gap: 10px; justify-content: center; margin-bottom: 20px; }
        .tab { padding: 15px 30px; background: rgba(255,255,255,0.1); border: none; border-radius: 30px; color: white; font-size: 16px; cursor: pointer; }
        .tab.active { background: #1DB954; }
        .search-box { display: flex; gap: 10px; max-width: 600px; margin: 0 auto 30px; }
        input { flex: 1; padding: 15px 20px; border: none; border-radius: 30px; font-size: 16px; outline: none; }
        button { padding: 15px 30px; border: none; border-radius: 30px; background: #1DB954; color: white; font-size: 16px; cursor: pointer; }
        button:hover { transform: scale(1.05); }
        button:disabled { background: #535353; cursor: not-allowed; }
        .player { background: rgba(0,0,0,0.5); border-radius: 20px; padding: 30px; margin-top: 30px; text-align: center; }
        .track-name { font-size: 1.5rem; margin-bottom: 5px; }
        .artist-name { color: #b3b3b3; }
        .controls { display: flex; justify-content: center; gap: 20px; margin-top: 20px; }
        .controls button { background: #535353; padding: 10px 20px; }
        .playlist { margin-top: 30px; background: rgba(0,0,0,0.3); border-radius: 15px; padding: 20px; }
        .track-item { display: flex; align-items: center; padding: 10px; border-radius: 10px; cursor: pointer; }
        .track-item:hover { background: rgba(255,255,255,0.1); }
        .track-item img { width: 50px; height: 50px; border-radius: 5px; margin-right: 15px; }
        .track-info { flex: 1; text-align: left; }
        .results { margin-top: 30px; }
        .error { background: rgba(255,0,0,0.3); padding: 15px; border-radius: 10px; margin: 10px 0; }
        .local-files { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; padding: 20px; }
        .local-file { background: rgba(0,0,0,0.3); padding: 20px; border-radius: 10px; cursor: pointer; text-align: center; }
        .local-file:hover { background: rgba(29,185,84,0.3); }
        .hidden { display: none !important; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎧 Spotify Radio</h1>
            <p>Поиск и потоковая трансляция музыки</p>
        </header>
        <div class="tabs">
            <button class="tab active" onclick="switchTab('spotify')">🔍 Spotify</button>
            <button class="tab" onclick="switchTab('local')">📁 Локальные</button>
            <button class="tab" onclick="switchTab('dj')">🎛️ DJ Станция</button>
            <button class="tab" onclick="switchTab('history')">📜 История</button>
        </div>
        
        <!-- Spotify Tab -->
        <div id="spotify-tab">
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="Поиск трека...">
                <button onclick="search()">Поиск</button>
            </div>
            <div id="error-msg" class="error hidden"></div>
            <div class="results" id="results" style="display:none;">
                <h2>Результаты поиска</h2>
                <div id="resultsList"></div>
            </div>
        </div>
        
        <!-- Local Tab -->
        <div id="local-tab" class="hidden">
            <h2 style="text-align: center; margin-bottom: 20px;">Локальные файлы</h2>
            <div class="local-files" id="localFiles"></div>
        </div>
        
        <!-- DJ Station Tab -->
        <div id="dj-tab" class="hidden">
            <h2 style="text-align: center; margin-bottom: 20px;">🎛️ DJ Станция</h2>
            <div class="dj-controls" style="display: flex; justify-content: center; gap: 10px; margin-bottom: 20px; flex-wrap: wrap;">
                <button onclick="shufflePlaylist()" style="background: #9b59b6;">🔀 Перемешать</button>
                <button onclick="clearPlaylist()" style="background: #e74c3c;">🗑️ Очистить</button>
                <button onclick="refreshQueue()" style="background: #3498db;">🔄 Обновить</button>
            </div>
            <div class="queue-info" id="queueInfo" style="text-align: center; margin-bottom: 10px; color: #b3b3b3;"></div>
            <div class="playlist" id="djPlaylist"></div>
        </div>
        
        <!-- History Tab -->
        <div id="history-tab" class="hidden">
            <h2 style="text-align: center; margin-bottom: 20px;">📜 История</h2>
            <div class="playlist" id="historyList"></div>
        </div>
        
        <div class="player" id="player" style="display:none;">
            <div class="track-name" id="trackName"></div>
            <div class="artist-name" id="artistName"></div>
            <div class="controls">
                <button onclick="prevTrack()">⏮</button>
                <button onclick="togglePlay()" id="playBtn">▶</button>
                <button onclick="nextTrack()">⏭</button>
                <button onclick="startRadio()">📻 Радио</button>
            </div>
            <div class="volume-controls" style="display: flex; justify-content: center; gap: 10px; margin-top: 15px;">
                <button onclick="volumeDown()" style="background: #f39c12; padding: 8px 15px;">🔉</button>
                <span id="volumeDisplay" style="align-self: center; color: #b3b3b3;">50%</span>
                <button onclick="volumeUp()" style="background: #f39c12; padding: 8px 15px;">🔊</button>
            </div>
            <div class="playlist" id="playlistSection" style="display:none;">
                <h2>Плейлист</h2>
                <div id="playlist"></div>
            </div>
        </div>
    </div>
    <script>
        let currentState = { isPlaying: false, currentTrack: null, playlist: [] };
        
        function switchTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById('spotify-tab').classList.toggle('hidden', tab !== 'spotify');
            document.getElementById('local-tab').classList.toggle('hidden', tab !== 'local');
            document.getElementById('dj-tab').classList.toggle('hidden', tab !== 'dj');
            document.getElementById('history-tab').classList.toggle('hidden', tab !== 'history');
            if (tab === 'local') loadLocalFiles();
            if (tab === 'dj') refreshQueue();
            if (tab === 'history') loadHistory();
        }
        
        async function refreshQueue() {
            const response = await fetch('/api/playlist');
            const data = await response.json();
            const container = document.getElementById('djPlaylist');
            const info = document.getElementById('queueInfo');
            if (data.playlist && data.playlist.length > 0) {
                info.textContent = `В очереди: ${data.playlist.length} треков`;
                container.innerHTML = data.playlist.map((t, i) => 
                    `<div class="track-item">
                        <span style="margin-right: 10px; color: #1DB954;">${i + 1}</span>
                        <div class="track-info">
                            <div>${t.name}</div>
                            <small style="color: #b3b3b3;">${t.artist || ''}</small>
                        </div>
                        <button onclick="removeFromQueue(${i})" style="background: #e74c3c; padding: 5px 10px; font-size: 12px;">✕</button>
                    </div>`
                ).join('');
            } else {
                info.textContent = 'Плейлист пуст';
                container.innerHTML = '<p style="text-align: center; color: #b3b3b3;">Нет треков в плейлисте</p>';
            }
        }
        
        async function shufflePlaylist() {
            await fetch('/api/queue/shuffle', { method: 'POST' });
            refreshQueue();
        }
        
        async function clearPlaylist() {
            await fetch('/api/queue/clear', { method: 'POST' });
            refreshQueue();
        }
        
        async function removeFromQueue(index) {
            await fetch('/api/queue/remove', { 
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({index: index})
            });
            refreshQueue();
        }
        
        async function loadHistory() {
            const response = await fetch('/api/history');
            const data = await response.json();
            const container = document.getElementById('historyList');
            if (data.history && data.history.length > 0) {
                container.innerHTML = data.history.map(t => 
                    `<div class="track-item">
                        <div class="track-info">
                            <div>${t.name}</div>
                            <small style="color: #b3b3b3;">${t.artist || ''}</small>
                        </div>
                    </div>`
                ).join('');
            } else {
                container.innerHTML = '<p style="text-align: center; color: #b3b3b3;">История пуста</p>';
            }
        }
        
        async function refreshHistory() {
            loadHistory();
        }
        
        async function volumeUp() {
            await fetch('/api/volume/up', { method: 'POST' });
            updateVolumeDisplay();
        }
        
        async function volumeDown() {
            await fetch('/api/volume/down', { method: 'POST' });
            updateVolumeDisplay();
        }
        
        async function updateVolumeDisplay() {
            const response = await fetch('/api/state');
            const data = await response.json();
            const volumeEl = document.getElementById('volumeDisplay');
            if (volumeEl && data.volume !== undefined) {
                volumeEl.textContent = data.volume + '%';
            }
        }
        
        async function loadLocalFiles() {
            const response = await fetch('/api/local/files');
            const data = await response.json();
            const container = document.getElementById('localFiles');
            if (data.files && data.files.length > 0) {
                container.innerHTML = data.files.map(f => 
                    `<div class="local-file" onclick="playLocal('${f}')">🎵 ${f}</div>`
                ).join('');
            } else {
                container.innerHTML = '<p>Файлы не найдены. Положите mp3/wav файлы в папку music/</p>';
            }
        }
        
        async function playLocal(filename) {
            const response = await fetch('/api/local/play', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({filename})
            });
            const data = await response.json();
            if (data.success) {
                showPlayer(data.track);
            }
        }
        
        async function search() {
            const query = document.getElementById('searchInput').value;
            if (!query) return;
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            if (data.error) {
                showError(data.error);
            } else if (data.tracks) {
                hideError();
                showResults(data.tracks);
            }
        }
        
        function showError(msg) {
            const errDiv = document.getElementById('error-msg');
            errDiv.textContent = 'Ошибка: ' + msg;
            errDiv.classList.remove('hidden');
        }
        
        function hideError() {
            document.getElementById('error-msg').classList.add('hidden');
        }
        
        function showResults(tracks) {
            const resultsDiv = document.getElementById('results');
            const resultsList = document.getElementById('resultsList');
            resultsList.innerHTML = tracks.map((track) => 
                `<div class="track-item">
                    <img src="${track.image || ''}" alt="${track.name}">
                    <div class="track-info">
                        <div>${track.name}</div>
                        <div class="artist-name">${track.artist}</div>
                    </div>
                    <div style="display: flex; gap: 5px;">
                        <button onclick="selectTrack('${track.id}')" style="background: #1DB954; padding: 5px 10px; font-size: 12px;">▶</button>
                        <button onclick="addToQueueFromSearch('${track.id}')" style="background: #f39c12; padding: 5px 10px; font-size: 12px;">+</button>
                    </div>
                </div>`
            ).join('');
            resultsDiv.style.display = 'block';
        }
        
        async function addToQueueFromSearch(trackId) {
            const response = await fetch('/api/queue/add-from-search', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({track_id: trackId})
            });
            const data = await response.json();
            if (data.success) {
                alert('Добавлено в очередь!');
            } else {
                alert('Ошибка: ' + (data.error || 'Неизвестная ошибка'));
            }
        }
        async function selectTrack(trackId) {
            // Сначала пробуем получить данные трека напрямую
            const response = await fetch('/api/play', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({track_id: trackId}) });
            const data = await response.json();
            if (data.track) {
                showPlayer(data.track);
                currentState.currentTrack = data.track;
            } else if (data.error) {
                alert(data.error);
            }
        }
        async function playTrackFromSearch(track) {
            // Отправляем трек напрямую
            const response = await fetch('/api/play', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({track: track}) });
            const data = await response.json();
            if (data.track) {
                showPlayer(data.track);
                currentState.currentTrack = track;
            } else if (data.error) {
                alert(data.error);
            }
        }
        async function startRadio() {
            if (!currentState.currentTrack) return;
            const response = await fetch('/api/radio', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({track_id: currentState.currentTrack.id}) });
            const data = await response.json();
            if (data.playlist) { currentState.playlist = data.playlist; showPlaylist(data.playlist); }
        }
        function showPlayer(track) {
            currentState.currentTrack = track;
            document.getElementById('trackName').textContent = track.name;
            document.getElementById('artistName').textContent = track.artist;
            document.getElementById('player').style.display = 'block';
        }
        function showPlaylist(playlist) {
            document.getElementById('playlistSection').style.display = 'block';
            document.getElementById('playlist').innerHTML = playlist.map((t, i) => 
                `<div class="track-item" onclick="playTrack(${i})">
                    <img src="${t.image || ''}" alt="${t.name}">
                    <div class="track-info"><div>${t.name}</div><div class="artist-name">${t.artist}</div></div>
                </div>`
            ).join('');
        }
        async function togglePlay() {
            const endpoint = currentState.isPlaying ? '/api/pause' : '/api/resume';
            await fetch(endpoint, {method: 'POST'});
            currentState.isPlaying = !currentState.isPlaying;
            document.getElementById('playBtn').textContent = currentState.isPlaying ? '⏸' : '▶';
        }
        async function nextTrack() {
            const response = await fetch('/api/next', {method: 'POST'});
            const data = await response.json();
            if (data.track) showPlayer(data.track);
        }
        async function prevTrack() {
            const response = await fetch('/api/prev', {method: 'POST'});
            const data = await response.json();
            if (data.track) showPlayer(data.track);
        }
        document.getElementById('searchInput').addEventListener('keypress', (e) => { if (e.key === 'Enter') search(); });
    </script>
</body>
</html>
'''

# Vercel совместимость - создаем Flask приложение
app = Flask(__name__)

# Глобальное состояние (для serverless - будет сбрасываться)
radio_state = {
    'is_playing': False,
    'current_track': None,
    'playlist': [],
    'current_index': 0
}

# Кэш клиента для ленивой загрузки
_spotify_client = None


def get_spotify_client():
    """Ленивая загрузка Spotify клиента."""
    global _spotify_client
    if _spotify_client is None:
        from spotify.client import SpotifyClient
        _spotify_client = SpotifyClient()
    return _spotify_client


def get_audio_engine():
    """Ленивая загрузка Audio Engine."""
    from audio.engine import AudioEngine
    return AudioEngine()


@app.route('/')
def index():
    """Главная страница."""
    return HTML_TEMPLATE


@app.route('/api/search')
def search():
    """API для поиска треков."""
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    try:
        spotify = get_spotify_client()
        tracks = spotify.search_track(query, limit=10)
        return jsonify({'tracks': tracks})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/play', methods=['POST'])
def play():
    """API для воспроизведения трека."""
    data = request.json
    track_id = data.get('track_id')
    track_data = data.get('track')  # Можно передать трек напрямую
    
    if track_data:
        # Используем данные трека из поиска
        radio_state['current_track'] = track_data
        radio_state['is_playing'] = True
        return jsonify({'success': True, 'track': track_data})
    
    if not track_id:
        return jsonify({'error': 'track_id or track is required'}), 400
    
    try:
        spotify = get_spotify_client()
        track = spotify.get_track(track_id)
        radio_state['current_track'] = track
        radio_state['is_playing'] = True
        return jsonify({'success': True, 'track': track})
    except Exception as e:
        error_msg = str(e)
        if '403' in error_msg or 'premium' in error_msg.lower():
            return jsonify({'error': 'Требуется Spotify Premium для воспроизведения треков. Используйте локальные файлы.'}), 400
        return jsonify({'error': str(e)}), 500


@app.route('/api/radio', methods=['POST'])
def start_radio():
    """API для запуска радио."""
    data = request.json
    seed_track_id = data.get('track_id')
    
    if not seed_track_id:
        return jsonify({'error': 'track_id is required'}), 400
    
    try:
        spotify = get_spotify_client()
        playlist = spotify.create_radio_playlist(seed_track_id, limit=50)
        radio_state['playlist'] = playlist
        radio_state['current_index'] = 0
        radio_state['is_playing'] = True
        radio_state['current_track'] = playlist[0] if playlist else None
        
        return jsonify({
            'success': True, 
            'playlist': playlist,
            'current_track': radio_state['current_track']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/playlist', methods=['GET'])
def get_playlist():
    """API для получения текущего плейлиста."""
    return jsonify(radio_state)


@app.route('/api/next', methods=['POST'])
def next_track():
    """API для следующего трека."""
    playlist = radio_state.get('playlist', [])
    
    # Если плейлист пуст, пробуем создать радио
    if not playlist:
        current = radio_state.get('current_track')
        if current and current.get('id'):
            try:
                spotify = get_spotify_client()
                playlist = spotify.create_radio_playlist(current['id'], limit=20)
                radio_state['playlist'] = playlist
                radio_state['current_index'] = 0
            except:
                pass
    
    if not playlist:
        return jsonify({'error': 'Сначала найдите трек или создайте радио!'}), 400
    
    idx = radio_state.get('current_index', 0) or 0
    playlist_len = len(playlist)
    radio_state['current_index'] = (idx + 1) % playlist_len
    radio_state['current_track'] = playlist[radio_state['current_index']]
    
    return jsonify({'track': radio_state['current_track']})


@app.route('/api/prev', methods=['POST'])
def prev_track():
    """API для предыдущего трека."""
    playlist = radio_state.get('playlist', [])
    
    # Если плейлист пуст, пробуем создать радио
    if not playlist:
        current = radio_state.get('current_track')
        if current and current.get('id'):
            try:
                spotify = get_spotify_client()
                playlist = spotify.create_radio_playlist(current['id'], limit=20)
                radio_state['playlist'] = playlist
                radio_state['current_index'] = 0
            except:
                pass
    
    if not playlist:
        return jsonify({'error': 'Сначала найдите трек или создайте радио!'}), 400
    
    idx = radio_state.get('current_index', 0) or 0
    playlist_len = len(playlist)
    radio_state['current_index'] = (idx - 1) % playlist_len
    radio_state['current_track'] = playlist[radio_state['current_index']]
    
    return jsonify({'track': radio_state['current_track']})


@app.route('/api/pause', methods=['POST'])
def pause():
    """API для паузы."""
    radio_state['is_playing'] = False
    return jsonify({'success': True})


@app.route('/api/resume', methods=['POST'])
def resume():
    """API для возобновления."""
    radio_state['is_playing'] = True
    return jsonify({'success': True})


# Локальные файлы
import os
from pathlib import Path

@app.route('/api/local/files')
def get_local_files():
    """Получить список локальных файлов."""
    music_dir = Path(__file__).parent.parent / 'music'
    audio_exts = {'.mp3', '.wav', '.ogg', '.flac', '.m4a'}
    files = []
    if music_dir.exists():
        for f in music_dir.iterdir():
            if f.is_file() and f.suffix.lower() in audio_exts:
                files.append(f.name)
    return jsonify({'files': files})


@app.route('/api/local/play', methods=['POST'])
def play_local():
    """Воспроизвести локальный файл."""
    data = request.json
    filename = data.get('filename')
    
    if not filename:
        return jsonify({'error': 'filename is required'}), 400
    
    music_dir = Path(__file__).parent.parent / 'music'
    file_path = music_dir / filename
    
    if not file_path.exists():
        return jsonify({'error': 'File not found'}), 404
    
    # Обновляем состояние
    radio_state['current_track'] = {
        'name': filename,
        'artist': 'Локальный файл',
        'type': 'local'
    }
    radio_state['is_playing'] = True
    radio_state['local_file'] = str(file_path)
    
    return jsonify({
        'success': True, 
        'track': radio_state['current_track']
    })


@app.route('/api/queue/add', methods=['POST'])
def queue_add():
    """Добавить трек в очередь воспроизведения."""
    data = request.json
    track = data.get('track')
    
    if not track:
        return jsonify({'error': 'track is required'}), 400
    
    if 'playlist' not in radio_state:
        radio_state['playlist'] = []
    
    radio_state['playlist'].append(track)
    
    return jsonify({
        'success': True,
        'queue_length': len(radio_state['playlist'])
    })


@app.route('/api/queue/remove', methods=['POST'])
def queue_remove():
    """Удалить трек из очереди по индексу."""
    data = request.json
    index = data.get('index')
    
    if 'playlist' not in radio_state or not radio_state['playlist']:
        return jsonify({'error': 'Плейлист пуст'}), 400
    
    try:
        removed = radio_state['playlist'].pop(index)
        return jsonify({'success': True, 'removed': removed})
    except IndexError:
        return jsonify({'error': 'Неверный индекс'}), 400


@app.route('/api/queue/shuffle', methods=['POST'])
def queue_shuffle():
    """Перемешать плейлист."""
    import random
    
    playlist = radio_state.get('playlist', [])
    
    # Если плейлист пуст, пробуем создать радио
    if not playlist:
        current = radio_state.get('current_track')
        if current and isinstance(current, dict) and current.get('id'):
            try:
                spotify = get_spotify_client()
                playlist = spotify.create_radio_playlist(current['id'], limit=20)
                radio_state['playlist'] = playlist
                radio_state['current_index'] = 0
            except:
                pass
    
    if not playlist:
        return jsonify({'error': 'Сначала найдите трек или создайте радио!'}), 400
    
    random.shuffle(radio_state['playlist'])
    radio_state['current_index'] = 0
    
    return jsonify({'success': True})


@app.route('/api/queue/clear', methods=['POST'])
def queue_clear():
    """Очистить плейлист."""
    radio_state['playlist'] = []
    radio_state['current_index'] = 0
    radio_state['current_track'] = None
    
    return jsonify({'success': True})


@app.route('/api/queue/reorder', methods=['POST'])
def queue_reorder():
    """Переместить трек в плейлисте."""
    data = request.json
    from_index = data.get('from_index')
    to_index = data.get('to_index')
    
    if 'playlist' not in radio_state or not radio_state['playlist']:
        return jsonify({'error': 'Плейлист пуст'}), 400
    
    try:
        track = radio_state['playlist'].pop(from_index)
        radio_state['playlist'].insert(to_index, track)
        return jsonify({'success': True})
    except IndexError:
        return jsonify({'error': 'Неверный индекс'}), 400


# Управление громкостью
@app.route('/api/volume', methods=['POST'])
def set_volume():
    """Установить громкость (0-100)."""
    data = request.json
    volume = data.get('volume', 50)
    
    if not isinstance(volume, (int, float)):
        return jsonify({'error': 'volume must be a number'}), 400
    
    volume = max(0, min(100, int(volume)))
    radio_state['volume'] = volume
    
    return jsonify({'success': True, 'volume': volume})


@app.route('/api/volume/up', methods=['POST'])
def volume_up():
    """Увеличить громкость."""
    current = radio_state.get('volume', 50)
    radio_state['volume'] = min(100, current + 10)
    return jsonify({'success': True, 'volume': radio_state['volume']})


@app.route('/api/volume/down', methods=['POST'])
def volume_down():
    """Уменьшить громкость."""
    current = radio_state.get('volume', 50)
    radio_state['volume'] = max(0, current - 10)
    return jsonify({'success': True, 'volume': radio_state['volume']})


# История воспроизведения
@app.route('/api/history', methods=['GET'])
def get_history():
    """Получить историю воспроизведения."""
    history = radio_state.get('history', [])
    return jsonify({'history': history})


@app.route('/api/history/add', methods=['POST'])
def add_to_history():
    """Добавить трек в историю."""
    data = request.json
    track = data.get('track')
    
    if not track:
        return jsonify({'error': 'track is required'}), 400
    
    if 'history' not in radio_state:
        radio_state['history'] = []
    
    # Добавляем в начало, избегаем дубликатов
    history = radio_state['history']
    history = [t for t in history if t.get('id') != track.get('id')]
    history.insert(0, track)
    radio_state['history'] = history[:50]  # Храним последние 50
    
    return jsonify({'success': True})


# Добавить трек в очередь из результатов поиска
@app.route('/api/queue/add-from-search', methods=['POST'])
def add_from_search():
    """Добавить трек в очередь из результатов поиска."""
    data = request.json
    track = data.get('track')
    
    if not track:
        return jsonify({'error': 'track is required'}), 400
    
    if 'playlist' not in radio_state:
        radio_state['playlist'] = []
    
    radio_state['playlist'].append(track)
    
    return jsonify({
        'success': True,
        'queue_length': len(radio_state['playlist'])
    })


# API для получения всех данных состояния
@app.route('/api/state', methods=['GET'])
def get_state():
    """Получить полное состояние радио."""
    return jsonify({
        'is_playing': radio_state.get('is_playing', False),
        'current_track': radio_state.get('current_track'),
        'playlist': radio_state.get('playlist', []),
        'current_index': radio_state.get('current_index', 0),
        'volume': radio_state.get('volume', 50),
        'history': radio_state.get('history', [])[:10]
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
