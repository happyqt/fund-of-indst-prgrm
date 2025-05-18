import datetime

from flask import request, jsonify, g
from app.database import get_db
from app.models.user import User
from app.models.book import Book
from app.models.exchange import Exchange
from app.auth import login_required
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_


@login_required
def propose_exchange():
    """
    Создать новое предложение обмена.
    Текущий пользователь предлагает одну из своих книг (proposed_book_id)
    в обмен на книгу другого пользователя (requested_book_id).
    ---
    tags:
      - Exchanges
    summary: Предложить обмен книгами
    security:
      - basicAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ExchangeProposeRequest'
    responses:
      201:
        $ref: '#/components/responses/ExchangeCreated'
      400:
        description: Некорректный запрос (например, книги совпадают, одна из книг принадлежит текущему пользователю, если он ее запрашивает)
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MessageResponse'
      401:
        $ref: '#/components/responses/UnauthorizedError'
      404:
        description: Одна из книг не найдена или недоступна для обмена.
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MessageResponse'
      500:
        $ref: '#/components/responses/InternalServerError'
    """
    data = request.get_json()
    if not data or 'proposed_book_id' not in data or 'requested_book_id' not in data:
        return jsonify({"message": "Отсутствуют обязательные поля: proposed_book_id и requested_book_id"}), 400

    proposed_book_id = data.get('proposed_book_id')
    requested_book_id = data.get('requested_book_id')
    proposing_user_id = g.current_user.id

    if proposed_book_id == requested_book_id:
        return jsonify({"message": "Нельзя обменять книгу саму на себя."}), 400

    db_generator = get_db()
    db = next(db_generator)

    try:
        # print(f"[APP_DEBUG] propose_exchange: Trying to find proposed_book_id={proposed_book_id}")
        # # Вывести все книги, которые видит сессия приложения, для отладки
        # all_books_in_app_db = db.query(Book).all()
        # print(
        #     f"[APP_DEBUG] Books visible to app session: {[(b.id, b.title, b.owner_id, b.is_available) for b in all_books_in_app_db]}")

        proposed_book = db.query(Book).filter(Book.id == proposed_book_id, Book.is_available.is_(True)).first()
        if not proposed_book:
            return jsonify({"message": f"Предлагаемая книга с ID {proposed_book_id} не найдена или недоступна."}), 404

        if proposed_book.owner_id != proposing_user_id:
            return jsonify({"message": "Вы можете предлагать только свои книги."}), 403

        requested_book = db.query(Book).filter(Book.id == requested_book_id, Book.is_available.is_(True)).first()
        if not requested_book:
            return jsonify({"message": f"Запрашиваемая книга с ID {requested_book_id} не найдена или недоступна."}), 404
        if requested_book.owner_id == proposing_user_id:
            return jsonify({"message": "Нельзя запрашивать свою же книгу для обмена."}), 400

        receiving_user_id = requested_book.owner_id

        # Проверка на существующее активное предложение
        existing_proposal = db.query(Exchange).filter(
            Exchange.proposing_user_id == proposing_user_id,
            Exchange.proposed_book_id == proposed_book_id,
            Exchange.requested_book_id == requested_book_id,
            Exchange.status == 'pending'
        ).first()
        if existing_proposal:
            return jsonify({"message": "Вы уже сделали такое предложение обмена."}), 409

        new_exchange = Exchange(
            proposing_user_id=proposing_user_id,
            receiving_user_id=receiving_user_id,
            proposed_book_id=proposed_book_id,
            requested_book_id=requested_book_id,
            status='pending'
        )
        db.add(new_exchange)
        db.commit()
        db.refresh(new_exchange)

        exchange_data = {
            "id": new_exchange.id,
            "proposing_user_id": new_exchange.proposing_user_id,
            "receiving_user_id": new_exchange.receiving_user_id,
            "proposed_book_id": new_exchange.proposed_book_id,
            "requested_book_id": new_exchange.requested_book_id,
            "status": new_exchange.status,
            "created_at": new_exchange.created_at.isoformat() if new_exchange.created_at else None,
            "updated_at": new_exchange.updated_at.isoformat() if new_exchange.updated_at else None
        }
        return jsonify(exchange_data), 201

    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({"error": "Database error", "message": str(e)}), 500
    except Exception as e:
        db.rollback()
        return jsonify({"error": "Internal server error", "message": str(e)}), 500
    finally:
        db_generator.close()


@login_required
def list_user_exchanges():
    """
    Получить список предложений обмена для текущего пользователя.
    Можно фильтровать по типу: 'sent' (отправленные) или 'received' (полученные).
    По умолчанию показывает все предложения, где пользователь участвует.
    ---
    tags:
      - Exchanges
    summary: Список предложений обмена пользователя
    security:
      - basicAuth: []
    parameters:
      - name: type
        in: query
        required: false
        description: "Тип предложений для отображения ('sent' или 'received')"
        schema:
          type: string
          enum: ["sent", "received", "all"]
        default: "all"
    responses:
      200:
        description: Список предложений обмена.
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ExchangeListResponse'
      401:
        $ref: '#/components/responses/UnauthorizedError'
      500:
        $ref: '#/components/responses/InternalServerError'
    """
    user_id = g.current_user.id
    exchange_type = request.args.get('type', 'all')  # По умолчанию 'all'

    db_generator = get_db()
    db = next(db_generator)

    try:
        query = db.query(Exchange)
        if exchange_type == 'sent':
            query = query.filter(Exchange.proposing_user_id == user_id)
        elif exchange_type == 'received':
            query = query.filter(Exchange.receiving_user_id == user_id)
        elif exchange_type == 'all':
            query = query.filter(or_(Exchange.proposing_user_id == user_id, Exchange.receiving_user_id == user_id))
        else:
            return jsonify({
                "message": "Неверное значение для параметра 'type'. Допустимые значения: 'sent', 'received', 'all'."}), 400

        exchanges = query.order_by(Exchange.created_at.desc()).all()

        exchanges_list = []
        for ex in exchanges:
            exchanges_list.append({
                "id": ex.id,
                "proposing_user_id": ex.proposing_user_id,
                "receiving_user_id": ex.receiving_user_id,
                "proposed_book_id": ex.proposed_book_id,
                "requested_book_id": ex.requested_book_id,
                "status": ex.status,
                "created_at": ex.created_at.isoformat() if ex.created_at else None,
                "updated_at": ex.updated_at.isoformat() if ex.updated_at else None
            })
        return jsonify(exchanges_list), 200

    except SQLAlchemyError as e:
        return jsonify({"error": "Database error", "message": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500
    finally:
        db_generator.close()


@login_required
def accept_exchange(exchange_id):
    """
    Принять предложение обмена.
    Только получатель предложения (receiving_user) может принять его.
    Предложение должно быть в статусе 'pending'.
    При успешном принятии книги становятся недоступными, меняют владельцев,
    а конфликтующие предложения по этим книгам отклоняются.
    ---
    tags:
      - Exchanges
    summary: Принять предложение обмена
    security:
      - basicAuth: []
    parameters:
      - name: exchange_id
        in: path
        required: true
        description: ID предложения обмена
        schema:
          type: integer
    responses:
      200:
        $ref: '#/components/responses/ExchangeActionSuccess'
      401:
        $ref: '#/components/responses/UnauthorizedError'
      403:
        $ref: '#/components/responses/ExchangeActionForbidden'
      404:
        $ref: '#/components/responses/NotFound'
      409:
        description: Конфликт, например, одна из книг уже недоступна.
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MessageResponse'
      500:
        $ref: '#/components/responses/InternalServerError'
    """
    current_user_id = g.current_user.id
    db_generator = get_db()
    db = next(db_generator)

    try:
        exchange = db.query(Exchange).filter(Exchange.id == exchange_id).first()

        if not exchange:
            return jsonify({"message": "Предложение обмена не найдено."}), 404

        if exchange.receiving_user_id != current_user_id:
            return jsonify({"message": "Вы не можете принять это предложение обмена."}), 403

        if exchange.status != 'pending':
            return jsonify({
                "message": f"Предложение обмена не может быть принято,"
                           f" так как его текущий статус: '{exchange.status}'."}), 403

        # Получаем книги, участвующие в обмене
        proposed_book = db.query(Book).filter(Book.id == exchange.proposed_book_id, Book.is_available.is_(True)).first()
        requested_book = db.query(Book).filter(Book.id == exchange.requested_book_id,
                                               Book.is_available.is_(True)).first()

        # Проверка, что обе книги все еще существуют и доступны
        if not proposed_book:
            exchange.status = 'rejected'
            db.add(exchange)
            db.commit()
            return jsonify({
                "message": f"Предлагаемая книга (ID: {exchange.proposed_book_id}) больше недоступна или не существует. Предложение отклонено."}), 409

        if not requested_book:
            # Если запрашиваемая книга стала недоступна, отклоняем текущий обмен
            exchange.status = 'rejected'
            db.add(exchange)
            db.commit()
            return jsonify({
                "message": f"Запрашиваемая книга (ID: {exchange.requested_book_id}) больше недоступна или не существует. Предложение отклонено."}), 409

        # Проверка, что владельцы книг не изменились неожиданно
        if proposed_book.owner_id != exchange.proposing_user_id:
            exchange.status = 'rejected'
            db.add(exchange)
            db.commit()
            return jsonify({"message": "Владелец предлагаемой книги изменился. Предложение отклонено."}), 409

        exchange.status = 'accepted'

        original_proposer_id = exchange.proposing_user_id
        original_receiver_id = exchange.receiving_user_id

        proposed_book.owner_id = original_receiver_id
        requested_book.owner_id = original_proposer_id

        proposed_book.is_available = False
        requested_book.is_available = False

        db.add(exchange)
        db.add(proposed_book)
        db.add(requested_book)

        # Находим и отклоняем все другие 'pending' предложения, затрагивающие эти две книги
        conflicting_exchanges = db.query(Exchange).filter(
            Exchange.id != exchange.id,
            Exchange.status == 'pending',
            or_(
                Exchange.proposed_book_id == proposed_book.id,
                Exchange.requested_book_id == proposed_book.id,
                Exchange.proposed_book_id == requested_book.id,
                Exchange.requested_book_id == requested_book.id
            )
        ).all()

        for conf_ex in conflicting_exchanges:
            conf_ex.status = 'rejected'
            db.add(conf_ex)

        db.commit()

        db.refresh(exchange)
        db.refresh(proposed_book)
        db.refresh(requested_book)
        for conf_ex in conflicting_exchanges:
            db.refresh(conf_ex)

        exchange_data = {
            "id": exchange.id,
            "proposing_user_id": exchange.proposing_user_id,
            "receiving_user_id": exchange.receiving_user_id,
            "proposed_book_id": exchange.proposed_book_id,
            "requested_book_id": exchange.requested_book_id,
            "status": exchange.status,
            "created_at": exchange.created_at.isoformat() if exchange.created_at else None,
            "updated_at": exchange.updated_at.isoformat() if exchange.updated_at else None
        }
        return jsonify(exchange_data), 200

    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({"error": "Database error", "message": str(e)}), 500
    except Exception as e:
        db.rollback()
        return jsonify({"error": "Internal server error", "message": str(e)}), 500
    finally:
        db_generator.close()


@login_required
def reject_exchange(exchange_id):
    """
    Отклонить предложение обмена.
    Только получатель предложения (receiving_user) может отклонить его.
    Предложение должно быть в статусе 'pending'.
    ---
    tags:
      - Exchanges
    summary: Отклонить предложение обмена
    security:
      - basicAuth: []
    parameters:
      - name: exchange_id
        in: path
        required: true
        description: ID предложения обмена
        schema:
          type: integer
    responses:
      200:
        $ref: '#/components/responses/ExchangeActionSuccess'
      401:
        $ref: '#/components/responses/UnauthorizedError'
      403:
        $ref: '#/components/responses/ExchangeActionForbidden'
      404:
        $ref: '#/components/responses/NotFound'
      500:
        $ref: '#/components/responses/InternalServerError'
    """
    current_user_id = g.current_user.id
    db_generator = get_db()
    db = next(db_generator)

    try:
        exchange = db.query(Exchange).filter(Exchange.id == exchange_id).first()

        if not exchange:
            return jsonify({"message": "Предложение обмена не найдено."}), 404

        if exchange.receiving_user_id != current_user_id:
            return jsonify({"message": "Вы не можете отклонить это предложение обмена."}), 403

        if exchange.status != 'pending':
            return jsonify({
                "message": f"Предложение обмена не может быть отклонено, так как его текущий статус: '{exchange.status}'."}), 403

        exchange.status = 'rejected'
        db.add(exchange)
        db.commit()
        db.refresh(exchange)

        exchange_data = {
            "id": exchange.id,
            "proposing_user_id": exchange.proposing_user_id,
            "receiving_user_id": exchange.receiving_user_id,
            "proposed_book_id": exchange.proposed_book_id,
            "requested_book_id": exchange.requested_book_id,
            "status": exchange.status,
            "created_at": exchange.created_at.isoformat() if exchange.created_at else None,
            "updated_at": exchange.updated_at.isoformat() if exchange.updated_at else None
        }
        return jsonify(exchange_data), 200

    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({"error": "Database error", "message": str(e)}), 500
    except Exception as e:
        db.rollback()
        return jsonify({"error": "Internal server error", "message": str(e)}), 500
    finally:
        db_generator.close()


@login_required
def cancel_exchange_proposal(exchange_id):
    """
    Отменить свое предложение обмена.
    Только пользователь, инициировавший предложение (proposing_user), может отменить его.
    Предложение должно быть в статусе 'pending'.
    ---
    tags:
      - Exchanges
    summary: Отменить свое предложение обмена
    security:
      - basicAuth: []
    parameters:
      - name: exchange_id
        in: path
        required: true
        description: ID предложения обмена для отмены
        schema:
          type: integer
    responses:
      200:
        description: Предложение обмена успешно отменено.
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Exchange'
      401:
        $ref: '#/components/responses/UnauthorizedError'
      403:
        $ref: '#/components/responses/ExchangeCancelForbidden'
      404:
        $ref: '#/components/responses/NotFound'
      500:
        $ref: '#/components/responses/InternalServerError'
    """
    current_user_id = g.current_user.id
    db_generator = get_db()
    db = next(db_generator)

    try:
        exchange = db.query(Exchange).filter(Exchange.id == exchange_id).first()

        if not exchange:
            return jsonify({"message": "Предложение обмена не найдено."}), 404

        if exchange.proposing_user_id != current_user_id:
            return jsonify(
                {"message": "Вы не можете отменить это предложение обмена, так как не являетесь его инициатором."}), 403

        if exchange.status != 'pending':
            return jsonify({
                "message": f"Предложение обмена не может быть отменено, так как его текущий статус: '{exchange.status}'."}), 403

        exchange.status = 'cancelled'
        db.add(exchange)
        db.commit()
        db.refresh(exchange)

        exchange_data = {
            "id": exchange.id,
            "proposing_user_id": exchange.proposing_user_id,
            "receiving_user_id": exchange.receiving_user_id,
            "proposed_book_id": exchange.proposed_book_id,
            "requested_book_id": exchange.requested_book_id,
            "status": exchange.status,
            "created_at": exchange.created_at.isoformat() if exchange.created_at else None,
            "updated_at": exchange.updated_at.isoformat() if exchange.updated_at else None
        }
        return jsonify(exchange_data), 200

    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({"error": "Database error", "message": str(e)}), 500
    except Exception as e:
        db.rollback()
        return jsonify({"error": "Internal server error", "message": str(e)}), 500
    finally:
        db_generator.close()
