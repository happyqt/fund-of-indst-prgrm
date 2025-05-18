"""
Модуль для обработки запросов, связанных с пользователями.
"""
from flask import request, jsonify, g
from app.database import get_db
from app.models.user import User
from app.models.book import Book
from app.auth import login_required, hash_password
from sqlalchemy.exc import SQLAlchemyError


def register_user():
    """
    Регистрация нового пользователя.
    ---
    tags:
      - Users
    summary: Регистрация нового пользователя
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/UserCreateRequest'
    responses:
      201:
        $ref: '#/components/responses/UserRegistered'
      400:
        $ref: '#/components/responses/MissingFieldsError'
      409:
        $ref: '#/components/responses/ConflictError'
      500:
        $ref: '#/components/responses/InternalServerError'
    """
    data = request.get_json()

    if not data or not all(k in data for k in ('username', 'email', 'password')):
        return jsonify({"error": "Missing required fields (username, email, password)"}), 400

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    hashed_password = hash_password(password)

    db_generator = get_db()
    db = next(db_generator)

    try:
        # Проверка на уникальность username и email
        existing_user = db.query(User).filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            return jsonify({"error": "Username or email already exists"}), 409

        new_user = User(username=username, email=email, hashed_password=hashed_password,
                        is_admin=False)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)  # Обновляем объект, чтобы получить id

        return jsonify({"message": "User registered successfully", "user_id": new_user.id}), 201
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({"error": "Database error", "message": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500
    finally:
        db_generator.close()


@login_required
def get_current_user_info():
    """
    Получить информацию о текущем аутентифицированном пользователе.
    ---
    tags:
      - Users
    summary: Получить информацию о текущем аутентифицированном пользователе
    description: Требуется Basic авторизация.
    security:
      - basicAuth: []
    responses:
      200:
        $ref: '#/components/responses/CurrentUserResponse'
      401:
        $ref: '#/components/responses/UnauthorizedError'
      500:
        $ref: '#/components/responses/InternalServerError'
    """
    user = g.current_user  # login_required уже поместил пользователя в g.current_user
    user_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_admin": user.is_admin
    }
    return jsonify(user_data), 200


@login_required
def get_my_books():
    """
    Получить список книг текущего аутентифицированного пользователя.
    ---
    tags:
      - Users
    summary: Получить список книг текущего пользователя
    description: Требуется Basic авторизация. Возвращает все книги, принадлежащие пользователю.
    security:
      - basicAuth: []
    responses:
      200:
        description: Список книг пользователя.
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/BookListResponse' # Используем ту же схему, что и для общего списка книг
      401:
        $ref: '#/components/responses/UnauthorizedError'
      500:
        $ref: '#/components/responses/InternalServerError'
    """
    db_generator = get_db()
    db = next(db_generator)
    try:
        user_id = g.current_user.id
        books = db.query(Book).filter(Book.owner_id == user_id).order_by(Book.id).all()
        books_list = []
        for book in books:
            books_list.append({
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "description": book.description,
                "owner_id": book.owner_id,
                "is_available": book.is_available
            })
        return jsonify(books_list), 200
    except SQLAlchemyError as e:
        return jsonify({"error": "Database error", "message": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500
    finally:
        db_generator.close()
