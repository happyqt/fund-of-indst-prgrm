import React, {useState, useEffect, useCallback} from 'react';
import {Link} from 'react-router-dom';
import {useAuth} from '../context/AuthContext';
import './BooksListPage.css';

function BooksListPage() {
    const [books, setBooks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const [inputTitleFilter, setInputTitleFilter] = useState('');
    const [inputAuthorFilter, setInputAuthorFilter] = useState('');

    const [activeTitleFilter, setActiveTitleFilter] = useState('');
    const [activeAuthorFilter, setActiveAuthorFilter] = useState('');

    const fetchBooks = useCallback(async () => {
        setLoading(true);
        setError(null);

        const queryParams = new URLSearchParams();
        if (activeTitleFilter) {
            queryParams.append('title', activeTitleFilter);
        }
        if (activeAuthorFilter) {
            queryParams.append('author', activeAuthorFilter);
        }
        const queryString = queryParams.toString();

        try {
            const response = await fetch(`/api/books${queryString ? `?${queryString}` : ''}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || `Ошибка загрузки книг: ${response.status}`);
            }

            const data = await response.json();
            setBooks(data);
        } catch (err) {
            console.error("Failed to fetch books:", err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [activeTitleFilter, activeAuthorFilter]);

    useEffect(() => {
        fetchBooks();
    }, [fetchBooks]);

    const handleApplyFilters = (event) => {
        event.preventDefault();
        setActiveTitleFilter(inputTitleFilter);
        setActiveAuthorFilter(inputAuthorFilter);
    };

    const handleClearFilters = () => {
        setInputTitleFilter('');
        setInputAuthorFilter('');
        if (activeTitleFilter !== '' || activeAuthorFilter !== '') {
            setActiveTitleFilter('');
            setActiveAuthorFilter('');
        }
    };


    if (loading && books.length === 0) {
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
                        value={inputTitleFilter} // Привязываем к inputTitleFilter
                        onChange={(e) => setInputTitleFilter(e.target.value)}
                        className="filter-input"
                    />
                </div>
                <div className="filter-group">
                    <input
                        type="text"
                        placeholder="Фильтр по автору..."
                        value={inputAuthorFilter} // Привязываем к inputAuthorFilter
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

            {loading && <p>Обновление списка книг...</p>}

            {books.length === 0 && !loading ? (
                <p>Нет доступных книг, соответствующих вашим фильтрам.</p>
            ) : (
                <ul className="books-ul">
                    {books.map(book => (
                        <li key={book.id} className="book-item">
                            <Link to={`/books/${book.id}`} className="book-title-link">
                                <strong>{book.title}</strong>
                            </Link>
                            <span> - <em>{book.author}</em></span>
                            <span className={book.is_available ? 'status-available' : 'status-unavailable'}>
                                ({book.is_available ? 'Доступна' : 'Недоступна'})
                            </span>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}

export default BooksListPage;
