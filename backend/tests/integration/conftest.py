"""Модуль общих конфигураций для тестов"""
# pylint: disable=redefined-outer-name
import pytest
import base64
from app import create_app
from app.database import engine, Base, SessionLocal
from app.models.user import User
from app.models.book import Book
from app.auth import hash_password


def basic_auth_headers(username, password):
    credentials = f"{username}:{password}"
    token = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    return {'Authorization': f'Basic {token}'}


@pytest.fixture(scope="session")
def app():
    """Фикстура, предоставляющая экземпляр Flask приложения для всей сессии."""
    flask_app = create_app()
    yield flask_app


@pytest.fixture(scope="function")
def client(app):
    """Фикстура, предоставляющая тестовый клиент Flask."""
    with app.test_client() as client:
        yield client


@pytest.fixture(scope="function")
def db_session():
    """
    Фикстура для создания/удаления таблиц БД для каждого тестового сценария.
    Также предоставляет сессию для добавления начальных данных теста.
    """
    Base.metadata.drop_all(bind=engine)  # Очистка перед тестом
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
# pylint: disable=unused-argument
def create_user(db_session):
    """
    Фабрика для создания пользователя непосредственно в БД.
    Возвращает созданный объект User.
    """

    def _create_user(username, password, email, is_admin=False):
        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),  # Используем hash_password из app.auth
            is_admin=is_admin
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _create_user


@pytest.fixture
# pylint: disable=unused-argument
def create_book(db_session):
    """
    Фабрика для создания книги непосредственно в БД.
    Возвращает созданный объект Book.
    """

    def _create_book(title, author, owner_id, description="Test book desc", is_available=True):
        book = Book(
            title=title,
            author=author,
            owner_id=owner_id,
            description=description,
            is_available=is_available
        )
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)
        return book

    return _create_book
