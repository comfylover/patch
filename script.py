# debug_launcher.py

import asyncio
from aiohttp import web
import session_utils  # Импортируем наш основной файл
import sys


async def main():
    if not session_utils.SESSION_UTILS_LOADED:
        print("ОШИБКА: Не удалось загрузить session_utils.py. Проверьте зависимости.", file=sys.stderr)
        print("Пожалуйста, выполните: pip install aiohttp pycryptodome 'aiohttp_session[secure]'", file=sys.stderr)
        return

    app = web.Application()
    routes = web.RouteTableDef()

    session_utils.setup_routes(routes, app)

    app.add_routes(routes)

    runner = web.AppRunner(app)
    await runner.setup()

    host = "127.0.0.1"
    port = 8080
    site = web.TCPSite(runner, host, port)
    await site.start()

    print(f"Пароль захардкожен в session_utils.py.")
    print(f"  - Основной режим: http://{host}:{port}/login")
    print(f"  - Аварийный режим: http://{host}:{port}/fallback")
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nСервер остановлен.")