"""Vercel API Handler - экспортирует Flask приложение."""
import os
import sys

# Добавляем корневую директорию проекта в путь
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Для отладки - печатаем пути
print(f"Project root: {project_root}", file=sys.stderr)
print(f"sys.path: {sys.path}", file=sys.stderr)

try:
    from web.app import app
    # Экспортируем app для Vercel
    handler = app
    print("App loaded successfully", file=sys.stderr)
except Exception as e:
    print(f"Error loading app: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    raise
