"""
Spotify Radio - Универсальное радио-приложение
Поддержка: CLI, Web, Discord
"""
import sys
import argparse


def main():
    """Главная точка входа."""
    parser = argparse.ArgumentParser(
        description="Spotify Radio - Трансляция музыки из Spotify"
    )
    parser.add_argument(
        'mode',
        choices=['cli', 'web', 'discord'],
        nargs='?',
        default='cli',
        help='Режим запуска: cli (консоль), web (веб-интерфейс), discord (Discord бот)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Порт для веб-интерфейса (по умолчанию: 5000)'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'cli':
        print("🎧 Запуск CLI режима...")
        from cli.main import main as cli_main
        import asyncio
        asyncio.run(cli_main())
        
    elif args.mode == 'web':
        print(f"🌐 Запуск веб-интерфейса на порту {args.port}...")
        from web.app import app
        app.run(host='0.0.0.0', port=args.port, debug=True)
        
    elif args.mode == 'discord':
        print("🤖 Запуск Discord бота...")
        from bot.main import bot
        # Для бота нужно добавить токен в файл .env
        from dotenv import load_dotenv
        import os
        load_dotenv()
        
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            print("❌ Не найден DISCORD_TOKEN в .env файле")
            print("Для запуска бота добавьте DISCORD_TOKEN=ваш_токен в .env")
            sys.exit(1)
        
        bot.run(token)


if __name__ == '__main__':
    main()
