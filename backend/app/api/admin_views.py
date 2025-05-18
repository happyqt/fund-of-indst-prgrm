"""
Модуль для обработки запросов, связанных с административными функциями.
"""
from flask import jsonify
from app.database import get_db
from app.models.user import User
from app.models.book import Book
from app.models.exchange import Exchange
from app.auth import admin_required
from sqlalchemy import func, case
from sqlalchemy.exc import SQLAlchemyError


@admin_required
def get_exchange_stats():
    """
    Получить статистику по обменам.
    Только для администраторов.
    ---
    tags:
      - Admin
    summary: Получить статистику по всем обменам в системе
    security:
      - basicAuth: []
    responses:
      200:
        description: Статистика по обменам.
        content:
          application/json:
            schema:
              type: object
              properties:
                total_exchanges:
                  type: integer
                  description: Общее количество обменов
                pending_count:
                  type: integer
                  description: Количество обменов в статусе 'pending'
                accepted_count:
                  type: integer
                  description: Количество обменов в статусе 'accepted'
                rejected_count:
                  type: integer
                  description: Количество обменов в статусе 'rejected'
                cancelled_count:
                  type: integer
                  description: Количество обменов в статусе 'cancelled'
      401:
        $ref: '#/components/responses/UnauthorizedError'
      403:
        $ref: '#/components/responses/ForbiddenError'
      500:
        $ref: '#/components/responses/InternalServerError'
    """
    db_generator = get_db()
    db = next(db_generator)
    try:
        total_exchanges = db.query(func.count(Exchange.id)).scalar()

        status_counts = db.query(
            Exchange.status,
            func.count(Exchange.id)
        ).group_by(Exchange.status).all()

        stats = {
            "total_exchanges": total_exchanges,
            "pending_count": 0,
            "accepted_count": 0,
            "rejected_count": 0,
            "cancelled_count": 0
        }
        for status_value, count in status_counts:
            key_name = f"{status_value}_count"
            if key_name in stats:
                stats[key_name] = count

        return jsonify(stats), 200
    except SQLAlchemyError as e:
        return jsonify({"error": "Database error", "message": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500
    finally:
        db_generator.close()


@admin_required
def list_all_books_admin():
    """
    Получить список всех книг в системе (включая недоступные).
    Только для администраторов.
    ---
    tags:
      - Admin
    summary: Получить список всех книг в системе (администратор)
    security:
      - basicAuth: []
    responses:
      200:
        description: Список всех книг.
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/BookListResponse' # Используем ту же схему
      401:
        $ref: '#/components/responses/UnauthorizedError'
      403:
        $ref: '#/components/responses/ForbiddenError'
      500:
        $ref: '#/components/responses/InternalServerError'
    """
    db_generator = get_db()
    db = next(db_generator)
    try:
        books = db.query(Book).order_by(Book.id).all()
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


@admin_required
def list_all_users_admin():
    """
    Получить список всех пользователей в системе.
    Только для администраторов. Пароли не возвращаются.
    ---
    tags:
      - Admin
    summary: Получить список всех пользователей в системе (администратор)
    security:
      - basicAuth: []
    responses:
      200:
        description: Список всех пользователей.
        content:
          application/json:
            schema:
              type: array
              items:
                $ref: '#/components/schemas/User' # Используем стандартную схему User
      401:
        $ref: '#/components/responses/UnauthorizedError'
      403:
        $ref: '#/components/responses/ForbiddenError'
      500:
        $ref: '#/components/responses/InternalServerError'
    """
    db_generator = get_db()
    db = next(db_generator)
    try:
        users = db.query(User).order_by(User.id).all()
        users_list = []
        for user in users:
            users_list.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_admin": user.is_admin
                # Hashed password не включаем
            })
        return jsonify(users_list), 200
    except SQLAlchemyError as e:
        return jsonify({"error": "Database error", "message": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500
    finally:
        db_generator.close()
