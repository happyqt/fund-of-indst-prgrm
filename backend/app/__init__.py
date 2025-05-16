import os
import yaml
from flask import Flask, jsonify, request, g
from app.database import init_db, get_db
from app.models.book import Book
from app.models.user import User
from app.api.book_views import list_books, get_book
from app.api.user_views import register_user, get_current_user_info
from app.auth import login_required, admin_required
from flasgger import Swagger
from sqlalchemy.exc import SQLAlchemyError


def create_app():
    app = Flask(__name__)
    app.config['SWAGGER'] = {
        'title': 'OA3 Callbacks',
        'openapi': '3.0.2'
    }
    swagger_template = {
        "openapi": "3.0.2",
        "info": {
            "title": "Book Exchange API",
            "description": "API для сервиса обмена книгами",
            "version": "1.0.1"
        },
        "paths": {},
        "components": {
            "schemas": {
                "Book": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "integer",
                            "description": "Уникальный идентификатор книги",
                            "readOnly": True
                        },
                        "title": {
                            "type": "string",
                            "description": "Название книги"
                        },
                        "author": {
                            "type": "string",
                            "description": "Автор книги"
                        },
                        "description": {
                            "type": "string",
                            "description": "Описание книги",
                            "nullable": True
                        },
                        "owner_id": {
                            "type": "integer",
                            "description": "ID пользователя-владельца книги"
                        },
                        "is_available": {
                            "type": "boolean",
                            "description": "Флаг доступности книги для обмена",
                            "default": True
                        }
                    },
                    "required": [
                        "title",
                        "author",
                        "owner_id"
                    ]
                },
                "BookCreateRequest": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Название книги"
                        },
                        "author": {
                            "type": "string",
                            "description": "Автор книги"
                        },
                        "description": {
                            "type": "string",
                            "description": "Описание книги",
                            "nullable": True
                        }
                    },
                    "required": ["title", "author"]
                },
                "BookListResponse": {
                    "type": "array",
                    "items": {
                        "$ref": "#/components/schemas/Book"
                    }
                },
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "description": "Уникальный идентификатор пользователя",
                               "readOnly": True},
                        "username": {"type": "string", "description": "Имя пользователя"},
                        "email": {"type": "string", "description": "Email пользователя"},
                        "is_admin": {"type": "boolean", "description": "Флаг администратора", "readOnly": True}
                    },
                    "required": ["id", "username", "email", "is_admin"]
                },
                "UserCreateRequest": {
                    "type": "object",
                    "properties": {
                        "username": {"type": "string", "description": "Имя пользователя (уникальное)"},
                        "email": {"type": "string", "description": "Email пользователя (уникальный)"},
                        "password": {"type": "string", "description": "Пароль пользователя"}
                    },
                    "required": ["username", "email", "password"]
                },
                "GenericErrorResponse": {
                    "type": "object",
                    "properties": {
                        "error": {"type": "string"},
                        "message": {"type": "string"}
                    }
                },
                "MessageResponse": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"}
                    }
                }
            },
            "responses": {
                "BookCreated": {
                    "description": "Книга успешно добавлена.",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Book"}
                        }
                    }
                },
                "MissingFieldsError": {
                    "description": "Отсутствуют обязательные поля в теле запроса.",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/GenericErrorResponse"}
                        }
                    }
                },
                "UnauthorizedError": {
                    "description": "Требуется аутентификация.",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/MessageResponse"}
                        }
                    }
                },
                "ForbiddenError": {
                    "description": "Доступ запрещен (требуются права администратора).",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/MessageResponse"}
                        }
                    }
                },
                "InternalServerError": {
                    "description": "Произошла внутренняя ошибка сервера или базы данных.",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/GenericErrorResponse"}
                        }
                    }
                },
                "NotFound": {
                    "description": "Ресурс не найден.",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/MessageResponse"}
                        }
                    }
                },
                "ConflictError": {
                    "description": "Ресурс уже существует (например, пользователь с таким именем/email).",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/GenericErrorResponse"}
                        }
                    }
                },
                "UserRegistered": {
                    "description": "Пользователь успешно зарегистрирован.",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "message": {"type": "string"},
                                    "user_id": {"type": "integer"}
                                }
                            }
                        }
                    }
                },
                "CurrentUserResponse": {
                    "description": "Информация о текущем пользователе.",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/User"}
                        }
                    }
                }
            },
            "securitySchemes": {
                "basicAuth": {
                    "type": "http",
                    "scheme": "basic"
                }
            }
        }
    }







    with app.app_context():
        print("Attempting to initialize database...")
        try:
            init_db()
            print("Database initialization routine finished.")
        except Exception as e:
            print(f"Error during database initialization: {e}")

    app.add_url_rule('/api/books', view_func=list_books, methods=['GET'])
    app.add_url_rule('/api/books/<int:book_id>', view_func=get_book, methods=['GET'])

    @app.route('/api/books', methods=['POST'])
    @login_required
    def create_book_route():
        """
        Добавить новую книгу
        ---
        tags:
          - Books
        summary: Добавить новую книгу
        description: Требуется Basic авторизация. Владелец книги определяется из аутентифицированного пользователя.
        security:
          - basicAuth: []
        requestBody:
          required: true
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BookCreateRequest'
        responses:
          201:
            $ref: '#/components/responses/BookCreated'
          400:
            $ref: '#/components/responses/MissingFieldsError'
          401:
            $ref: '#/components/responses/UnauthorizedError'
          500:
            $ref: '#/components/responses/InternalServerError'
        """
        db_generator = get_db()
        db = next(db_generator)

        try:
            data = request.get_json()
            if not data or not all(k in data for k in ('title', 'author')):
                return jsonify({"error": "Missing required fields (title, author)"}), 400

            owner_id = g.current_user.id

            new_book = Book(
                title=data['title'],
                author=data['author'],
                description=data.get('description'),
                owner_id=owner_id,
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

    app.add_url_rule('/api/register', view_func=register_user, methods=['POST'])

    app.add_url_rule('/api/users/me', view_func=get_current_user_info, methods=['GET'])

    @app.route('/')
    def index():
        return "Backend is running!"

    Swagger(app, template=swagger_template)

    return app
