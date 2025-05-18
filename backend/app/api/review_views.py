"""
Модуль для обработки запросов, связанных с отзывами о книгах.
"""
from flask import request, jsonify, g
from app.database import get_db
from app.models.book import Book
from app.models.user import User
from app.models.review import Review
from app.auth import login_required
from sqlalchemy.exc import SQLAlchemyError, IntegrityError


def get_reviews_for_book(book_id):
    """
    Получить все отзывы для конкретной книги.
    ---
    tags:
      - Reviews
    summary: Получить все отзывы для книги
    parameters:
      - name: book_id
        in: path
        required: true
        description: ID книги, для которой запрашиваются отзывы
        schema:
          type: integer
    responses:
      200:
        description: Список отзывов для книги.
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ReviewListResponse'
      404:
        description: Книга не найдена.
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
        if not book:
            return jsonify({"message": "Книга не найдена."}), 404

        reviews = db.query(Review).filter(Review.book_id == book_id).order_by(Review.created_at.desc()).all()
        reviews_list = []
        for review in reviews:
            user_info = {"id": review.user.id, "username": review.user.username}
            reviews_list.append({
                "id": review.id,
                "book_id": review.book_id,
                "user": user_info,
                "rating": review.rating,
                "text": review.text,
                "created_at": review.created_at.isoformat() if review.created_at else None,
                "updated_at": review.updated_at.isoformat() if review.updated_at else None
            })
        return jsonify(reviews_list), 200
    except SQLAlchemyError as e:
        return jsonify({"error": "Database error", "message": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500
    finally:
        db_generator.close()


@login_required
def create_review_for_book(book_id):
    """
    Оставить отзыв о книге.
    Пользователь не может оставлять более одного отзыва на одну книгу.
    ---
    tags:
      - Reviews
    summary: Оставить отзыв о книге
    security:
      - basicAuth: []
    parameters:
      - name: book_id
        in: path
        required: true
        description: ID книги, для которой оставляется отзыв
        schema:
          type: integer
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ReviewCreateRequest'
    responses:
      201:
        description: Отзыв успешно создан.
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ReviewResponse'
      400:
        description: Некорректный запрос (например, неверный рейтинг, отсутствуют поля).
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MessageResponse'
      401:
        $ref: '#/components/responses/UnauthorizedError'
      403:
        description: >
          Действие запрещено (например, повторный отзыв на ту же книгу).
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MessageResponse'
      404:
        description: Книга не найдена.
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MessageResponse'
      500:
        $ref: '#/components/responses/InternalServerError'
    """
    data = request.get_json()
    if not data or 'rating' not in data:
        return jsonify({"message": "Отсутствует обязательное поле 'rating'."}), 400

    rating = data.get('rating')
    text = data.get('text', None)

    if not isinstance(rating, int) or not (1 <= rating <= 5):
        return jsonify({"message": "Рейтинг должен быть целым числом от 1 до 5."}), 400

    db_generator = get_db()
    db = next(db_generator)

    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            return jsonify({"message": "Книга не найдена."}), 404

        current_user_id = g.current_user.id

        existing_review = db.query(Review).filter(
            Review.book_id == book_id,
            Review.user_id == current_user_id
        ).first()

        if existing_review:
            return jsonify({"message": "Вы уже оставили отзыв на эту книгу."}), 403

        new_review = Review(
            book_id=book_id,
            user_id=current_user_id,
            rating=rating,
            text=text
        )
        db.add(new_review)
        db.commit()
        db.refresh(new_review)


        db.refresh(new_review.user)

        user_info = {"id": new_review.user.id, "username": new_review.user.username}
        review_data = {
            "id": new_review.id,
            "book_id": new_review.book_id,
            "user": user_info,
            "rating": new_review.rating,
            "text": new_review.text,
            "created_at": new_review.created_at.isoformat() if new_review.created_at else None,
            "updated_at": new_review.updated_at.isoformat() if new_review.updated_at else None
        }
        return jsonify(review_data), 201

    except IntegrityError:
        db.rollback()
        return jsonify({"error": "Database integrity error", "message": "Возможно, неверное значение рейтинга."}), 400
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({"error": "Database error", "message": str(e)}), 500
    except Exception as e:
        db.rollback()
        return jsonify({"error": "Internal server error", "message": str(e)}), 500
    finally:
        db_generator.close()
