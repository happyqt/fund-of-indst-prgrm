import React, {useState, useEffect, useCallback} from 'react';
import {Link} from 'react-router-dom';
import {useAuth} from '../context/AuthContext';
import './BooksListPage.css';

const PER_PAGE = 12;

function BooksListPage() {
    const [books, setBooks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const [inputTitleFilter, setInputTitleFilter] = useState('');
    const [inputAuthorFilter, setInputAuthorFilter] = useState('');

    const [activeTitleFilter, setActiveTitleFilter] = useState('');
    const [activeAuthorFilter, setActiveAuthorFilter] = useState('');

    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [total, setTotal] = useState(0);

    const {user, isAuthenticated, isLoading: authLoading} = useAuth();
    const [showMyBooks, setShowMyBooks] = useState(true);

    const fetchBooks = useCallback(async () => {
        setLoading(true);
        setError(null);

        const queryParams = new URLSearchParams();
        if (activeTitleFilter) queryParams.append('title', activeTitleFilter);
        if (activeAuthorFilter) queryParams.append('author', activeAuthorFilter);
        queryParams.append('page', page);
        queryParams.append('per_page', PER_PAGE);

        try {
            const response = await fetch(`/api/books?${queryParams.toString()}`, {
                method: 'GET',
                headers: {'Content-Type': 'application/json'},
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || `Ошибка загрузки книг: ${response.status}`);
            }

            const data = await response.json();
            // Поддержка нового формата {books, total, ...}
            if (Array.isArray(data)) {
                setBooks(data);
                setTotalPages(1);
                setTotal(data.length);
            } else {
                setBooks(data.books || []);
                setTotalPages(data.total_pages || 1);
                setTotal(data.total || 0);
            }
        } catch (err) {
            console.error("Failed to fetch books:", err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [activeTitleFilter, activeAuthorFilter, page]);

    useEffect(() => {
        if (!authLoading) {
            fetchBooks();
        }
    }, [fetchBooks, authLoading]);

    const handleApplyFilters = (event) => {
        event.preventDefault();
        setPage(1);
        setActiveTitleFilter(inputTitleFilter);
        setActiveAuthorFilter(inputAuthorFilter);
    };

    const handleClearFilters = () => {
        setInputTitleFilter('');
        setInputAuthorFilter('');
        setPage(1);
        if (activeTitleFilter !== '' || activeAuthorFilter !== '') {
            setActiveTitleFilter('');
            setActiveAuthorFilter('');
        }
    };

    const displayedBooks = isAuthenticated && !showMyBooks
        ? books.filter(book => book.owner_id !== user.id)
        : books;

    if (authLoading || (loading && books.length === 0)) {
        return <p>Загрузка книг...</p>;
    }

    if (error) {
        return <p className="error-message">Ошибка при загрузке книг: {error}</p>;
    }

    return (
        <div className="books-list-container">
            <h2>Доступные книги для обмена</h2>

            <form onSubmit={handleApplyFilters} className="filter-form">
                <div className="filter-group">
                    <input
                        type="text"
                        placeholder="Фильтр по названию..."
                        value={inputTitleFilter}
                        onChange={(e) => setInputTitleFilter(e.target.value)}
                        className="filter-input"
                    />
                </div>
                <div className="filter-group">
                    <input
                        type="text"
                        placeholder="Фильтр по автору..."
                        value={inputAuthorFilter}
                        onChange={(e) => setInputAuthorFilter(e.target.value)}
                        className="filter-input"
                    />
                </div>
                <div className="filter-actions">
                    <button type="submit" className="filter-button apply">Применить фильтры</button>
                    <button type="button" onClick={handleClearFilters} className="filter-button clear">
                        Очистить
                    </button>
                </div>
            </form>

            {isAuthenticated && (
                <div className="show-my-books-toggle">
                    <label htmlFor="showMyBooksCheckbox">
                        <input
                            type="checkbox"
                            id="showMyBooksCheckbox"
                            checked={showMyBooks}
                            onChange={(e) => setShowMyBooks(e.target.checked)}
                        />
                        Показывать мои книги в этом списке
                    </label>
                </div>
            )}

            {loading && <p>Обновление списка книг...</p>}

            {total > 0 && (
                <p className="results-count">
                    Найдено книг: <strong>{total}</strong>
                    {totalPages > 1 && ` (страница ${page} из ${totalPages})`}
                </p>
            )}

            {displayedBooks.length === 0 && !loading ? (
                <p>
                    Нет доступных книг, соответствующих вашим фильтрам
                    {isAuthenticated && !showMyBooks && user ? " (ваши книги скрыты)" : ""}.
                </p>
            ) : (
                <ul className="books-ul">
                    {displayedBooks.map(book => (
                        <li key={book.id} className="book-item">
                            <div>
                                <Link to={`/books/${book.id}`} className="book-title-link">
                                    <strong>{book.title}</strong>
                                </Link>
                                <span> — <em>{book.author}</em></span>
                                {book.owner_username && (
                                    <span className="book-owner"> · {book.owner_username}</span>
                                )}
                                {isAuthenticated && user && book.owner_id === user.id && (
                                    <span className="my-book-indicator"> (Моя книга)</span>
                                )}
                            </div>
                            <span className={book.is_available ? 'status-available' : 'status-unavailable'}>
                                ({book.is_available ? 'Доступна' : 'Недоступна'})
                            </span>
                        </li>
                    ))}
                </ul>
            )}

            {totalPages > 1 && (
                <div className="pagination">
                    <button
                        onClick={() => setPage(p => Math.max(1, p - 1))}
                        disabled={page === 1 || loading}
                        className="page-button"
                    >
                        ← Назад
                    </button>
                    <span className="page-info">Страница {page} из {totalPages}</span>
                    <button
                        onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                        disabled={page === totalPages || loading}
                        className="page-button"
                    >
                        Вперёд →
                    </button>
                </div>
            )}
        </div>
    );
}

export default BooksListPage;
