import React, {useState, useEffect} from 'react';
import {useAuth} from '../context/AuthContext.jsx';
import '../pages/Form.css';

function EditBookForm({book, onSave, onCancel}) {
    const [title, setTitle] = useState(book.title);
    const [author, setAuthor] = useState(book.author);
    const [description, setDescription] = useState(book.description || '');
    const [isAvailable, setIsAvailable] = useState(book.is_available);

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [successMessage, setSuccessMessage] = useState(null);

    const {getAuthHeader} = useAuth();

    useEffect(() => {
        setError(null);
        setSuccessMessage(null);
    }, [book.id]);


    const handleSubmit = async (event) => {
        event.preventDefault();

        setError(null);
        setSuccessMessage(null);
        setLoading(true);

        const updatedBookData = {
            title: title,
            author: author,
            description: description || null,
            is_available: isAvailable,
        };

        try {
            const response = await fetch(`/api/books/${book.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': getAuthHeader(),
                },
                body: JSON.stringify(updatedBookData),
            });

            const data = await response.json();

            if (response.ok) {
                setSuccessMessage('Книга успешно обновлена!');
                onSave(data);
            } else {
                setError(data.message || data.error || `Ошибка обновления: ${response.status}`);
                onCancel();
            }
        } catch (err) {
            console.error("Failed to update book:", err);
            setError('Произошла ошибка при обновлении книги. Попробуйте снова.');
            onCancel();
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="form-container"
             style={{marginTop: '1rem', marginBottom: '1rem', padding: '1rem', backgroundColor: '#eef'}}>
            <h4>Редактирование книги "{book.title}"</h4>
            <form onSubmit={handleSubmit}>
                <div>
                    <label htmlFor={`title-${book.id}`}>Название:</label>
                    <input
                        type="text"
                        id={`title-${book.id}`}
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        required
                        disabled={loading}
                    />
                </div>
                <div>
                    <label htmlFor={`author-${book.id}`}>Автор:</label>
                    <input
                        type="text"
                        id={`author-${book.id}`}
                        value={author}
                        onChange={(e) => setAuthor(e.target.value)}
                        required
                        disabled={loading}
                    />
                </div>
                <div>
                    <label htmlFor={`description-${book.id}`}>Описание:</label>
                    <textarea
                        id={`description-${book.id}`}
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        disabled={loading}
                        rows="3"
                    ></textarea>
                </div>
                <div>
                    <label htmlFor={`isAvailable-${book.id}`}>Доступна для обмена:</label>
                    <input
                        type="checkbox"
                        id={`isAvailable-${book.id}`}
                        checked={isAvailable}
                        onChange={(e) => setIsAvailable(e.target.checked)}
                        disabled={loading}
                        style={{marginLeft: '0.5rem'}}
                    />
                </div>


                {error && <p className="error-message">{error}</p>}
                {successMessage && <p className="success-message">{successMessage}</p>}

                <div style={{display: 'flex', justifyContent: 'space-between', gap: '10px'}}>
                    <button type="submit" disabled={loading} style={{flexGrow: 1}}>
                        {loading ? 'Сохранение...' : 'Сохранить изменения'}
                    </button>
                    <button
                        type="button"
                        onClick={onCancel}
                        disabled={loading}
                        style={{backgroundColor: '#6c757d', flexGrow: 1}}
                    >
                        Отмена
                    </button>
                </div>
            </form>
        </div>
    );
}

export default EditBookForm;