"""Интеграционные тесты для API работы с книгами."""
# pylint: disable=redefined-outer-name
import pytest
from app.models.user import User  # Нужен для создания владельца книги
from app.models.book import Book  # Нужен для проверки данных в БД
from app.models.exchange import Exchange
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


@pytest.fixture(scope="function")
def other_user(db_session, create_user):
    """Фикстура для создания 'другого' пользователя."""
    username = "otheruser"
    password = "otherpassword"
    user = create_user(username=username, password=password, email=f"{username}@example.com")
    return user


@pytest.fixture(scope="function")
def other_user_auth_headers(other_user):
    return basic_auth_headers(other_user.username, "otherpassword")


def test_get_books_empty(client, db_session):
    """Проверка GET /api/books когда нет книг."""
    response = client.get('/api/books')

    assert response.status_code == 200
    resp_json = response.get_json()
    # Новый формат: {books: [], total: 0, ...}
    assert resp_json['books'] == []
    assert resp_json['total'] == 0


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


def test_get_my_books_empty(client, authenticated_user):
    """Проверка GET /api/users/me/books когда у пользователя нет книг."""
    _user, auth_headers = authenticated_user
    response = client.get('/api/users/me/books', headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json() == []


def test_get_my_books_with_books(client, db_session, authenticated_user, create_book, other_user):
    """Проверка GET /api/users/me/books когда у пользователя есть книги."""
    user1, auth_headers1 = authenticated_user

    # Книги текущего пользователя
    book1_user1 = create_book(title="My Book 1", author="Me", owner_id=user1.id)
    book2_user1 = create_book(title="My Book 2", author="Me", owner_id=user1.id, is_available=False)

    # Книга другого пользователя
    create_book(title="Other's Book", author="Other", owner_id=other_user.id)

    response = client.get('/api/users/me/books', headers=auth_headers1)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2

    book_titles = {item['title'] for item in data}
    assert book1_user1.title in book_titles
    assert book2_user1.title in book_titles

    for item in data:
        if item['id'] == book1_user1.id:
            assert item['is_available'] is True
        if item['id'] == book2_user1.id:
            assert item['is_available'] is False


def test_get_my_books_unauthenticated(client):
    """Проверка GET /api/users/me/books без аутентификации."""
    response = client.get('/api/users/me/books')
    assert response.status_code == 401


def test_update_my_book_success(client, db_session, authenticated_user, create_book):
    """Проверка успешного обновления своей книги."""
    user, auth_headers = authenticated_user
    book = create_book(title="Old Title", author="Old Author", owner_id=user.id)

    update_payload = {
        "title": "New Title",
        "author": "New Author",
        "description": "Updated description.",
        "is_available": False
    }
    response = client.put(f'/api/books/{book.id}', json=update_payload, headers=auth_headers)

    assert response.status_code == 200
    data = response.get_json()
    assert data["title"] == update_payload["title"]
    assert data["author"] == update_payload["author"]
    assert data["description"] == update_payload["description"]
    assert data["is_available"] == update_payload["is_available"]

    db_session.refresh(book)
    assert book.title == update_payload["title"]
    assert book.is_available is False


def test_update_book_partial(client, db_session, authenticated_user, create_book):
    """Проверка частичного обновления своей книги."""
    user, auth_headers = authenticated_user
    book = create_book(title="Original Title", author="Original Author", owner_id=user.id)

    update_payload = {"description": "Only description updated."}
    response = client.put(f'/api/books/{book.id}', json=update_payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["description"] == update_payload["description"]
    assert data["title"] == book.title  # Title должен остаться прежним

    db_session.refresh(book)
    assert book.description == update_payload["description"]


def test_update_book_not_owner(client, db_session, authenticated_user, other_user_auth_headers, create_book):
    """Попытка обновить книгу, не будучи ее владельцем."""
    user_owner, _ = authenticated_user
    book = create_book(title="Owner's Book", author="Owner", owner_id=user_owner.id)

    update_payload = {"title": "Attempted New Title"}
    response = client.put(f'/api/books/{book.id}', json=update_payload, headers=other_user_auth_headers)
    assert response.status_code == 403


def test_update_book_not_found(client, authenticated_user):
    """Попытка обновить несуществующую книгу."""
    _user, auth_headers = authenticated_user
    response = client.put('/api/books/9999', json={"title": "Nada"}, headers=auth_headers)
    assert response.status_code == 404


def test_delete_my_book_success(client, db_session, authenticated_user, create_book):
    """Проверка успешного удаления своей книги без активных обменов."""
    user, auth_headers = authenticated_user
    book = create_book(title="To Be Deleted", author="Author", owner_id=user.id)
    book_id = book.id

    response = client.delete(f'/api/books/{book_id}', headers=auth_headers)
    assert response.status_code == 200
    assert "Book successfully deleted" in response.get_json()["message"]

    deleted_book = db_session.query(Book).filter_by(id=book_id).first()
    assert deleted_book is None


def test_delete_book_involved_in_pending_exchange_fails(client, db_session, authenticated_user, other_user,
                                                        create_book):
    """Попытка удалить книгу, участвующую в активном ('pending') обмене 409."""
    proposing_user, proposing_auth_headers = authenticated_user
    receiving_user = other_user

    book_to_delete = create_book(title="Delete Me If You Can", author="Proposer", owner_id=proposing_user.id)
    requested_book = create_book(title="Keep Me Safe", author="Receiver", owner_id=receiving_user.id)

    exchange_payload = {
        "proposed_book_id": book_to_delete.id,
        "requested_book_id": requested_book.id
    }
    resp_exchange = client.post('/api/exchanges', json=exchange_payload, headers=proposing_auth_headers)
    assert resp_exchange.status_code == 201
    exchange_id = resp_exchange.get_json()["id"]

    exchange_in_db = db_session.query(Exchange).filter_by(id=exchange_id).first()
    assert exchange_in_db is not None

    # Попытка удалить книгу
    response_delete = client.delete(f'/api/books/{book_to_delete.id}', headers=proposing_auth_headers)
    assert response_delete.status_code == 409
    assert "part of exchange history" in response_delete.get_json()["message"]

    # Книга не должна быть удалена
    assert db_session.query(Book).filter_by(id=book_to_delete.id).first() is not None
    # Обмен должен остаться в статусе pending
    db_session.refresh(exchange_in_db)
    assert exchange_in_db.status == 'pending'


def test_delete_book_involved_in_completed_exchange_fails(client, db_session, authenticated_user, other_user,
                                                          other_user_auth_headers, create_book):
    """Попытка удалить книгу, участвовавшую в завершенном ('accepted') обмене 409."""
    user1, user1_headers = authenticated_user
    user2 = other_user
    user2_headers = other_user_auth_headers

    book_owned_by_user1 = create_book(title="Book From User1", author="User1", owner_id=user1.id)
    book_owned_by_user2 = create_book(title="Book From User2", author="User2", owner_id=user2.id)

    # User1 предлагает обмен User2
    exchange_payload = {
        "proposed_book_id": book_owned_by_user1.id,
        "requested_book_id": book_owned_by_user2.id
    }
    resp_propose = client.post('/api/exchanges', json=exchange_payload, headers=user1_headers)
    assert resp_propose.status_code == 201
    exchange_id = resp_propose.get_json()["id"]

    # User2 принимает обмен
    resp_accept = client.post(f'/api/exchanges/{exchange_id}/accept', headers=user2_headers)
    assert resp_accept.status_code == 200

    db_session.refresh(book_owned_by_user1)
    db_session.refresh(book_owned_by_user2)
    # После обмена владельцем book_owned_by_user1 стал user2
    # Попытаемся удалить ее от имени user2 (текущего владельца)
    book_to_delete_after_exchange = db_session.query(Book).filter_by(id=book_owned_by_user1.id).first()
    assert book_to_delete_after_exchange.owner_id == user2.id  # Проверим, что владелец сменился

    response_delete = client.delete(f'/api/books/{book_owned_by_user1.id}', headers=user2_headers)
    assert response_delete.status_code == 409
    assert "part of exchange history" in response_delete.get_json()["message"]

    assert db_session.query(Book).filter_by(id=book_owned_by_user1.id).first() is not None


def test_delete_book_not_owner(client, db_session, authenticated_user, other_user_auth_headers, create_book):
    """Попытка удалить книгу, не будучи ее владельцем."""
    user_owner, _ = authenticated_user
    book = create_book(title="Owner's Book To Delete", author="Owner", owner_id=user_owner.id)
    response = client.delete(f'/api/books/{book.id}', headers=other_user_auth_headers)
    assert response.status_code == 403


def test_delete_book_not_found(client, authenticated_user):
    """Попытка удалить несуществующую книгу."""
    _user, auth_headers = authenticated_user
    response = client.delete('/api/books/8888', headers=auth_headers)
    assert response.status_code == 404


def test_get_books_with_filters(client, db_session, create_user, create_book):
    """Проверка GET /api/books с различными фильтрами."""
    owner = create_user(username="filter_owner", password="password", email="filter@owner.com")

    book1 = create_book(title="Python Programming", author="John Doe", owner_id=owner.id)
    book2 = create_book(title="Advanced Python", author="Jane Doe", owner_id=owner.id)
    book3 = create_book(title="Web Development with Flask", author="John Smith", owner_id=owner.id)
    book4 = create_book(title="Data Science Handbook", author="Peter Pan", owner_id=owner.id, is_available=False)

    def get_books(url):
        """Helper: returns books list from paginated response."""
        r = client.get(url)
        assert r.status_code == 200
        resp = r.get_json()
        # Поддерживаем оба формата (новый и старый)
        return resp['books'] if isinstance(resp, dict) else resp

    # Фильтр по названию (должен найти book1 и book2)
    data = get_books('/api/books?title=Python')
    assert len(data) == 2
    titles = {item['title'] for item in data}
    assert book1.title in titles
    assert book2.title in titles

    # Фильтр по названию (регистр)
    data = get_books('/api/books?title=python')
    assert len(data) == 2
    titles = {item['title'] for item in data}
    assert book1.title in titles
    assert book2.title in titles

    # Фильтр по автору
    data = get_books('/api/books?author=Doe')
    assert len(data) == 2
    authors = {item['author'] for item in data}
    assert book1.author in authors
    assert book2.author in authors

    # Фильтр по названию и автору (должен найти book1)
    data = get_books('/api/books?title=Python&author=John Doe')
    assert len(data) == 1
    assert data[0]['title'] == book1.title
    assert data[0]['author'] == book1.author

    # Фильтр по части названия (должен найти book3)
    data = get_books('/api/books?title=Flask')
    assert len(data) == 1
    assert data[0]['title'] == book3.title

    # Фильтр, который ничего не находит
    data = get_books('/api/books?title=NonExistentBook')
    assert data == []

    # Фильтр по автору, который ничего не находит
    data = get_books('/api/books?author=Nobody')
    assert data == []

    # Проверка, что недоступные книги не возвращаются даже с фильтром
    data = get_books('/api/books?title=Data Science')
    assert data == []


def test_get_books_no_filters_returns_all_available(client, db_session, create_user, create_book):
    """Проверка, что GET /api/books без фильтров возвращает все доступные книги."""
    owner = create_user(username="all_owner", password="password", email="all@owner.com")
    book1 = create_book(title="Available Book 1", author="Author A", owner_id=owner.id, is_available=True)
    book2 = create_book(title="Available Book 2", author="Author B", owner_id=owner.id, is_available=True)
    create_book(title="Unavailable Book", author="Author C", owner_id=owner.id, is_available=False)

    response = client.get('/api/books')
    assert response.status_code == 200
    resp = response.get_json()
    # Поддерживаем оба формата
    data = resp['books'] if isinstance(resp, dict) else resp
    assert len(data) == 2
    titles = {item['title'] for item in data}
    assert book1.title in titles
    assert book2.title in titles
