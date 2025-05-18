"""
Модуль инициализации базы данных
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql://user:password@db:5432/mydatabase"

engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)


def get_db():
    """Создает и предоставляет сессию базы данных, обеспечивая ее закрытие после использования."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Инициализирует базу данных, создавая все таблицы, определенные через SQLAlchemy Base.metadata."""
    Base.metadata.create_all(bind=engine)
    print("База данных инициализирована (таблицы созданы).")
