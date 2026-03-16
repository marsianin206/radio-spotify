# 🎧 Spotify Radio

Веб-приложение для поиска и трансляции музыки из Spotify.

## 🌐 Деплой на Vercel

### Быстрый старт

1. **Установите Vercel CLI** (если не установлен):
```bash
npm i -g vercel
```

2. **Войдите в Vercel:**
```bash
vercel login
```

3. **Задеплойте проект:**
```bash
vercel
```

### Ручной деплой через GitHub

1. Загрузите код на GitHub
2. Перейдите на [vercel.com](https://vercel.com)
3. Нажмите "New Project"
4. Импортируйте ваш репозиторий
5. Настройте:
   - Framework Preset: **Other**
   - Build Command: оставьте пустым
   - Output Directory: оставьте пустым
6. Нажмите **Deploy**

## ⚙️ Настройка переменных окружения на Vercel

Добавьте переменные в **Vercel Dashboard** → **Settings** → **Environment Variables**:

| Имя | Значение |
|-----|----------|
| `CLIENT_ID` | Ваш Spotify Client ID |
| `CLIENT_SECRET` | Ваш Spotify Client Secret |

## 🔧 Локальный запуск

```bash
# Установите зависимости
pip install -r requirements.txt

# Запустите локально
python main.py web
# или
python web/app.py
```

Откройте http://localhost:5000

## 📁 Структура проекта

```
radio spotify/
├── .env                 # Переменные окружения
├── main.py              # Главный файл (локальный запуск)
├── requirements.txt     # Зависимости Python
├── vercel.json          # Конфигурация Vercel
├── README.md            # Документация
├── spotify/
│   ├── __init__.py
│   └── client.py       # Spotify API клиент
├── audio/
│   ├── __init__.py
│   └── engine.py       # Аудио-движок
├── web/
│   └── app.py          # Flask приложение
├── cli/
│   └── main.py         # CLI интерфейс (локально)
└── bot/
    └── main.py         # Discord бот (локально)
```

## ⚠️ Ограничения Vercel

- **Serverless**: состояние сбрасывается между запросами
- **Serverless не поддерживает**: долгие соединения, WebSocket, потоковое аудио
- **Discord бот и CLI**: работают только локально, не на Vercel

Для полноценного радио с потоковым воспроизведением используйте локальный запуск или другой хостинг (Railway, Render, VPS).
