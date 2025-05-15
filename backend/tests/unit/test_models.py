import unittest
from app.models.book import Book
from app.models.user import User
from app.models.exchange import Exchange

class TestModels(unittest.TestCase):

    def test_book_instantiation(self):
        """Проверка создания экземпляра модели Book."""
        book = Book(title="Тестовая Книга", author="Тестовый Автор",
                    owner_id=1, description="Описание тестовой книги.", is_available=True)
        self.assertEqual(book.title, "Тестовая Книга")
        self.assertEqual(book.author, "Тестовый Автор")
        self.assertEqual(book.owner_id, 1)
        self.assertEqual(book.description, "Описание тестовой книги.")
        self.assertTrue(book.is_available)

    def test_user_instantiation(self):
        """Проверка создания экземпляра модели User."""
        user = User(username="test_user", email="test@example.com",
                    hashed_password="hashed_password", is_admin=False)
        self.assertEqual(user.username, "test_user")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.hashed_password, "hashed_password")
        self.assertFalse(user.is_admin)

    def test_exchange_instantiation(self):
        """Проверка создания экземпляра модели Exchange."""
        # Проверка создания с указанным статусом
        exchange = Exchange(
            proposing_user_id=1,
            receiving_user_id=2,
            proposed_book_id=10,
            requested_book_id=20,
            status='accepted'
        )
        self.assertEqual(exchange.proposing_user_id, 1)
        self.assertEqual(exchange.receiving_user_id, 2)
        self.assertEqual(exchange.proposed_book_id, 10)
        self.assertEqual(exchange.requested_book_id, 20)
        self.assertEqual(exchange.status, 'accepted')

        # Проверка значения статуса по умолчанию при инициировании
        exchange_default_instantiation = Exchange(proposing_user_id=1, receiving_user_id=2,
                                                  proposed_book_id=10, requested_book_id=20)
        self.assertIsNone(exchange_default_instantiation.status)