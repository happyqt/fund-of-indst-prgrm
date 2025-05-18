import React, {useState, useEffect, useCallback} from 'react';
import {useAuth} from '../context/AuthContext';
import {Link} from 'react-router-dom';
import './MyExchangesPage.css';

function MyExchangesPage() {
    const [exchanges, setExchanges] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [actionError, setActionError] = useState(null);
    const [actionSuccess, setActionSuccess] = useState(null);
    const [filterType, setFilterType] = useState('all');
    const [booksDetails, setBooksDetails] = useState({});

    const {user, getAuthHeader, isLoading: authLoading} = useAuth();

    const fetchBookDetailsForExchanges = useCallback(async (fetchedExchanges) => {
        if (!fetchedExchanges || fetchedExchanges.length === 0) {
            return {};
        }

        const bookIds = new Set();
        fetchedExchanges.forEach(ex => {
            bookIds.add(ex.proposed_book_id);
            bookIds.add(ex.requested_book_id);
        });

        const newBooksDetails = {...booksDetails};
        let fetchedNewDetails = false;

        for (const bookId of Array.from(bookIds)) {
            if (!newBooksDetails[bookId]) {
                try {
                    const response = await fetch(`/api/books/${bookId}`, {
                        headers: {
                            'Authorization': getAuthHeader(),
                        }
                    });
                    if (response.ok) {
                        const bookData = await response.json();
                        newBooksDetails[bookId] = bookData;
                        fetchedNewDetails = true;
                    } else {
                        console.warn(`Failed to fetch details for book ${bookId}`);
                        newBooksDetails[bookId] = {title: 'Неизвестная книга', author: 'Неизвестен'};
                    }
                } catch (err) {
                    console.error(`Error fetching book ${bookId}:`, err);
                    newBooksDetails[bookId] = {title: 'Ошибка загрузки', author: ''};
                }
            }
        }
        if (fetchedNewDetails) {
            setBooksDetails(newBooksDetails);
        }
        return newBooksDetails;
    }, [getAuthHeader, booksDetails]);


    const fetchExchanges = useCallback(async () => {
        if (authLoading || !user) return;

        setLoading(true);
        setError(null);
        setActionError(null);
        setActionSuccess(null);

        try {
            const response = await fetch(`/api/exchanges?type=${filterType}`, {
                headers: {
                    'Authorization': getAuthHeader(),
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.message || `Ошибка загрузки обменов: ${response.status}`);
            }

            const data = await response.json();
            setExchanges(data);
            await fetchBookDetailsForExchanges(data);

        } catch (err) {
            console.error("Failed to fetch exchanges:", err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [filterType, getAuthHeader, authLoading, user, fetchBookDetailsForExchanges]);

    useEffect(() => {
        fetchExchanges();
    }, [fetchExchanges]);

    const handleExchangeAction = async (exchangeId, action) => {
        setActionError(null);
        setActionSuccess(null);
        setLoading(true);

        try {
            const response = await fetch(`/api/exchanges/${exchangeId}/${action}`, {
                method: 'POST',
                headers: {
                    'Authorization': getAuthHeader(),
                    'Content-Type': 'application/json',
                },
            });
            const data = await response.json();
            if (response.ok) {
                setActionSuccess(`Обмен успешно ${action === 'accept' ? 'принят' : (action === 'reject' ? 'отклонен' : 'отменен')}.`);
                fetchExchanges();
            } else {
                setActionError(data.message || `Ошибка выполнения действия: ${response.status}`);
            }
        } catch (err) {
            console.error(`Failed to ${action} exchange:`, err);
            setActionError('Произошла ошибка. Попробуйте снова.');
        } finally {
            setLoading(false);
        }
    };

    const getBookDisplay = (bookId) => {
        const book = booksDetails[bookId];
        if (!book) return `Книга ID: ${bookId} (загрузка...)`;
        return <><strong><Link to={`/books/${bookId}`} className="book-title-link">{book.title || "Без названия"}</Link></strong> ({book.author || "Без автора"})</>;
    };


    if (authLoading) {
        return <p>Загрузка информации о пользователе...</p>;
    }

    if (loading && exchanges.length === 0) {
        return <p>Загрузка ваших обменов...</p>;
    }

    if (error) {
        return <p className="error-message">Ошибка: {error}</p>;
    }

    return (
        <div className="my-exchanges-container">
            <h2>Мои обмены</h2>

            <div className="filter-buttons">
                <button onClick={() => setFilterType('all')}
                        className={filterType === 'all' ? 'active' : ''}>Все
                </button>
                <button onClick={() => setFilterType('sent')}
                        className={filterType === 'sent' ? 'active' : ''}>Отправленные
                </button>
                <button onClick={() => setFilterType('received')}
                        className={filterType === 'received' ? 'active' : ''}>Полученные
                </button>
            </div>

            {actionError && <p className="error-message">{actionError}</p>}
            {actionSuccess && <p className="success-message">{actionSuccess}</p>}

            {loading && <p>Обновление списка обменов...</p>}

            {exchanges.length === 0 && !loading ? (
                <p>У вас
                    нет {filterType === 'sent' ? 'отправленных' : filterType === 'received' ? 'полученных' : ''} предложений
                    обмена.</p>
            ) : (
                <ul className="exchanges-list">
                    {exchanges.map(exchange => {
                        const isProposer = exchange.proposing_user_id === user.id;
                        const isReceiver = exchange.receiving_user_id === user.id;

                        return (
                            <li key={exchange.id} className={`exchange-item status-${exchange.status}`}>
                                <div className="exchange-details">
                                    <p><strong>ID Обмена:</strong> {exchange.id}</p>
                                    <p>
                                        {isProposer ? "Вы предлагаете:" : `Пользователь ${exchange.proposing_user_id} предлагает:`} {getBookDisplay(exchange.proposed_book_id)}
                                    </p>
                                    <p>
                                        {isReceiver ? "Вам предлагают за:" : `Пользователю ${exchange.receiving_user_id} за:`} {getBookDisplay(exchange.requested_book_id)}
                                    </p>
                                    <p><strong>Статус:</strong> <span
                                        className="status-text">{exchange.status}</span></p>
                                    {exchange.exchange_location &&
                                        <p><strong>Место обмена:</strong> {exchange.exchange_location}</p>}
                                    <p>
                                        <small>Создан: {new Date(exchange.created_at).toLocaleString()}</small>
                                        {exchange.updated_at &&
                                            <small> |
                                                Обновлен: {new Date(exchange.updated_at).toLocaleString()}</small>}
                                    </p>
                                </div>

                                {exchange.status === 'pending' && (
                                    <div className="exchange-actions">
                                        {isReceiver && (
                                            <>
                                                <button onClick={() => handleExchangeAction(exchange.id, 'accept')}
                                                        className="action-button accept">Принять
                                                </button>
                                                <button onClick={() => handleExchangeAction(exchange.id, 'reject')}
                                                        className="action-button reject">Отклонить
                                                </button>
                                            </>
                                        )}
                                        {isProposer && (
                                            <button onClick={() => handleExchangeAction(exchange.id, 'cancel')}
                                                    className="action-button cancel">Отменить предложение
                                            </button>
                                        )}
                                    </div>
                                )}
                                {exchange.status === 'accepted' && (
                                    <p className="info-message">Обмен состоялся. Книги изменили владельцев и стали
                                        недоступны.</p>
                                )}
                            </li>
                        );
                    })}
                </ul>
            )}
        </div>
    );
}

export default MyExchangesPage;