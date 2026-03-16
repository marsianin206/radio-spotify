"""Vercel API Handler."""
import os
import sys

# Добавляем корневую директорию в путь
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from web.app import app

# Экспортируем для Vercel
handler = app
