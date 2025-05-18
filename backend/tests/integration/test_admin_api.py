"""Интеграционные тесты для API административных функций."""
# pylint: disable=redefined-outer-name, unused-argument
import pytest
from app.models.user import User
from app.models.book import Book
from app.models.exchange import Exchange
from tests.integration.conftest import basic_auth_headers


@pytest.fixture(scope="function")
def admin_user(db_session, create_user):
    """Фикстура для создания администратора."""
    user = create_user(username="adminuser", password="adminpassword", email="admin@example.com", is_admin=True)
    return user


@pytest.fixture(scope="function")
def admin_auth_headers(admin_user):
    """Заголовки авторизации для администратора."""
    return basic_auth_headers(admin_user.username, "adminpassword")


@pytest.fixture(scope="function")
def regular_user(db_session, create_user):
    """Фикстура для создания обычного пользователя."""
    user = create_user(username="regularuser", password="regularpassword", email="regular@example.com", is_admin=False)
    return user


@pytest.fixture(scope="function")
def regular_user_auth_headers(regular_user):
    """Заголовки авторизации для обычного пользователя."""
    return basic_auth_headers(regular_user.username, "regularpassword")


def test_get_exchange_stats_as_admin(client, db_session, admin_auth_headers, create_user, create_book):
    """Проверка получения статистики обменов администратором."""
    user1 = create_user("user_stats1", "pw", "stats1@x.com")
    user2 = create_user("user_stats2", "pw", "stats2@x.com")
    book1_u1 = create_book("Book S1U1", "AU1", user1.id)
    book1_u2 = create_book("Book S1U2", "AU2", user2.id)
    book2_u1 = create_book("Book S2U1", "AU1", user1.id)
    book2_u2 = create_book("Book S2U2", "AU2", user2.id)

    db_session.add_all([
        Exchange(proposing_user_id=user1.id, receiving_user_id=user2.id, proposed_book_id=book1_u1.id,
                 requested_book_id=book1_u2.id, status='pending'),
        Exchange(proposing_user_id=user2.id, receiving_user_id=user1.id, proposed_book_id=book2_u2.id,
                 requested_book_id=book2_u1.id, status='accepted'),
        Exchange(proposing_user_id=user1.id, receiving_user_id=user2.id, proposed_book_id=book2_u1.id,
                 requested_book_id=book2_u2.id, status='accepted'),
        Exchange(proposing_user_id=user2.id, receiving_user_id=user1.id, proposed_book_id=book1_u2.id,
                 requested_book_id=book1_u1.id, status='rejected'),
    ])
    db_session.commit()

    response = client.get('/api/admin/exchanges/stats', headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['total_exchanges'] == 4
    assert data['pending_count'] == 1
    assert data['accepted_count'] == 2
    assert data['rejected_count'] == 1
    assert data['cancelled_count'] == 0


def test_get_exchange_stats_empty(client, db_session, admin_auth_headers):
    """Проверка получения статистики при отсутствии обменов."""
    response = client.get('/api/admin/exchanges/stats', headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['total_exchanges'] == 0
    assert data['pending_count'] == 0


def test_get_exchange_stats_as_regular_user(client, regular_user_auth_headers):
    """Обычный пользователь не должен иметь доступ к статистике."""
    response = client.get('/api/admin/exchanges/stats', headers=regular_user_auth_headers)
    assert response.status_code == 403


def test_get_exchange_stats_unauthenticated(client):
    """Неаутентифицированный пользователь не должен иметь доступ к статистике."""
    response = client.get('/api/admin/exchanges/stats')
    assert response.status_code == 401


def test_list_all_books_admin_success(client, db_session, admin_auth_headers, create_user, create_book):
    """Администратор получает список всех книг, включая недоступные."""
    owner = create_user("book_owner_admin", "pw", "boa@x.com")
    book1 = create_book("Available Book Admin", "Author", owner.id, is_available=True)
    book2 = create_book("Unavailable Book Admin", "Author", owner.id, is_available=False)

    response = client.get('/api/admin/books', headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    titles_in_response = {b['title'] for b in data}
    assert book1.title in titles_in_response
    assert book2.title in titles_in_response

    availability_map = {b['title']: b['is_available'] for b in data}
    assert availability_map[book1.title] is True
    assert availability_map[book2.title] is False


def test_list_all_books_admin_as_regular_user(client, regular_user_auth_headers, db_session, create_user, create_book):
    """Обычный пользователь не должен иметь доступ к /api/admin/books."""
    owner = create_user("book_owner_admin2", "pw", "boa2@x.com")
    create_book("Some Book", "Some Author", owner.id)
    response = client.get('/api/admin/books', headers=regular_user_auth_headers)
    assert response.status_code == 403


def test_list_all_books_admin_unauthenticated(client, db_session, create_user, create_book):
    """Неаутентифицированный пользователь не должен иметь доступ к /api/admin/books."""
    owner = create_user("book_owner_admin3", "pw", "boa3@x.com")
    create_book("Another Book", "Another Author", owner.id)
    response = client.get('/api/admin/books')
    assert response.status_code == 401


def test_list_all_users_admin_success(client, db_session, admin_user, admin_auth_headers, regular_user):
    """Администратор получает список всех пользователей."""
    response = client.get('/api/admin/users', headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.get_json()

    assert len(data) >= 2

    usernames_in_response = {u['username'] for u in data}
    assert admin_user.username in usernames_in_response
    assert regular_user.username in usernames_in_response

    for user_data in data:
        assert 'hashed_password' not in user_data
        if user_data['username'] == admin_user.username:
            assert user_data['is_admin'] is True
        if user_data['username'] == regular_user.username:
            assert user_data['is_admin'] is False


def test_list_all_users_admin_as_regular_user(client, regular_user_auth_headers):
    """Обычный пользователь не должен иметь доступ к /api/admin/users."""
    response = client.get('/api/admin/users', headers=regular_user_auth_headers)
    assert response.status_code == 403


def test_list_all_users_admin_unauthenticated(client):
    """Неаутентифицированный пользователь не должен иметь доступ к /api/admin/users."""
    response = client.get('/api/admin/users')
    assert response.status_code == 401
