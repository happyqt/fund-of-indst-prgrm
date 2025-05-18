import React, {useState, useEffect} from 'react';
import {useParams} from 'react-router-dom';
import {useAuth} from '../context/AuthContext';
import './BookDetailPage.css';
import './Form.css';

function BookDetailPage() {
    const {book_id} = useParams();

    const [book, setBook] = useState(null);
    const [reviews, setReviews] = useState([]);
    const [bookLoading, setBookLoading] = useState(true);
    const [bookError, setBookError] = useState(null);


    const [reviewRating, setReviewRating] = useState(5); // Дефолтное значение рейтинга
    const [reviewText, setReviewText] = useState('');
    const [reviewLoading, setReviewLoading] = useState(false);
    const [reviewError, setReviewError] = useState(null);
    const [reviewSuccess, setReviewSuccess] = useState(null);

    const {isAuthenticated, isLoading: authLoading, getAuthHeader} = useAuth();

    const fetchReviews = async () => {
        try {
            const response = await fetch(`/api/books/${book_id}/reviews`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || `Ошибка загрузки отзывов: ${response.status}`);
            }
            const data = await response.json();
            setReviews(data);
        } catch (err) {
            console.error("Failed to fetch reviews:", err);
        }
    };


    useEffect(() => {
        const fetchBookDetails = async () => {
            setBookLoading(true);
            setBookError(null);
            try {
                const response = await fetch(`/api/books/${book_id}`);
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.message || `Ошибка загрузки книги: ${response.status}`);
                }
                const data = await response.json();
                setBook(data);
            } catch (err) {
                console.error("Failed to fetch book details:", err);
                setBookError('Не удалось загрузить информацию о книге. Попробуйте позже.');
            } finally {
                setBookLoading(false);
            }
        };

        fetchBookDetails();
        fetchReviews();

    }, [book_id]); // book_id - параметр из URL

    const handleReviewSubmit = async (event) => {
        event.preventDefault();

        // Не отправляем отзыв, если не аутентифицированы (дополнительная проверка)
        if (!isAuthenticated) {
            setError("Для отправки отзыва необходимо войти.");
            return;
        }

        setReviewLoading(true);
        setReviewError(null);
        setReviewSuccess(null);

        const rating = parseInt(reviewRating, 10); // Преобразуем в число
        if (isNaN(rating) || rating < 1 || rating > 5) {
            setReviewError("Рейтинг должен быть числом от 1 до 5.");
            setReviewLoading(false);
            return;
        }


        const reviewData = {
            rating: rating,
            text: reviewText || null, // Отправляем null, если текст пустой
        };

        try {
            const response = await fetch(`/api/books/${book_id}/reviews`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': getAuthHeader(), // Требуется аутентификация для оставления отзыва
                },
                body: JSON.stringify(reviewData),
            });

            const data = await response.json();

            if (response.ok) {
                setReviewSuccess('Ваш отзыв успешно добавлен!');
                setReviewRating(5); // Сбрасываем рейтинг к дефолту
                setReviewText('');
                fetchReviews();
            } else {
                setReviewError(data.message || data.error || `Ошибка отправки отзыва: ${response.status}`);
            }
        } catch (err) {
            console.error("Failed to submit review:", err);
            setReviewError('Произошла ошибка при отправке отзыва. Попробуйте снова.');
        } finally {
            setReviewLoading(false);
        }
    };


    if (bookLoading) {
        return <p>Загрузка деталей книги...</p>;
    }

    if (bookError) {
        return <p className="error-message">Ошибка: {bookError}</p>;
    }

    if (!book && !bookLoading) {
        return <p>Книга не найдена.</p>;
    }


    return (
        <div className="book-detail-container">
            <h2>{book.title}</h2>
            <p><strong>Автор:</strong> {book.author}</p>
            {book.description && <p><strong>Описание:</strong> {book.description}</p>}
            <p><strong>Владелец (ID):</strong> {book.owner_id}</p>
            <p><strong>Статус:</strong> {book.is_available ? 'Доступна для обмена' : 'Недоступна'}</p>

            <hr/>

            <h3>Отзывы</h3>
            {/* Форма для оставления отзыва - показываем только аутентифицированным пользователям */}
            {!authLoading && isAuthenticated && (
                <div className="review-form-section form-container"> {/* Используем стили форм */}
                    <h4>Оставить отзыв</h4>
                    <form onSubmit={handleReviewSubmit}>
                        <div>
                            <label htmlFor="rating">Рейтинг:</label>
                            <select
                                id="rating"
                                value={reviewRating}
                                onChange={(e) => setReviewRating(e.target.value)}
                                required
                                disabled={reviewLoading}
                            >
                                <option value="1">1</option>
                                <option value="2">2</option>
                                <option value="3">3</option>
                                <option value="4">4</option>
                                <option value="5">5</option>
                            </select>
                        </div>
                        <div>
                            <label htmlFor="reviewText">Текст отзыва (необязательно):</label>
                            <textarea
                                id="reviewText"
                                value={reviewText}
                                onChange={(e) => setReviewText(e.target.value)}
                                disabled={reviewLoading}
                                rows="3"
                            ></textarea>
                        </div>

                        {reviewError && <p className="error-message">{reviewError}</p>}
                        {reviewSuccess && <p className="success-message">{reviewSuccess}</p>}

                        <button type="submit" disabled={reviewLoading}>
                            {reviewLoading ? 'Отправка...' : 'Отправить отзыв'}
                        </button>
                    </form>
                </div>
            )}
            {/* Сообщение для неаутентифицированных пользователей */}
            {!authLoading && !isAuthenticated && (
                <p>Войдите, чтобы оставить отзыв.</p>
            )}


            {/* Список отзывов */}
            {reviews.length === 0 ? (
                <p>Нет отзывов для этой книги.</p>
            ) : (
                <ul className="reviews-list">
                    {reviews.map(review => (
                        <li key={review.id} className="review-item">
                            {/* Убедимся, что review.user существует перед доступом к username */}
                            <p>
                                <strong>{review.user?.username || 'Неизвестный пользователь'}:</strong> Оценка {review.rating}/5
                            </p>
                            {review.text && <p>{review.text}</p>}
                            {/* Проверяем review.created_at перед вызовом toLocaleDateString */}
                            <small>Оставлен: {review.created_at ? new Date(review.created_at).toLocaleDateString() : 'Дата неизвестна'}</small>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}

export default BookDetailPage;