import sys
import time
import os

from app.database import init_db, SessionLocal
from app import create_app
from app.models.user import User
from app.models.book import Book
from app.auth import hash_password
from sqlalchemy.exc import SQLAlchemyError

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

        existing_books_count = db.query(Book).filter(Book.owner_id == admin_user.id).count()

        if existing_books_count == 0:
            print(f"Adding initial books for admin user...", file=sys.stderr)
            initial_books = [
                Book(title="Нормативный документ #1", author="Учебный офис", owner_id=admin_user.id,
                     description="Классика(никто не читает)"),
                Book(title="Лор cue2a", author="vlad seliar", owner_id=admin_user.id,
                     description="Лучше не читать."),
                Book(title="Матанализ матанализ", author="Виктор Лопаткин", owner_id=admin_user.id,
                     description="calculus", is_available=False)
            ]
            db.add_all(initial_books)
            db.commit()
            print(f"Added {len(initial_books)} initial books for admin user.", file=sys.stderr)
        else:
            print(
                f"Admin user already has {existing_books_count} books. Skipping initial book creation.",
                file=sys.stderr)


    except SQLAlchemyError as user_db_error:
        print(f"Database error during user/book initialization: {user_db_error}", file=sys.stderr)
        db.rollback()
        sys.exit(1)
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
