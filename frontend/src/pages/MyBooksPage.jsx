import React, {useState, useEffect} from 'react';
import {useAuth} from '../context/AuthContext';
import {useNavigate} from 'react-router-dom';
import EditBookForm from '../components/EditBookForm'; // импорт формы редактирования
import './Form.css';
import { Link } from 'react-router-dom';

function MyBooksPage() {
    const [myBooks, setMyBooks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [editingBookId, setEditingBookId] = useState(null); // Состояние для отслеживания, какая книга редактируется

    const {isAuthenticated, isLoading: authLoading, getAuthHeader} = useAuth();
    const navigate = useNavigate();

    const fetchMyBooks = async () => {
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
            setMyBooks(data); // Устанавливаем полученный список книг
        } catch (err) {
            console.error("Failed to fetch my books:", err);
            setError('Не удалось загрузить список ваших книг. Попробуйте позже.');
        } finally {
            setLoading(false);
        }
    };


    useEffect(() => {
        if (authLoading) {
            return;
        }

        if (!isAuthenticated) {
            navigate('/login');
            return;
        }

        fetchMyBooks();

    }, [isAuthenticated, authLoading]); // Зависимости эффекта


    const handleBookUpdated = (updatedBook) => {
        setMyBooks(prevBooks => prevBooks.map(book =>
            book.id === updatedBook.id ? updatedBook : book
        ));
        setEditingBookId(null);
    };

    const handleCancelEdit = () => {
        setEditingBookId(null);
    };


    if (authLoading || loading) {
        return <p>Загрузка ваших книг...</p>;
    }

    if (error) {
        return <p className="error-message">Ошибка при загрузке ваших книг: {error}</p>;
    }


    return (
        <div>
            <h2>Мои книги</h2>
            {myBooks.length === 0 ? (
                <p>У вас пока нет добавленных книг.</p>
            ) : (
                <ul>
                    {myBooks.map(book => (
                         <li key={book.id}>
                            {editingBookId === book.id ? (
                                <EditBookForm
                                    book={book}
                                    onSave={handleBookUpdated}
                                    onCancel={handleCancelEdit}
                                />
                            ) : (
                                <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                                    <div>
                                        <Link to={`/books/${book.id}`} className="book-title-link">
                                             <strong>{book.title}</strong>
                                        </Link>
                                         - <em>{book.author}</em> ({book.is_available ? 'Доступна' : 'Недоступна'})
                                    </div>
                                    <div>
                                        <button onClick={() => setEditingBookId(book.id)} style={{marginRight: '10px'}}>
                                            Редактировать
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