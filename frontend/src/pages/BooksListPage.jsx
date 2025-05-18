import React, {useState, useEffect} from 'react';
import {useAuth} from '../context/AuthContext';

function BooksListPage() {
    const [books, setBooks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchBooks = async () => {
            try {
                const response = await fetch('/api/books', {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                });

                if (!response.ok) {
                    // парсим ошибку
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
        };

        fetchBooks();
    }, []);


    if (loading) {
        return <p>Загрузка книг...</p>;
    }

    if (error) {
        return <p>Ошибка при загрузке книг: {error}</p>;
    }

    return (
        <div>
            <h2>Доступные книги для обмена</h2>
            {books.length === 0 ? (
                <p>Нет доступных книг для обмена.</p>
            ) : (
                <ul>
                    {books.map(book => (
                        <li key={book.id}>
                            <strong>{book.title}</strong> - <em>{book.author}</em> (Владелец: {book.owner_id})
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}

export default BooksListPage;
