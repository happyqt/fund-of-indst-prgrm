import React, {useState} from 'react';
import {useAuth} from '../context/AuthContext';
import {useNavigate} from 'react-router-dom';
import './Form.css';

function AddBookPage() {
    const [title, setTitle] = useState('');
    const [author, setAuthor] = useState('');
    const [description, setDescription] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [successMessage, setSuccessMessage] = useState(null);

    const {isAuthenticated, isLoading, getAuthHeader} = useAuth();
    const navigate = useNavigate();


    const handleSubmit = async (event) => {
        event.preventDefault();

        setError(null);
        setSuccessMessage(null);
        setLoading(true);

        const bookData = {
            title,
            author,
            description: description || null,
        };

        try {
            const response = await fetch('/api/books', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': getAuthHeader(),
                },
                body: JSON.stringify(bookData),
            });

            const data = await response.json();

            if (response.ok) {
                setSuccessMessage('Книга успешно добавлена!');
                setTitle('');
                setAuthor('');
                setDescription('');
            } else {
                setError(data.message || data.error || `Ошибка: ${response.status}`);
            }
        } catch (err) {
            console.error("Failed to add book:", err);
            setError('Произошла ошибка при добавлении книги. Попробуйте снова.');
        } finally {
            setLoading(false);
        }
    };

    if (isLoading) {
        return <p>Загрузка...</p>;
    }

    return (
        <div className="form-container">
            <h2>Добавить новую книгу</h2>
            <form onSubmit={handleSubmit}>
                <div>
                    <label htmlFor="title">Название книги:</label>
                    <input
                        type="text"
                        id="title"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        required
                        disabled={loading}
                    />
                </div>
                <div>
                    <label htmlFor="author">Автор:</label>
                    <input
                        type="text"
                        id="author"
                        value={author}
                        onChange={(e) => setAuthor(e.target.value)}
                        required
                        disabled={loading}
                    />
                </div>
                <div>
                    <label htmlFor="description">Описание (необязательно):</label>
                    <textarea
                        id="description"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        disabled={loading}
                        rows="4"
                    ></textarea>
                </div>

                {error && <p className="error-message">{error}</p>}
                {successMessage &&
                    <p className="success-message">{successMessage}</p>}


                <button type="submit" disabled={loading}>
                    {loading ? 'Добавление...' : 'Добавить книгу'}
                </button>
            </form>
        </div>
    );
}

export default AddBookPage;