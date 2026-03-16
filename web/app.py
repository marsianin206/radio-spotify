"""Веб-интерфейс Spotify Radio для Vercel."""
import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify, Response

# HTML шаблон (встроенный для Vercel совместимости)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Spotify Radio</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #1DB954 0%, #191414 100%); min-height: 100vh; color: white; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        header { text-align: center; padding: 40px 0; }
        h1 { font-size: 3rem; margin-bottom: 10px; }
        .search-box { display: flex; gap: 10px; max-width: 600px; margin: 0 auto 30px; }
        input { flex: 1; padding: 15px 20px; border: none; border-radius: 30px; font-size: 16px; outline: none; }
        button { padding: 15px 30px; border: none; border-radius: 30px; background: #1DB954; color: white; font-size: 16px; cursor: pointer; }
        button:hover { transform: scale(1.05); }
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
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎧 Spotify Radio</h1>
            <p>Поиск и потоковая трансляция музыки</p>
        </header>
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="Поиск трека...">
            <button onclick="search()">Поиск</button>
        </div>
        <div class="results" id="results" style="display:none;">
            <h2>Результаты поиска</h2>
            <div id="resultsList"></div>
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
            <div class="playlist" id="playlistSection" style="display:none;">
                <h2>Плейлист</h2>
                <div id="playlist"></div>
            </div>
        </div>
    </div>
    <script>
        let currentState = { isPlaying: false, currentTrack: null, playlist: [] };
        async function search() {
            const query = document.getElementById('searchInput').value;
            if (!query) return;
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            if (data.tracks) showResults(data.tracks);
        }
        function showResults(tracks) {
            const resultsDiv = document.getElementById('results');
            const resultsList = document.getElementById('resultsList');
            resultsList.innerHTML = tracks.map((track) => 
                `<div class="track-item" onclick="selectTrack('${track.id}')">
                    <img src="${track.image || ''}" alt="${track.name}">
                    <div class="track-info">
                        <div>${track.name}</div>
                        <div class="artist-name">${track.artist}</div>
                    </div>
                </div>`
            ).join('');
            resultsDiv.style.display = 'block';
        }
        async function selectTrack(trackId) {
            const response = await fetch('/api/play', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({track_id: trackId}) });
            const data = await response.json();
            if (data.track) showPlayer(data.track);
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
    
    if not track_id:
        return jsonify({'error': 'track_id is required'}), 400
    
    try:
        spotify = get_spotify_client()
        track = spotify.get_track(track_id)
        radio_state['current_track'] = track
        radio_state['is_playing'] = True
        return jsonify({'success': True, 'track': track})
    except Exception as e:
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
    if not playlist:
        return jsonify({'error': 'No playlist'}), 400
    
    idx = radio_state.get('current_index', 0) or 0
    playlist_len = len(playlist)
    radio_state['current_index'] = (idx + 1) % playlist_len
    radio_state['current_track'] = playlist[radio_state['current_index']]
    
    return jsonify({'track': radio_state['current_track']})


@app.route('/api/prev', methods=['POST'])
def prev_track():
    """API для предыдущего трека."""
    playlist = radio_state.get('playlist', [])
    if not playlist:
        return jsonify({'error': 'No playlist'}), 400
    
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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
