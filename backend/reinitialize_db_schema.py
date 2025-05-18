import sys
import time
import os

from app.database import init_db, SessionLocal
from app import create_app
from app.models.user import User
from app.auth import hash_password

print("Attempting to re-initialize database schema...", file=sys.stderr)

try:
    # Создаем контекст приложения и вызываем init_db()
    app = create_app()
    with app.app_context():
        init_db()
    print("Database schema re-initialized successfully by test service.", file=sys.stderr)

    db = SessionLocal()
    try:
        existing_admin = db.query(User).filter(
            (User.username == "admin") | (User.email == "admin@example.com")
        ).first()

        if not existing_admin:
            print("Creating default admin user...", file=sys.stderr)
            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=hash_password("adminpassword"),
                is_admin=True
            )
            db.add(admin_user)
            db.commit()
            print("Default admin user 'admin' created.", file=sys.stderr)
        else:
            print("Default admin user already exists.", file=sys.stderr)

    except Exception as user_e:
        print(f"Error creating default admin user: {user_e}", file=sys.stderr)
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

except Exception as e:
    # Выводим ошибку и завершаем скрипт с ненулевым кодом, если инициализация не удалась
    print(f"Error during database schema re-initialization: {e}", file=sys.stderr)
    sys.exit(1)
