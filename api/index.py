"""Vercel API Handler - экспортирует Flask приложение."""
from web.app import app

# Экспортируем app для Vercel
handler = app
