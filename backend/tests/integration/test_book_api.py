import pytest
from app import create_app
from app.database import engine, Base, SessionLocal
from app.models.user import User  # Нужен для создания владельца книги
from app.models.book import Book  # Нужен для проверки данных в БД



@pytest.fixture(scope="session")
def app():
    """Фикстура, предоставляющая экземпляр Flask приложения."""
    # Создаем экземпляр приложения
    flask_app = create_app()

    yield flask_app


@pytest.fixture(scope="function")
def client(app):
    """Фикстура, предоставляющая тестовый клиент Flask."""
    with app.test_client() as client:
        yield client


@pytest.fixture(scope="function")
def setup_teardown_db_per_test():
    """
    Фикстура для создания/удаления таблиц БД для каждого тестового сценария.
    Также предоставляет сессию для добавления начальных данных теста.
    """
    print("\nНастройка БД для теста: Создание таблиц...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Таблицы созданы.")

    # Предоставляем сессию для добавления данных перед выполнением теста
    session = SessionLocal()
    try:
        yield session
    finally:
        # Закрываем сессию после выполнения теста
        session.close()
        print("Очистка БД после теста: Удаление таблиц...")
        Base.metadata.drop_all(bind=engine)
        print("Таблицы удалены.")


def test_get_books_empty(client, setup_teardown_db_per_test):
    """Проверка GET /api/books когда нет книг."""
    response = client.get('/api/books')  # Делаем GET запрос через тестовый клиент

    # Проверяем статус код ответа
    assert response.status_code == 200
    # Проверяем, что тело ответа - пустой JSON массив
    assert response.get_json() == []


def test_add_book(client, setup_teardown_db_per_test):
    """Проверка POST /api/books на успешное добавление книги."""
    db_session = setup_teardown_db_per_test
    test_user = User(username="testuser_add", email="add@example.com", hashed_password="aboba1337")
    db_session.add(test_user)
    db_session.commit()  # Сохраняем пользователя, чтобы получить его ID
    db_session.refresh(test_user)  # Обновляем объект пользователя, чтобы получить ID

    # Данные для новой книги в формате JSON
    book_data = {
        "title": "Новая Тестовая Книга",
        "author": "Тестовый Автор",
        "owner_id": test_user.id,
        "description": "Эта книга добавлена тестом."
    }

    response = client.post('/api/books', json=book_data)

    # Проверяем статус код
    assert response.status_code == 201
    # Проверяем тело ответа
    response_json = response.get_json()
    assert "id" in response_json  # Успешное добавление должно вернуть ID
    assert response_json["title"] == book_data["title"]
    assert response_json["author"] == book_data["author"]
    assert response_json.get("description") == book_data["description"]  # description может быть None если не передан

    # Проверяем, что книга действительно добавилась в БД
    added_book = db_session.query(Book).filter_by(id=response_json["id"]).first()
    assert added_book is not None
    assert added_book.title == book_data["title"]
    assert added_book.owner_id == test_user.id
    assert added_book.is_available is True


def test_add_book_missing_fields(client, setup_teardown_db_per_test):
    """Проверка POST /api/books с отсутствующими обязательными полями."""
    # Отсутствует 'author'
    book_data_missing_author = {
        "title": "Книга без автора",
        "owner_id": 1  # owner_id может быть любым, ошибка будет раньше
    }
    response = client.post('/api/books', json=book_data_missing_author)
    assert response.status_code == 400  # Ожидаем 400 Bad Request
    assert "Missing required fields" in response.get_json().get("error", "")

    # Отсутствует 'title'
    book_data_missing_title = {
        "author": "Автор",
        "owner_id": 1
    }
    response = client.post('/api/books', json=book_data_missing_title)
    assert response.status_code == 400
    assert "Missing required fields" in response.get_json().get("error", "")

    # Отсутствует 'owner_id'
    book_data_missing_owner = {
        "title": "Книга без владельца",
        "author": "Автор"
    }
    response = client.post('/api/books', json=book_data_missing_owner)
    assert response.status_code == 400
    assert "Missing required fields" in response.get_json().get("error", "")


def test_add_book_non_existent_owner(client, setup_teardown_db_per_test):
    """Проверка POST /api/books с несуществующим owner_id."""
    # DB пуста, пользователь с ID 999 не существует
    book_data = {
        "title": "Книга с неверным владельцем",
        "author": "Автор",
        "owner_id": 999  # Указываем ID пользователя, которого нет
    }
    response = client.post('/api/books', json=book_data)
    assert response.status_code == 404  # Ожидаем 404 Not Found
    assert "Owner with id 999 not found" in response.get_json().get("error", "")


def test_get_book_existing(client, setup_teardown_db_per_test):
    """Проверка GET /api/books/{book_id} для существующей книги."""
    # Добавляем тестового пользователя и книгу через сессию фикстуры
    db_session = setup_teardown_db_per_test
    test_user = User(username="user_get", email="getbook@example.com", hashed_password="hashedpassword")
    db_session.add(test_user)
    db_session.commit()
    db_session.refresh(test_user)

    test_book = Book(title="Существующая Книга", author="Существующий Автор", owner_id=test_user.id,
                     description="Описание.")
    db_session.add(test_book)
    db_session.commit()  # Сохраняем книгу, чтобы получить ее ID
    db_session.refresh(test_book)  # Обновляем объект книги, чтобы получить ID

    # Делаем GET запрос по ID созданной книги
    response = client.get(f'/api/books/{test_book.id}')

    assert response.status_code == 200  # Ожидаем 200 OK
    response_json = response.get_json()
    assert response_json["id"] == test_book.id
    assert response_json["title"] == "Существующая Книга"
    assert response_json["author"] == "Существующий Автор"
    assert response_json.get("description") == "Описание."
    assert response_json["owner_id"] == test_user.id
    assert response_json["is_available"] is True


def test_get_book_not_found(client, setup_teardown_db_per_test):
    """Проверка GET /api/books/{book_id} для несуществующей книги."""
    # DB пуста, книги с ID 999 нет
    response = client.get('/api/books/999')

    assert response.status_code == 404  # Ожидаем 404 Not Found
    assert "Book not found" in response.get_json().get("message", "")
