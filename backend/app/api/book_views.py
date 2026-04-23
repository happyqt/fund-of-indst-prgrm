"""
Модуль для обработки запросов, связанных с книгами.
"""
from flask import jsonify, request, g
from app.database import get_db
from app.models.book import Book
from app.models.user import User
from app.models.exchange import Exchange
from app.auth import login_required
from sqlalchemy import or_, func
from sqlalchemy.exc import SQLAlchemyError


def list_books():
    """
    Получить список доступных книг.
    Позволяет фильтровать по названию (title) и автору (author) по частичному совпадению без регистра.
    Поддерживает пагинацию через параметры page и per_page.
    ---
    tags:
      - Books
    summary: Получить список доступных книг с возможностью фильтрации и пагинации
    parameters:
      - name: title
        in: query
        required: false
        description: Часть названия книги для поиска
        schema:
          type: string
      - name: author
        in: query
        required: false
        description: Часть имени автора для поиска
        schema:
          type: string
      - name: page
        in: query
        required: false
        description: Номер страницы (начиная с 1)
        schema:
          type: integer
          default: 1
      - name: per_page
        in: query
        required: false
        description: Количество книг на странице (от 1 до 100)
        schema:
          type: integer
          default: 20
    responses:
      200:
        description: Список доступных книг с метаданными пагинации.
        content:
          application/json:
            schema:
              type: object
              properties:
                books:
                  $ref: '#/components/schemas/BookListResponse'
                total:
                  type: integer
                  description: Общее количество книг, соответствующих фильтру
                page:
                  type: integer
                per_page:
                  type: integer
                total_pages:
                  type: integer
      500:
        $ref: '#/components/responses/InternalServerError'
    """
    db_generator = get_db()
    db = next(db_generator)
    try:
        query = db.query(Book, User.username).join(User, Book.owner_id == User.id).filter(
            Book.is_available.is_(True)
        )

        title_filter = request.args.get('title')
        author_filter = request.args.get('author')

        if title_filter:
            query = query.filter(func.lower(Book.title).contains(func.lower(title_filter)))

        if author_filter:
            query = query.filter(func.lower(Book.author).contains(func.lower(author_filter)))

        # Пагинация
        try:
            page = max(1, int(request.args.get('page', 1)))
            per_page = min(100, max(1, int(request.args.get('per_page', 20))))
        except (ValueError, TypeError):
            page = 1
            per_page = 20

        total = query.count()
        total_pages = (total + per_page - 1) // per_page
        rows = query.offset((page - 1) * per_page).limit(per_page).all()

        books_list = []
        for book, owner_username in rows:
            books_list.append({
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "description": book.description,
                "owner_id": book.owner_id,
                "owner_username": owner_username,
                "is_available": book.is_available
            })
        return jsonify({
            "books": books_list,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }), 200
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({"error": "Database error", "message": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500
    finally:
        db_generator.close()


def get_book(book_id):
    """
    Получить информацию о конкретной книге.
    ---
    tags:
      - Books
    summary: Получить информацию о конкретной книге
    parameters:
      - name: book_id
        in: path
        required: true
        description: ID книги для получения информации
        schema:
          type: integer
    responses:
      200:
        description: Информация о книге.
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Book'
      404:
        $ref: '#/components/responses/NotFound'
      500:
        $ref: '#/components/responses/InternalServerError'
    """
    db_generator = get_db()
    db = next(db_generator)
    try:
        row = db.query(Book, User.username).join(User, Book.owner_id == User.id).filter(
            Book.id == book_id
        ).first()
        if row is None:
            return jsonify({"message": "Book not found"}), 404
        book, owner_username = row
        book_data = {
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "description": book.description,
            "owner_id": book.owner_id,
            "owner_username": owner_username,
            "is_available": book.is_available
        }
        return jsonify(book_data), 200
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({"error": "Database error", "message": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500
    finally:
        db_generator.close()


@login_required
def update_book(book_id):
    """
    Обновить информацию о своей книге.
    Только владелец может обновить информацию о своей книге.
    ---
    tags:
      - Books
    summary: Обновить информацию о своей книге
    security:
      - basicAuth: []
    parameters:
      - name: book_id
        in: path
        required: true
        description: ID книги для обновления
        schema:
          type: integer
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              title:
                type: string
                description: Новое название книги
              author:
                type: string
                description: Новый автор книги
              description:
                type: string
                description: Новое описание книги
                nullable: True
              is_available:
                type: boolean
                description: Новый флаг доступности книги для обмена
            minProperties: 1 # Хотя бы одно поле должно быть для обновления
    responses:
      200:
        description: Книга успешно обновлена.
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Book'
      400:
        description: Некорректные данные в запросе (например, нет данных для обновления).
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MessageResponse'
      401:
        $ref: '#/components/responses/UnauthorizedError'
      403:
        description: Доступ запрещен (пользователь не является владельцем книги).
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MessageResponse'
      404:
        $ref: '#/components/responses/NotFound'
      500:
        $ref: '#/components/responses/InternalServerError'
    """
    db_generator = get_db()
    db = next(db_generator)
    try:
        book = db.query(Book).filter(Book.id == book_id).first()

        if book is None:
            return jsonify({"message": "Book not found"}), 404

        if book.owner_id != g.current_user.id:
            return jsonify({"message": "You are not authorized to update this book"}), 403

        data = request.get_json()
        if not data:
            return jsonify({"message": "No data provided for update"}), 400

        updated_fields = False
        if 'title' in data and data['title'] is not None:
            book.title = data['title']
            updated_fields = True
        if 'author' in data and data['author'] is not None:
            book.author = data['author']
            updated_fields = True
        if 'description' in data:
            book.description = data['description']
            updated_fields = True
        if 'is_available' in data and isinstance(data['is_available'], bool):
            book.is_available = data['is_available']
            updated_fields = True

        if not updated_fields:
            return jsonify({"message": "No valid fields provided for update"}), 400

        db.add(book)
        db.commit()
        db.refresh(book)

        book_data = {
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "description": book.description,
            "owner_id": book.owner_id,
            "is_available": book.is_available
        }
        return jsonify(book_data), 200

    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({"error": "Database error", "message": str(e)}), 500
    except Exception as e:
        db.rollback()
        return jsonify({"error": "Internal server error", "message": str(e)}), 500
    finally:
        db_generator.close()


@login_required
def delete_book(book_id):
    """
    Удалить свою книгу.
    Только владелец может удалить свою книгу.
    Книга НЕ МОЖЕТ быть удалена, если она когда-либо участвовала в каком-либо обмене
    (в качестве предложенной или запрошенной, независимо от статуса обмена),
    чтобы сохранить целостность истории обменов.
    Вместо этого пользователь может пометить книгу как недоступную (is_available = False).
    ---
    tags:
      - Books
    summary: Удалить свою книгу (только если она не связана с историей обменов)
    security:
      - basicAuth: []
    parameters:
      - name: book_id
        in: path
        required: true
        description: ID книги для удаления
        schema:
          type: integer
    responses:
      200:
        description: Книга успешно удалена.
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MessageResponse'
      401:
        $ref: '#/components/responses/UnauthorizedError'
      403:
        description: Доступ запрещен (пользователь не является владельцем книги).
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MessageResponse'
      404:
        $ref: '#/components/responses/NotFound'
      409:
        description: >
          Книга не может быть удалена, так как она является частью истории обменов.
          Пожалуйста, пометьте ее как недоступную, если вы больше не хотите ее предлагать.
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MessageResponse'
      500:
        $ref: '#/components/responses/InternalServerError'
    """
    db_generator = get_db()
    db = next(db_generator)
    try:
        book = db.query(Book).filter(Book.id == book_id).first()

        if book is None:
            return jsonify({"message": "Book not found"}), 404

        if book.owner_id != g.current_user.id:
            return jsonify({"message": "You are not authorized to delete this book"}), 403

        # Проверка, участвует ли книга в каких-либо обменах (в любой роли, в любом статусе)
        involved_in_exchange = db.query(Exchange).filter(
            or_(
                Exchange.proposed_book_id == book_id,
                Exchange.requested_book_id == book_id
            )
        ).first()  # Достаточно найти хотя бы одну запись

        if involved_in_exchange:
            return jsonify({
                "message": "Cannot delete this book as it is part of exchange history. "
                           "Consider marking it as unavailable (is_available = false) instead."
            }), 409  # Conflict

        # Если книга не участвовала в обменах, удаляем ее
        db.delete(book)
        db.commit()

        return jsonify({"message": "Book successfully deleted"}), 200

    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({"error": "Database error", "message": str(e)}), 500
    except Exception as e:  # Generic exception handler
        db.rollback()
        return jsonify({"error": "An unexpected error occurred", "message": str(e)}), 500
    finally:
        db_generator.close()
