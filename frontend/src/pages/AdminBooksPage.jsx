import React, {useState, useEffect} from 'react';
import {useAuth} from '../context/AuthContext';

function AdminBooksPage() {
    const [allBooks, setAllBooks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const {isLoading: authLoading, isAdmin, getAuthHeader} = useAuth();

    useEffect(() => {
        if (authLoading) {
            return;
        }


        const fetchAllBooks = async () => {
            setLoading(true);
            setError(null);

            try {
                const response = await fetch('/api/admin/books', {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': getAuthHeader(),
                    },
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.message || `Ошибка загрузки всех книг: ${response.status}`);
                }

                const data = await response.json();
                setAllBooks(data);
            } catch (err) {
                console.error("Failed to fetch all books for admin:", err);
                setError('Не удалось загрузить список всех книг. Попробуйте позже.'); // Более дружелюбное сообщение
            } finally {
                setLoading(false);
            }
        };

        fetchAllBooks();

    }, [authLoading, isAdmin]);

    if (authLoading || loading) {
        return <p>Загрузка всех книг (Админ)...</p>;
    }

    if (!isAdmin) {
        return null;
    }


    if (error) {
        return <p className="error-message">Ошибка при загрузке всех книг: {error}</p>;
    }


    return (
        <div>
            <h2>Все книги в системе (Админ)</h2>
            {allBooks.length === 0 ? (
                <p>В системе пока нет книг.</p>
            ) : (
                <ul>
                    {allBooks.map(book => (
                        <li key={book.id}>
                            <strong>{book.title}</strong> - <em>{book.author}</em> (Владелец ID: {book.owner_id},
                            Статус: {book.is_available ? 'Доступна' : 'Недоступна'})
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}

export default AdminBooksPage;