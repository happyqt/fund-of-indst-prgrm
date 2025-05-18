"""Интеграционные тесты для API работы с книгами."""
# pylint: disable=redefined-outer-name
import pytest
from app.models.user import User  # Нужен для создания владельца книги
from app.models.book import Book  # Нужен для проверки данных в БД
from app.auth import hash_password
from tests.integration.conftest import basic_auth_headers


@pytest.fixture(scope="function")
def authenticated_user(db_session):
    username = "testauthuser"
    password = "testpassword"

    hashed_pw = hash_password(password)
    user = User(username=username, email=f"{username}@example.com", hashed_password=hashed_pw)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    auth_headers = basic_auth_headers(username, password)
    return user, auth_headers


def test_get_books_empty(client, db_session):
    """Проверка GET /api/books когда нет книг."""
    response = client.get('/api/books')  # Делаем GET запрос через тестовый клиент

    # Проверяем статус код ответа
    assert response.status_code == 200
    # Проверяем, что тело ответа - пустой JSON массив
    assert response.get_json() == []


def test_add_book(client, db_session, authenticated_user):
    """Проверка POST /api/books на успешное добавление книги."""
    user, auth_headers = authenticated_user

    book_data_payload = {
        "title": "Новая Тестовая Книга",
        "author": "Тестовый Автор",
        "description": "Эта книга добавлена тестом."
    }

    response = client.post('/api/books', json=book_data_payload, headers=auth_headers)

    assert response.status_code == 201
    response_json = response.get_json()
    assert "id" in response_json
    assert response_json["title"] == book_data_payload["title"]
    assert response_json["author"] == book_data_payload["author"]
    assert response_json.get("description") == book_data_payload["description"]
    assert response_json["owner_id"] == user.id  # Проверяем, что владелец - аутентифицированный пользователь
    assert response_json["is_available"] is True

    added_book = db_session.query(Book).filter_by(id=response_json["id"]).first()
    assert added_book is not None
    assert added_book.title == book_data_payload["title"]
    assert added_book.owner_id == user.id
    assert added_book.is_available is True


def test_add_book_unauthenticated(client, db_session):
    """Проверка POST /api/books без аутентификации."""
    book_data_payload = {
        "title": "Книга без аутентификации",
        "author": "Аноним",
    }
    response = client.post('/api/books', json=book_data_payload)
    assert response.status_code == 401


def test_add_book_missing_fields(client, db_session, authenticated_user):
    """Проверка POST /api/books с отсутствующими обязательными полями."""
    user, auth_headers = authenticated_user

    # Отсутствует 'author'
    book_data_missing_author = {
        "title": "Книга без автора",
        "description": "Описание"
    }
    response = client.post('/api/books', json=book_data_missing_author, headers=auth_headers)
    assert response.status_code == 400
    assert "Missing required fields" in response.get_json().get("error", "")

    # Отсутствует 'title'
    book_data_missing_title = {
        "author": "Автор",
        "description": "Описание"
    }
    response = client.post('/api/books', json=book_data_missing_title, headers=auth_headers)
    assert response.status_code == 400
    assert "Missing required fields" in response.get_json().get("error", "")


def test_get_book_existing(client, db_session):
    """Проверка GET /api/books/{book_id} для существующей книги."""

    owner_user = User(username="owner_get", email="owner_get@example.com", hashed_password=hash_password("aboba1337"))
    db_session.add(owner_user)
    db_session.commit()
    db_session.refresh(owner_user)

    test_book = Book(title="Существующая Книга", author="Существующий Автор", owner_id=owner_user.id,
                     description="Описание.")
    db_session.add(test_book)
    db_session.commit()
    db_session.refresh(test_book)

    response = client.get(f'/api/books/{test_book.id}')

    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json["id"] == test_book.id
    assert response_json["title"] == "Существующая Книга"
    assert response_json["author"] == "Существующий Автор"
    assert response_json.get("description") == "Описание."
    assert response_json["owner_id"] == owner_user.id
    assert response_json["is_available"] is True


def test_get_book_not_found(client, db_session):
    """Проверка GET /api/books/{book_id} для несуществующей книги."""
    # DB пуста, книги с ID 999 нет
    response = client.get('/api/books/999')

    assert response.status_code == 404  # Ожидаем 404 Not Found
    assert "Book not found" in response.get_json().get("message", "")
