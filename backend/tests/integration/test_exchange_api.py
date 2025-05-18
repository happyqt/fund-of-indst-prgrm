"""Интеграционные тесты для API обмена книгами."""
# pylint: disable=redefined-outer-name
import pytest
from app.models.user import User
from app.models.book import Book
from app.models.exchange import Exchange
from app.auth import hash_password
from tests.integration.conftest import basic_auth_headers


@pytest.fixture
def user1_data():
    """Фикстура с данными для первого тестового пользователя."""
    return {"username": "user1", "password": "password1", "email": "user1@example.com"}


@pytest.fixture
def user2_data():
    """Фикстура с данными для второго тестового пользователя."""
    return {"username": "user2", "password": "password2", "email": "user2@example.com"}


@pytest.fixture
def user3_data():
    """Фикстура с данными для третьего тестового пользователя."""
    return {"username": "user3", "password": "password3", "email": "user3@example.com"}


@pytest.fixture
def user1_auth_headers(user1_data):
    """Заголовки авторизации для пользователя 1."""
    return basic_auth_headers(user1_data["username"], user1_data["password"])


@pytest.fixture
def user2_auth_headers(user2_data):
    """Заголовки авторизации для пользователя 2."""
    return basic_auth_headers(user2_data["username"], user2_data["password"])


@pytest.fixture
def user3_auth_headers(user3_data):
    """Заголовки авторизации для пользователя 3."""
    return basic_auth_headers(user3_data["username"], user3_data["password"])


@pytest.fixture
def users_and_books(create_user, user1_data, user2_data, user3_data, create_book):
    """Создает тестовых пользователей и набор книг для них."""
    user1 = create_user(**user1_data)
    user2 = create_user(**user2_data)
    user3 = create_user(**user3_data)

    book1_user1 = create_book("Book1 by User1", "Author1", user1.id)
    book2_user1 = create_book("Book2 by User1", "Author1", user1.id)
    book1_user2 = create_book("Book1 by User2", "Author2", user2.id)
    book2_user2 = create_book("Book2 by User2", "Author2", user2.id)
    book1_user3 = create_book("Book1 by User3", "Author3", user3.id)

    return {
        'user1': user1,
        'user2': user2,
        'user3': user3,
        'book1_user1': book1_user1,
        'book2_user1': book2_user1,
        'book1_user2': book1_user2,
        'book2_user2': book2_user2,
        'book1_user3': book1_user3,
    }


@pytest.fixture
# pylint: disable=unused-argument
def pending_exchange_u1_to_u2(client, db_session, users_and_books, user1_auth_headers):
    """Создает запрос обмена от user1 к user2"""
    book1_user1 = users_and_books['book1_user1']
    book1_user2 = users_and_books['book1_user2']
    payload = {
        "proposed_book_id": book1_user1.id,
        "requested_book_id": book1_user2.id,
        "exchange_location": "Central Library" # центральная, ну вы поняли да, смешно
    }
    response = client.post('/api/exchanges', json=payload, headers=user1_auth_headers)

    response_json = response.get_json()
    assert response.status_code == 201, f"Failed to create pending exchange. Response: {response_json}"
    return response_json


def test_propose_exchange_success(client, db_session, users_and_books, user1_auth_headers):
    """Проверка успешного создания предложения обмена."""
    book1_user1 = users_and_books['book1_user1']
    book1_user2 = users_and_books['book1_user2']
    user1 = users_and_books['user1']
    user2 = users_and_books['user2']

    test_location = "Туалет на пятом этаже"
    payload = {
        "proposed_book_id": book1_user1.id,
        "requested_book_id": book1_user2.id,
        "exchange_location": test_location
    }
    response = client.post('/api/exchanges', json=payload, headers=user1_auth_headers)

    assert response.status_code == 201
    data = response.get_json()
    assert data["proposing_user_id"] == user1.id
    assert data["receiving_user_id"] == user2.id
    assert data["status"] == "pending"

    assert "exchange_location" in data
    assert data["exchange_location"] == test_location

    exchange_in_db = db_session.get(Exchange, data["id"])

    assert exchange_in_db is not None
    assert exchange_in_db.exchange_location == test_location


# pylint: disable=unused-argument
def test_propose_exchange_invalid_scenarios(client, db_session, users_and_books, user1_auth_headers):
    """Проверка различных невалидных сценариев при предложении обмена."""
    user1 = users_and_books['user1']
    book1_user1 = users_and_books['book1_user1']
    book2_user1 = users_and_books['book2_user1']
    book1_user2 = users_and_books['book1_user2']
    # Попытка обменять свою книгу на свою же другую книгу
    payload_own_for_own = {"proposed_book_id": book1_user1.id, "requested_book_id": book2_user1.id}
    response = client.post('/api/exchanges', json=payload_own_for_own, headers=user1_auth_headers)
    assert response.status_code == 400

    # Попытка предложить книгу, которой не владеешь
    payload_not_owned = {"proposed_book_id": book1_user2.id, "requested_book_id": book1_user1.id}
    response = client.post('/api/exchanges', json=payload_not_owned, headers=user1_auth_headers)
    assert response.status_code == 403

    # Попытка предложить недоступную книгу
    book1_user1.is_available = False
    db_session.add(book1_user1)
    db_session.commit()
    payload_unavailable = {"proposed_book_id": book1_user1.id, "requested_book_id": book1_user2.id}
    response = client.post('/api/exchanges', json=payload_unavailable, headers=user1_auth_headers)
    assert response.status_code == 404
    book1_user1.is_available = True  # Восстанавливаем для других тестов
    db_session.add(book1_user1)
    db_session.commit()

    # Попытка предложить несуществующую книгу
    payload_non_existent = {"proposed_book_id": 999, "requested_book_id": book1_user2.id}
    response = client.post('/api/exchanges', json=payload_non_existent, headers=user1_auth_headers)
    assert response.status_code == 404


# pylint: disable=unused-argument
def test_propose_exchange_duplicate_pending(client, users_and_books, user1_auth_headers,
                                            pending_exchange_u1_to_u2):
    """Проверка ошибки при создании дублирующего активного предложения обмена."""
    # pending_exchange_user1_to_user2 уже создал первое предложение
    book1_user1 = users_and_books['book1_user1']
    book1_user2 = users_and_books['book1_user2']
    payload = {"proposed_book_id": book1_user1.id, "requested_book_id": book1_user2.id}
    response = client.post('/api/exchanges', json=payload, headers=user1_auth_headers)
    assert response.status_code == 409


def test_list_user_exchanges_filtered(client, db_session, users_and_books,
                                      user1_auth_headers, user2_auth_headers):
    """Проверка получения списка обменов с фильтрацией (sent, received, all)."""
    user1 = users_and_books['user1']
    book1_user1 = users_and_books['book1_user1']
    book2_user1 = users_and_books['book2_user1']
    book1_user2 = users_and_books['book1_user2']
    # User1 -> User2
    client.post('/api/exchanges', json={"proposed_book_id": book1_user1.id, "requested_book_id": book1_user2.id},
                headers=user1_auth_headers)
    # User2 -> User1
    client.post('/api/exchanges', json={"proposed_book_id": book1_user2.id, "requested_book_id": book2_user1.id},
                headers=user2_auth_headers)

    # Все для user1
    response_all = client.get('/api/exchanges?type=all', headers=user1_auth_headers)
    assert response_all.status_code == 200
    assert len(response_all.get_json()) == 2

    # Отправленные user1
    response_sent = client.get('/api/exchanges?type=sent', headers=user1_auth_headers)
    assert response_sent.status_code == 200
    exchanges_sent = response_sent.get_json()
    assert len(exchanges_sent) == 1
    assert exchanges_sent[0]["proposing_user_id"] == user1.id

    # Полученные user1
    response_received = client.get('/api/exchanges?type=received', headers=user1_auth_headers)
    assert response_received.status_code == 200
    exchanges_received = response_received.get_json()
    assert len(exchanges_received) == 1
    assert exchanges_received[0]["receiving_user_id"] == user1.id


def test_accept_exchange_success_and_book_state_change(client, db_session, users_and_books,
                                                       user2_auth_headers, pending_exchange_u1_to_u2):
    """Проверка успешного принятия обмена и изменения состояния книг."""
    user1 = users_and_books['user1']
    user2 = users_and_books['user2']
    book1_user1 = users_and_books['book1_user1']
    book1_user2 = users_and_books['book1_user2']
    exchange_id = pending_exchange_u1_to_u2["id"]

    response = client.post(f'/api/exchanges/{exchange_id}/accept', headers=user2_auth_headers)
    assert response.status_code == 200
    assert response.get_json()["status"] == "accepted"

    db_session.refresh(book1_user1)
    db_session.refresh(book1_user2)
    assert book1_user1.owner_id == user2.id and not book1_user1.is_available
    assert book1_user2.owner_id == user1.id and not book1_user2.is_available
    exchange_in_db = db_session.get(Exchange, exchange_id)
    assert exchange_in_db is not None
    assert exchange_in_db.status == "accepted"


# pylint: disable=unused-argument
def test_accept_exchange_negative_cases(client, db_session, user1_auth_headers, user2_auth_headers,
                                        pending_exchange_u1_to_u2, users_and_books):
    """Проверка негативных сценариев при принятии обмена."""
    exchange_id = pending_exchange_u1_to_u2["id"]

    # Попытка принять не своим пользователем (proposer)
    response_not_receiver = client.post(f'/api/exchanges/{exchange_id}/accept', headers=user1_auth_headers)
    assert response_not_receiver.status_code == 403

    # Попытка принять уже принятый обмен
    client.post(f'/api/exchanges/{exchange_id}/accept', headers=user2_auth_headers)
    response_already_accepted = client.post(f'/api/exchanges/{exchange_id}/accept', headers=user2_auth_headers)
    assert response_already_accepted.status_code == 403


# pylint: disable=unused-argument
def test_accept_exchange_when_book_unavailable(client, db_session, user2_auth_headers,
                                               pending_exchange_u1_to_u2, users_and_books):
    """Проверка принятия обмена, если одна из книг стала недоступна."""
    book1_user1 = users_and_books['book1_user1']
    exchange_id = pending_exchange_u1_to_u2["id"]
    book1_user1.is_available = False
    db_session.add(book1_user1)
    db_session.commit()

    response = client.post(f'/api/exchanges/{exchange_id}/accept', headers=user2_auth_headers)
    assert response.status_code == 409

    exchange_in_db = db_session.get(Exchange, exchange_id)
    assert exchange_in_db is not None
    assert exchange_in_db.status == "rejected"


# pylint: disable=unused-argument
def test_reject_exchange_success(client, db_session, user2_auth_headers, pending_exchange_u1_to_u2):
    """Проверка успешного отклонения обмена."""
    exchange_id = pending_exchange_u1_to_u2["id"]
    response = client.post(f'/api/exchanges/{exchange_id}/reject', headers=user2_auth_headers)
    assert response.status_code == 200
    assert response.get_json()["status"] == "rejected"

    exchange_in_db = db_session.get(Exchange, exchange_id)
    assert exchange_in_db is not None
    assert exchange_in_db.status == "rejected"


# pylint: disable=unused-argument
def test_reject_exchange_not_receiver(client, user1_auth_headers, pending_exchange_u1_to_u2):
    """Проверка ошибки при попытке отклонить обмен не получателем."""
    exchange_id = pending_exchange_u1_to_u2["id"]
    response = client.post(f'/api/exchanges/{exchange_id}/reject', headers=user1_auth_headers)
    assert response.status_code == 403


# pylint: disable=unused-argument
def test_cancel_exchange_success(client, db_session, user1_auth_headers, pending_exchange_u1_to_u2):
    """Проверка успешной отмены своего предложения обмена."""
    exchange_id = pending_exchange_u1_to_u2["id"]
    response = client.post(f'/api/exchanges/{exchange_id}/cancel', headers=user1_auth_headers)
    assert response.status_code == 200
    assert response.get_json()["status"] == "cancelled"

    exchange_in_db = db_session.get(Exchange, exchange_id)
    assert exchange_in_db is not None
    assert exchange_in_db.status == "cancelled"


# pylint: disable=unused-argument
def test_cancel_exchange_not_proposer(client, user2_auth_headers, pending_exchange_u1_to_u2):
    """Проверка ошибки при попытке отменить чужое предложение обмена."""
    exchange_id = pending_exchange_u1_to_u2["id"]
    response = client.post(f'/api/exchanges/{exchange_id}/cancel', headers=user2_auth_headers)
    assert response.status_code == 403


# pylint: disable=unused-argument
def test_accept_exchange_rejects_conflicting(client, db_session, users_and_books,
                                             user1_auth_headers, user2_auth_headers, user3_auth_headers):
    """Проверка, что принятие одного обмена отклоняет конфликтующие предложения."""
    book1_user1 = users_and_books['book1_user1']  # Книга user1
    book1_user2 = users_and_books['book1_user2']  # Книга user2
    book1_user3 = users_and_books['book1_user3']  # Книга user3
    # User1 предлагает book1_user1 за book1_user2 (user2)
    resp1 = client.post('/api/exchanges',
                        json={"proposed_book_id": book1_user1.id, "requested_book_id": book1_user2.id},
                        headers=user1_auth_headers)
    proposal1_id = resp1.get_json()["id"]

    # User3 предлагает book1_user3 за book1_user2 (книга user2, участвует в proposal1)
    resp2 = client.post('/api/exchanges',
                        json={"proposed_book_id": book1_user3.id, "requested_book_id": book1_user2.id},
                        headers=user3_auth_headers)
    proposal2_id = resp2.get_json()["id"]

    # User3 предлагает book1_user3 за book1_user1 (книга user1, участвует в proposal1)
    resp3 = client.post('/api/exchanges',
                        json={"proposed_book_id": book1_user3.id, "requested_book_id": book1_user1.id},
                        headers=user3_auth_headers)
    proposal3_id = resp3.get_json()["id"]

    # User2 принимает предложение от User1 (proposal1)
    accept_response = client.post(f'/api/exchanges/{proposal1_id}/accept', headers=user2_auth_headers)
    assert accept_response.status_code == 200

    proposal1_db = db_session.get(Exchange, proposal1_id)
    proposal2_db = db_session.get(Exchange, proposal2_id)
    proposal3_db = db_session.get(Exchange, proposal3_id)

    assert proposal1_db is not None and proposal1_db.status == "accepted"
    assert proposal2_db is not None and proposal2_db.status == "rejected"
    assert proposal3_db is not None and proposal3_db.status == "rejected"
