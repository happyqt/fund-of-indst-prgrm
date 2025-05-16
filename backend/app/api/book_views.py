from flask import request, jsonify
from app.database import get_db
from app.models.book import Book
from app.models.user import User
from sqlalchemy.exc import SQLAlchemyError
from app.auth import login_required


def list_books():
    """
    Получить список доступных книг.
    ---
    tags:
      - Books
    summary: Получить список доступных книг
    responses:
      200:
        description: Список доступных книг.
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/BookListResponse'
      500:
        $ref: '#/components/responses/InternalServerError'
    """
    db_generator = get_db()
    db = next(db_generator)
    try:
        books = db.query(Book).filter(Book.is_available == True).all()
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
        book = db.query(Book).filter(Book.id == book_id).first()
        if book is None:
            return jsonify({"message": "Book not found"}), 404
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
        return jsonify({"error": "Internal server error", "message": str(e)}), 500
    finally:
        db_generator.close()
