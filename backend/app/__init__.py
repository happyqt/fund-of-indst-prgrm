from flask import Flask
from app.database import init_db, get_db
from app.models.book import Book
from app.models.user import User
from app.api.book_views import BookAPI
from flasgger import Swagger


def create_app():
    app = Flask(__name__)
    app.config['SWAGGER'] = {
        'title': 'OA3 Callbacks',
        'openapi': '3.0.2'
    }
    swagger_template = {
        "info": {
            "title": "Book Exchange API",
            "description": "API для сервиса обмена книгами",
            "version": "1.0.0"
        },
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
                            "nullable": True  # Важно указать nullable для опциональных полей
                        },
                        "owner_id": {
                            "type": "integer",
                            "description": "ID пользователя-владельца книги"
                        },
                        "is_available": {
                            "type": "boolean",
                            "description": "Флаг доступности книги для обмена",
                            "default": True  # Указываем значение по умолчанию
                        }
                    },
                    "required": [
                        "title",
                        "author",
                        "owner_id"
                    ]
                },
                "BookCreateRequest": {  # <-- Новая схема для тела POST запроса
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
                        },
                        "owner_id": {
                            "type": "integer",
                            "description": "ID пользователя-владельца книги"
                        }
                    },
                    "required": ["title", "author", "owner_id"]
                }
            }
        },
    }



    Swagger(app, template=swagger_template)


    with app.app_context():
        print("Attempting to initialize database...")
        try:
            init_db()
            print("Database initialization routine finished.")
        except Exception as e:
            print(f"Error during database initialization: {e}")

    book_view = BookAPI.as_view('book_api')
    app.add_url_rule('/api/books', view_func=book_view, methods=['GET', 'POST'])
    app.add_url_rule('/api/books/<int:book_id>', view_func=book_view, methods=['GET'])

    @app.route('/')
    def index():
        return "Backend is running!"

    return app
