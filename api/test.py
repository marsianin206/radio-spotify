"""Минимальный тест Vercel."""
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({"status": "ok", "message": "Test works!"})

@app.route('/api/test')
def test():
    return jsonify({"test": "passed"})

# Vercel требует 'app', не 'handler'
