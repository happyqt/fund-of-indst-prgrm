from flask import request, jsonify, make_response
from flask.views import MethodView
from app.database import get_db
from app.models.book import Book
from app.models.user import User
from sqlalchemy.exc import SQLAlchemyError


class BookAPI(MethodView):
    """
    Book API Resource
    """

    def get(self, book_id=None):
        """
        Получить список книг или информацию о конкретной книге.
        ---
        parameters:
          - in: path
            name: book_id
            schema:
              type: integer
            required: false
            description: ID книги для получения информации
        responses:
          200:
            description: Список доступных книг или информация о книге.
            content:
              application/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/Book' # Ссылка на схему модели книги
          404:
            description: Книга не найдена (только для запроса по ID)
          500:
            description: Ошибка сервера или базы данных
        """
        db_generator = get_db()
        db = next(db_generator)  # Получаем сессию

        try:
            if book_id is None:
                # Обработка GET /api/books (получить список книг)
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
            else:
                # Обработка GET /api/books/<int:book_id> (получить конкретную книгу)
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
            db_generator.close()  # Закрываем сессию

    def post(self):
        """
                Добавить новую книгу.
                ---
                requestBody:
                  required: true
                  content:
                    application/json:
                      schema:
                        $ref: '#/components/schemas/BookCreateRequest'
                responses:
                  201:
                    description: Книга успешно добавлена
                    content:
                      application/json:
                        schema:
                          $ref: '#/components/schemas/Book' # Ссылка на схему модели книги
                  400:
                    description: Отсутствуют обязательные поля
                  404:
                    description: Владелец не найден
                  500:
                    description: Ошибка сервера или базы данных
                """
        db_generator = get_db()
        db = next(db_generator)

        try:
            data = request.get_json()
            if not data or not all(k in data for k in ('title', 'author', 'owner_id')):
                return jsonify({"error": "Missing required fields (title, author, owner_id)"}), 400

            owner = db.query(User).filter(User.id == data['owner_id']).first()
            if owner is None:
                return jsonify({"error": f"Owner with id {data['owner_id']} not found"}), 404

            new_book = Book(
                title=data['title'],
                author=data['author'],
                description=data.get('description'),
                owner_id=data['owner_id'],
                is_available=True
            )
            db.add(new_book)
            db.commit()
            db.refresh(new_book)

            response_data = {
                "id": new_book.id,
                "title": new_book.title,
                "author": new_book.author,
                "description": new_book.description,
                "owner_id": new_book.owner_id,
                "is_available": new_book.is_available
            }
            return jsonify(response_data), 201

        except SQLAlchemyError as e:
            db.rollback()
            return jsonify({"error": "Database error", "message": str(e)}), 500
        except Exception as e:
            return jsonify({"error": "Internal server error", "message": str(e)}), 500
        finally:
            db_generator.close()

