"""Интеграционные тесты для API отзывов."""
# pylint: disable=redefined-outer-name, unused-argument, too-many-arguments
import pytest
from app.models.user import User
from app.models.book import Book
from app.models.review import Review
from tests.integration.conftest import basic_auth_headers  # Используем существующие фикстуры


@pytest.fixture
def user_for_reviews(create_user):
    """Создает пользователя для тестов отзывов."""
    return create_user("reviewer_user", "review_pass", "reviewer@example.com")


@pytest.fixture
def user_for_reviews_headers(user_for_reviews):
    """Заголовки для пользователя-ревьюера."""
    return basic_auth_headers(user_for_reviews.username, "review_pass")


@pytest.fixture
def book_owner_for_reviews(create_user):
    """Создает владельца книги для тестов отзывов."""
    return create_user("book_owner_user", "owner_pass", "owner@example.com")


@pytest.fixture
def book_owner_for_reviews_headers(book_owner_for_reviews):  # Добавим заголовки для владельца
    """Заголовки для владельца книги."""
    return basic_auth_headers(book_owner_for_reviews.username, "owner_pass")


@pytest.fixture
def book_for_reviews(create_book, book_owner_for_reviews):
    """Создает книгу для оставления отзывов (принадлежит book_owner_for_reviews)."""
    return create_book("Book To Be Reviewed", "Author Reviewable", book_owner_for_reviews.id)


def test_create_review_success(client, db_session, book_for_reviews, user_for_reviews_headers, user_for_reviews):
    """Проверка успешного создания отзыва другим пользователем."""
    payload = {"rating": 5, "text": "Отличная книга от другого пользователя!"}
    response = client.post(f'/api/books/{book_for_reviews.id}/reviews', json=payload, headers=user_for_reviews_headers)

    assert response.status_code == 201
    data = response.get_json()
    assert data["rating"] == payload["rating"]
    assert data["text"] == payload["text"]
    assert data["user"]["id"] == user_for_reviews.id
    assert data["user"]["username"] == user_for_reviews.username
    assert db_session.query(Review).filter_by(id=data["id"]).count() == 1


def test_create_review_on_own_book_succeeds(client, db_session, book_for_reviews,
                                            book_owner_for_reviews_headers, book_owner_for_reviews):
    """Проверка, что владелец МОЖЕТ успешно создать отзыв на свою книгу."""
    payload = {"rating": 4, "text": "Это моя книга, и она хороша!"}
    response = client.post(f'/api/books/{book_for_reviews.id}/reviews',
                           json=payload, headers=book_owner_for_reviews_headers)

    assert response.status_code == 201
    data = response.get_json()
    assert data["rating"] == payload["rating"]
    assert data["text"] == payload["text"]
    assert data["user"]["id"] == book_owner_for_reviews.id
    assert db_session.query(Review).filter_by(id=data["id"]).count() == 1


def test_create_review_invalid_rating(client, book_for_reviews, user_for_reviews_headers):
    """Проверка создания отзыва с невалидным рейтингом."""
    payload_too_high = {"rating": 6, "text": "Слишком высокий."}
    response = client.post(f'/api/books/{book_for_reviews.id}/reviews', json=payload_too_high,
                           headers=user_for_reviews_headers)
    assert response.status_code == 400

    payload_too_low = {"rating": 0, "text": "Слишком низкий."}
    response = client.post(f'/api/books/{book_for_reviews.id}/reviews', json=payload_too_low,
                           headers=user_for_reviews_headers)
    assert response.status_code == 400


def test_create_review_twice_forbidden(client, book_for_reviews, user_for_reviews_headers):
    """Проверка запрета на создание второго отзыва на ту же книгу от того же пользователя."""
    payload1 = {"rating": 4, "text": "Первый отзыв."}
    resp1 = client.post(f'/api/books/{book_for_reviews.id}/reviews', json=payload1, headers=user_for_reviews_headers)
    assert resp1.status_code == 201

    payload2 = {"rating": 3, "text": "Второй отзыв, не должен пройти."}
    response = client.post(f'/api/books/{book_for_reviews.id}/reviews', json=payload2, headers=user_for_reviews_headers)
    assert response.status_code == 403
    assert "уже оставили отзыв" in response.get_json()["message"]


def test_create_review_book_not_found(client, user_for_reviews_headers):
    """Проверка создания отзыва для несуществующей книги."""
    payload = {"rating": 5, "text": "Книги нет."}
    response = client.post('/api/books/99999/reviews', json=payload, headers=user_for_reviews_headers)
    assert response.status_code == 404


def test_get_reviews_for_book_success(client, db_session, book_for_reviews, user_for_reviews,
                                      book_owner_for_reviews, create_user):
    """Проверка получения списка отзывов для книги."""
    # Отзыв от другого пользователя
    review1 = Review(book_id=book_for_reviews.id, user_id=user_for_reviews.id, rating=5, text="Супер!")
    # Отзыв от владельца книги
    review2 = Review(book_id=book_for_reviews.id, user_id=book_owner_for_reviews.id, rating=4, text="Моя прелесть.")

    db_session.add_all([review1, review2])
    db_session.commit()

    response = client.get(f'/api/books/{book_for_reviews.id}/reviews')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2

    user_ids_in_response = {item['user']['id'] for item in data}
    texts_in_response = {item['text'] for item in data}

    assert user_for_reviews.id in user_ids_in_response
    assert book_owner_for_reviews.id in user_ids_in_response
    assert "Супер!" in texts_in_response
    assert "Моя прелесть." in texts_in_response


def test_get_reviews_for_book_empty(client, db_session, book_for_reviews):
    """Проверка получения пустого списка отзывов, если их нет."""
    response = client.get(f'/api/books/{book_for_reviews.id}/reviews')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 0


def test_get_reviews_for_book_not_found(client, db_session):
    """Проверка получения отзывов для несуществующей книги."""
    response = client.get('/api/books/99999/reviews')
    assert response.status_code == 404
