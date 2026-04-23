import React, {useState, useEffect, useCallback} from 'react';
import {useParams, Link} from 'react-router-dom';
import {useAuth} from '../context/AuthContext';
import './BookDetailPage.css';
import './Form.css';

function BookDetailPage() {
    const {book_id} = useParams();

    const [book, setBook] = useState(null);
    const [reviews, setReviews] = useState([]);
    const [bookLoading, setBookLoading] = useState(true);
    const [bookError, setBookError] = useState(null);

    const [reviewRating, setReviewRating] = useState(5);
    const [reviewText, setReviewText] = useState('');
    const [reviewLoading, setReviewLoading] = useState(false);
    const [reviewError, setReviewError] = useState(null);
    const [reviewSuccess, setReviewSuccess] = useState(null);

    const [userAvailableBooks, setUserAvailableBooks] = useState([]);
    const [selectedProposingBookId, setSelectedProposingBookId] = useState('');
    const [exchangeLocation, setExchangeLocation] = useState('');
    const [exchangeLoading, setExchangeLoading] = useState(false);
    const [exchangeError, setExchangeError] = useState(null);
    const [exchangeSuccess, setExchangeSuccess] = useState(null);
    const [fetchingUserBooks, setFetchingUserBooks] = useState(false);


    const {user, isAuthenticated, isLoading: authLoading, getAuthHeader} = useAuth();

    const fetchBookAndReviews = useCallback(async () => {
        setBookLoading(true);
        setBookError(null);
        setReviews([]);
        try {
            const response = await fetch(`/api/books/${book_id}`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || `Ошибка загрузки книги: ${response.status}`);
            }
            const data = await response.json();
            setBook(data);

            const reviewsResponse = await fetch(`/api/books/${book_id}/reviews`);
            if (!reviewsResponse.ok) {
                console.warn(`Ошибка загрузки отзывов: ${reviewsResponse.status}`);
            } else {
                const reviewsData = await reviewsResponse.json();
                setReviews(reviewsData);
            }

        } catch (err) {
            console.error("Failed to fetch book details or reviews:", err);
            setBookError('Не удалось загрузить информацию о книге. Попробуйте позже.');
        } finally {
            setBookLoading(false);
        }
    }, [book_id]);

    useEffect(() => {
        fetchBookAndReviews();
    }, [fetchBookAndReviews]);


    const fetchUserAvailableBooks = useCallback(async () => {
        if (!isAuthenticated || !user) return;
        setFetchingUserBooks(true);
        setExchangeError(null);
        setUserAvailableBooks([]);
        try {
            const response = await fetch('/api/users/me/books', {
                headers: {'Authorization': getAuthHeader()}
            });
            if (!response.ok) throw new Error('Не удалось загрузить ваши книги');
            const myBooks = await response.json();
            const availableForProposal = myBooks.filter(b => b.is_available && b.id !== parseInt(book_id));
            setUserAvailableBooks(availableForProposal);
            if (availableForProposal.length > 0) {
                setSelectedProposingBookId(availableForProposal[0].id.toString());
            } else {
                setSelectedProposingBookId('');
            }
        } catch (err) {
            console.error("Failed to fetch user's available books:", err);
            setExchangeError('Не удалось загрузить ваши доступные книги для предложения.');
        } finally {
            setFetchingUserBooks(false);
        }
    }, [isAuthenticated, user, getAuthHeader, book_id]);

    const canProposeExchange = isAuthenticated && book && book.owner_id !== user?.id && book.is_available;

    useEffect(() => {
        if (canProposeExchange) {
            fetchUserAvailableBooks();
        }
    }, [canProposeExchange, fetchUserAvailableBooks]);


    const handleReviewSubmit = async (event) => {
        event.preventDefault();
        if (!isAuthenticated) {
            setReviewError("Для отправки отзыва необходимо войти.");
            return;
        }
        setReviewLoading(true);
        setReviewError(null);
        setReviewSuccess(null);
        const rating = parseInt(reviewRating, 10);
        if (isNaN(rating) || rating < 1 || rating > 5) {
            setReviewError("Рейтинг должен быть числом от 1 до 5.");
            setReviewLoading(false);
            return;
        }
        const reviewData = {rating, text: reviewText || null};
        try {
            const response = await fetch(`/api/books/${book_id}/reviews`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json', 'Authorization': getAuthHeader()},
                body: JSON.stringify(reviewData),
            });
            const data = await response.json();
            if (response.ok) {
                setReviewSuccess('Ваш отзыв успешно добавлен!');
                setReviewRating(5);
                setReviewText('');
                fetchBookAndReviews();
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

    const handleExchangeProposeSubmit = async (event) => {
        event.preventDefault();
        if (!selectedProposingBookId) {
            setExchangeError('Пожалуйста, выберите книгу, которую вы предлагаете.');
            return;
        }
        setExchangeLoading(true);
        setExchangeError(null);
        setExchangeSuccess(null);

        const exchangeData = {
            proposed_book_id: parseInt(selectedProposingBookId, 10),
            requested_book_id: parseInt(book_id, 10),
            exchange_location: exchangeLocation || null,
        };

        try {
            const response = await fetch('/api/exchanges', {
                method: 'POST',
                headers: {'Content-Type': 'application/json', 'Authorization': getAuthHeader()},
                body: JSON.stringify(exchangeData),
            });
            const data = await response.json();
            if (response.ok) {
                setExchangeSuccess('Предложение обмена успешно отправлено!');
                setExchangeLocation('');
            } else {
                setExchangeError(data.message || data.error || `Ошибка предложения обмена: ${response.status}`);
            }
        } catch (err) {
            console.error("Failed to propose exchange:", err);
            setExchangeError('Произошла ошибка при отправке предложения. Попробуйте снова.');
        } finally {
            setExchangeLoading(false);
        }
    };


    if (authLoading || bookLoading) {
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
            <p><strong>Владелец:</strong> {book.owner_username || `ID: ${book.owner_id}`}
                {isAuthenticated && user?.id === book.owner_id && <span> (Это ваша книга)</span>}
            </p>
            <p><strong>Статус:</strong> {book.is_available ? 'Доступна для обмена' : 'Недоступна'}</p>

            {canProposeExchange && (
                <div className="exchange-propose-section form-container">
                    <h4>Предложить обмен на эту книгу</h4>
                    {fetchingUserBooks && <p>Загрузка ваших доступных книг...</p>}
                    {!fetchingUserBooks && userAvailableBooks.length === 0 && (
                        <p>У вас нет доступных книг для предложения или вы пытаетесь обменять книгу на саму себя.</p>
                    )}
                    {!fetchingUserBooks && userAvailableBooks.length > 0 && (
                        <form onSubmit={handleExchangeProposeSubmit}>
                            <div>
                                <label htmlFor="proposingBook">Предложить вашу книгу:</label>
                                <select
                                    id="proposingBook"
                                    value={selectedProposingBookId}
                                    onChange={(e) => setSelectedProposingBookId(e.target.value)}
                                    required
                                    disabled={exchangeLoading}
                                >
                                    {userAvailableBooks.map(b => (
                                        <option key={b.id} value={b.id.toString()}>
                                            {b.title} (Автор: {b.author})
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label htmlFor="exchangeLocation">Место обмена (необязательно):</label>
                                <input
                                    type="text"
                                    id="exchangeLocation"
                                    value={exchangeLocation}
                                    onChange={(e) => setExchangeLocation(e.target.value)}
                                    disabled={exchangeLoading}
                                    placeholder="Например, библиотека корпуса Х"
                                />
                            </div>
                            {exchangeError && <p className="error-message">{exchangeError}</p>}
                            {exchangeSuccess && <p className="success-message">{exchangeSuccess}</p>}
                            <button type="submit" disabled={exchangeLoading}>
                                {exchangeLoading ? 'Отправка предложения...' : 'Предложить обмен'}
                            </button>
                        </form>
                    )}
                    {exchangeError && userAvailableBooks.length > 0 &&
                        <p className="error-message" style={{marginTop: "10px"}}>{exchangeError}</p>}

                </div>
            )}


            <hr/>

            <h3>Отзывы</h3>
            {!authLoading && isAuthenticated && (
                <div className="review-form-section form-container"> {/* Используем стили форм */}
                    <h4>Оставить отзыв</h4>
                    <form onSubmit={handleReviewSubmit}>
                        <div>
                            <label htmlFor="rating">Рейтинг:</label>
                            <select id="rating" value={reviewRating} onChange={(e) => setReviewRating(e.target.value)}
                                    required disabled={reviewLoading}>
                                {[1, 2, 3, 4, 5].map(r => <option key={r} value={r}>{r}</option>)}
                            </select>
                        </div>
                        <div>
                            <label htmlFor="reviewText">Текст отзыва (необязательно):</label>
                            <textarea id="reviewText" value={reviewText} onChange={(e) => setReviewText(e.target.value)}
                                      disabled={reviewLoading} rows="3"></textarea>
                        </div>
                        {reviewError && <p className="error-message">{reviewError}</p>}
                        {reviewSuccess && <p className="success-message">{reviewSuccess}</p>}
                        <button type="submit" disabled={reviewLoading}>
                            {reviewLoading ? 'Отправка...' : 'Отправить отзыв'}
                        </button>
                    </form>
                </div>
            )}
            {!authLoading && !isAuthenticated && (
                <p>Войдите, чтобы оставить отзыв.</p>
            )}

            {reviews.length === 0 ? (
                <p>Нет отзывов для этой книги.</p>
            ) : (
                <ul className="reviews-list">
                    {reviews.map(review => (
                        <li key={review.id} className="review-item">
                            <p>
                                <strong>{review.user?.username || 'Неизвестный пользователь'}:</strong>
                                {' '}<span className="stars">{'★'.repeat(review.rating)}{'☆'.repeat(5 - review.rating)}</span>
                            </p>
                            {review.text && <p>{review.text}</p>}
                            <small>Оставлен: {review.created_at ? new Date(review.created_at).toLocaleDateString() : 'Дата неизвестна'}</small>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}

export default BookDetailPage;