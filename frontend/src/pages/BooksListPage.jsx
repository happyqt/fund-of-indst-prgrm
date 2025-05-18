import React, {useState, useEffect} from 'react';

function BooksListPage() {
    const [books, setBooks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const mockBooks = [
            {id: 1, title: "Книга 1", author: "Автор 1", owner_id: 1, is_available: true},
            {id: 2, title: "Книга 2", author: "Автор 2", owner_id: 2, is_available: true},
            {id: 3, title: "Книга 3", author: "Автор 1", owner_id: 1, is_available: false},
        ];
        setBooks(mockBooks.filter(book => book.is_available));
        setLoading(false);
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
                            <strong>{book.title}</strong> - <em>{book.author}</em>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}

export default BooksListPage;