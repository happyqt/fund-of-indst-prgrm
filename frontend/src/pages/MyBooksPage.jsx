import React, {useState, useEffect, useCallback} from 'react';
import {useAuth} from '../context/AuthContext';
import {useNavigate, Link} from 'react-router-dom';
import EditBookForm from '../components/EditBookForm';
import './Form.css';

function MyBooksPage() {
    const [myBooks, setMyBooks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [editingBookId, setEditingBookId] = useState(null);
    const [actionMessage, setActionMessage] = useState(null);

    const {isAuthenticated, isLoading: authLoading, getAuthHeader} = useAuth();
    const navigate = useNavigate();

    const fetchMyBooks = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch('/api/users/me/books', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': getAuthHeader(),
                },
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || `Ошибка загрузки ваших книг: ${response.status}`);
            }

            const data = await response.json();
            setMyBooks(data);
        } catch (err) {
            console.error("Failed to fetch my books:", err);
            setError('Не удалось загрузить список ваших книг. Попробуйте позже.');
        } finally {
            setLoading(false);
        }
    }, [getAuthHeader]);

    useEffect(() => {
        if (authLoading) return;
        if (!isAuthenticated) {
            navigate('/login');
            return;
        }
        fetchMyBooks();
    }, [isAuthenticated, authLoading, fetchMyBooks]);

    const handleBookUpdated = (updatedBook) => {
        setMyBooks(prevBooks => prevBooks.map(book =>
            book.id === updatedBook.id ? updatedBook : book
        ));
        setEditingBookId(null);
    };

    const handleCancelEdit = () => {
        setEditingBookId(null);
    };

    const handleToggleAvailability = async (book) => {
        setActionMessage(null);
        const newAvailability = !book.is_available;
        try {
            const response = await fetch(`/api/books/${book.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': getAuthHeader(),
                },
                body: JSON.stringify({is_available: newAvailability}),
            });
            if (!response.ok) {
                const errData = await response.json();
                setActionMessage({type: 'error', text: errData.message || 'Ошибка при изменении доступности.'});
                return;
            }
            const updatedBook = await response.json();
            setMyBooks(prevBooks => prevBooks.map(b => b.id === updatedBook.id ? updatedBook : b));
            setActionMessage({
                type: 'success',
                text: `Книга «${updatedBook.title}» теперь ${updatedBook.is_available ? 'доступна' : 'недоступна'} для обмена.`
            });
        } catch (err) {
            setActionMessage({type: 'error', text: 'Произошла ошибка. Попробуйте снова.'});
        }
    };

    const handleDeleteBook = async (book) => {
        if (!window.confirm(`Удалить книгу «${book.title}»? Это действие нельзя отменить.`)) return;
        setActionMessage(null);
        try {
            const response = await fetch(`/api/books/${book.id}`, {
                method: 'DELETE',
                headers: {'Authorization': getAuthHeader()},
            });
            const data = await response.json();
            if (response.ok) {
                setMyBooks(prevBooks => prevBooks.filter(b => b.id !== book.id));
                setActionMessage({type: 'success', text: `Книга «${book.title}» удалена.`});
            } else {
                setActionMessage({type: 'error', text: data.message || 'Не удалось удалить книгу.'});
            }
        } catch (err) {
            setActionMessage({type: 'error', text: 'Произошла ошибка при удалении.'});
        }
    };

    if (authLoading || loading) {
        return <p>Загрузка ваших книг...</p>;
    }

    if (error) {
        return <p className="error-message">Ошибка при загрузке ваших книг: {error}</p>;
    }

    return (
        <div className="my-books-container">
            <h2>Мои книги</h2>

            {actionMessage && (
                <p className={actionMessage.type === 'error' ? 'error-message' : 'success-message'}>
                    {actionMessage.text}
                </p>
            )}

            {myBooks.length === 0 ? (
                <p>У вас пока нет добавленных книг. <Link to="/add-book">Добавить книгу →</Link></p>
            ) : (
                <ul className="my-books-list">
                    {myBooks.map(book => (
                        <li key={book.id} className="my-book-item">
                            {editingBookId === book.id ? (
                                <EditBookForm
                                    book={book}
                                    onSave={handleBookUpdated}
                                    onCancel={handleCancelEdit}
                                />
                            ) : (
                                <div className="my-book-row">
                                    <div className="my-book-info">
                                        <Link to={`/books/${book.id}`} className="book-title-link">
                                            <strong>{book.title}</strong>
                                        </Link>
                                        <span> — <em>{book.author}</em></span>
                                        <span className={book.is_available ? 'status-available' : 'status-unavailable'}>
                                            {book.is_available ? ' · Доступна' : ' · Недоступна'}
                                        </span>
                                    </div>
                                    <div className="my-book-actions">
                                        <button
                                            onClick={() => setEditingBookId(book.id)}
                                            className="btn-secondary"
                                        >
                                            Редактировать
                                        </button>
                                        <button
                                            onClick={() => handleToggleAvailability(book)}
                                            className={book.is_available ? 'btn-warning' : 'btn-success'}
                                        >
                                            {book.is_available ? 'Скрыть' : 'Сделать доступной'}
                                        </button>
                                        <button
                                            onClick={() => handleDeleteBook(book)}
                                            className="btn-danger"
                                        >
                                            Удалить
                                        </button>
                                    </div>
                                </div>
                            )}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}

export default MyBooksPage;