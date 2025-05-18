import sys
import time
import os

from app.database import init_db
from app import create_app

print("Attempting to re-initialize database schema...", file=sys.stderr)

try:
    # Создаем контекст приложения и вызываем init_db()
    app = create_app()
    with app.app_context():
        init_db()
    print("Database schema re-initialized successfully by test service.", file=sys.stderr)

except Exception as e:
    # Выводим ошибку и завершаем скрипт с ненулевым кодом, если инициализация не удалась
    print(f"Error during database schema re-initialization: {e}", file=sys.stderr)
    sys.exit(1)
