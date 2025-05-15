"""
Модуль для реализации базовой аутентификации и авторизации
"""
import base64
from flask import request, jsonify, g
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import get_db  # Предполагаем, что get_db доступен
from app.models.user import User  # Предполагаем, что модель User доступна


def hash_password(password):
    """
    Хэширует пароль с использованием Werkzeug.
    """
    return generate_password_hash(password)


def verify_password(stored_hash, provided_password):
    """
    Проверяет соответствие предоставленного пароля сохраненному хэшу.
    """
    return check_password_hash(stored_hash, provided_password)


def authenticate_basic():
    """
    Извлекает и декодирует учетные данные Basic авторизации из заголовка запроса.
    Возвращает кортеж (username, password) или None, если заголовок отсутствует
    или некорректен.
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None

    parts = auth_header.split()
    if parts[0].lower() != 'basic' or len(parts) != 2:
        return None

    try:
        decoded_bytes = base64.b64decode(parts[1])
        decoded_string = decoded_bytes.decode('utf-8')
        # Ожидаем формат "username:password"
        username, password = decoded_string.split(':', 1)
        return username, password
    except Exception:
        return None


def login_required(f):
    """
    Декоратор для защиты эндпоинтов, требующих аутентификации.
    Извлекает учетные данные из заголовка Basic Auth, ищет пользователя
    в базе данных и проверяет пароль.
    Если аутентификация успешна, сохраняет объект пользователя в g.current_user
    и вызывает декорируемую функцию.
    В противном случае возвращает ответ 401 Unauthorized.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        credentials = authenticate_basic()
        if not credentials:
            return jsonify({"message": "Authentication required"}), 401

        username, password = credentials
        db_generator = get_db()
        db = next(db_generator)

        try:
            user = db.query(User).filter_by(username=username).first()

            if user is None or not verify_password(user.hashed_password, password):
                return jsonify({"message": "Invalid credentials"}), 401

            # Сохраняем аутентифицированного пользователя в контексте запроса
            g.current_user = user

        except Exception as e:
            return jsonify({"error": "Authentication failed", "message": str(e)}), 500
        finally:
            db_generator.close()

        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """
    Декоратор для защиты эндпоинтов, требующих аутентификации администратора.
    Использует login_required, а затем проверяет, является ли пользователь администратором.
    """

    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        # После login_required, аутентифицированный пользователь находится в g.current_user
        if not hasattr(g, 'current_user') or not g.current_user.is_admin:
            return jsonify({"message": "Administrator access required"}), 403

        return f(*args, **kwargs)

    return decorated_function
