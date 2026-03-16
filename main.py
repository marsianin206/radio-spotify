"""
Spotify Radio - Универсальное радио-приложение
Поддержка: CLI, Web, Discord
"""
import sys
import argparse


def main():
    """Главная точка входа."""
    from dotenv import load_dotenv
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description="Spotify Radio - Трансляция музыки из Spotify"
    )
    parser.add_argument(
        'mode',
        choices=['cli', 'web', 'discord', 'all'],
        nargs='?',
        default='cli',
        help='Режим запуска: cli (консоль), web (веб-интерфейс), discord (Discord бот), all (все вместе)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Порт для веб-интерфейса (по умолчанию: 5000)'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Хост для веб-интерфейса (по умолчанию: 0.0.0.0)'
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
        app.run(host=args.host, port=args.port, debug=True)
        
    elif args.mode == 'discord':
        print("🤖 Запуск Discord бота...")
        import os
        from bot.main import bot
        
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            print("❌ Не найден DISCORD_TOKEN в .env файле")
            print("Для запуска бота добавьте DISCORD_TOKEN=ваш_токен в .env")
            sys.exit(1)
        
        bot.run(token)

    elif args.mode == 'all':
        print("🚀 Запуск всех сервисов (веб + Discord бот)...")
        import os
        import threading
        import asyncio
        
        # Запускаем веб в отдельном потоке
        def run_web():
            from web.app import app
            app.run(host=args.host, port=args.port, debug=False)
        
        web_thread = threading.Thread(target=run_web, daemon=True)
        web_thread.start()
        print(f"🌐 Веб-интерфейс запущен на порту {args.port}")
        
        # Запускаем Discord бота
        from bot.main import bot
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            print("❌ Не найден DISCORD_TOKEN в .env файле")
            print("Веб интерфейс работает, но бот не запущен")
        else:
            print("🤖 Discord бот запущен")
            bot.run(token)


if __name__ == '__main__':
    main()
