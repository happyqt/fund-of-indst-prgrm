import React, {useState, useEffect} from 'react';
import {useAuth} from '../context/AuthContext';

function AdminUsersPage() {
    const [allUsers, setAllUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const {isLoading: authLoading, isAdmin, getAuthHeader} = useAuth();

    useEffect(() => {
        if (authLoading) {
            return;
        }

        const fetchAllUsers = async () => {
            setLoading(true);
            setError(null);

            try {
                const response = await fetch('/api/admin/users', {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': getAuthHeader(),
                    },
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.message || `Ошибка загрузки всех пользователей: ${response.status}`);
                }

                const data = await response.json();
                setAllUsers(data);
            } catch (err) {
                console.error("Failed to fetch all users for admin:", err);
                setError('Не удалось загрузить список всех пользователей. Попробуйте позже.'); // Более дружелюбное сообщение
            } finally {
                setLoading(false); // Загрузка завершена
            }
        };

        fetchAllUsers();

    }, [authLoading, isAdmin]);
    if (authLoading || loading) {
        return <p>Загрузка всех пользователей (Админ)...</p>;
    }


    if (error) {
        return <p className="error-message">Ошибка при загрузке всех пользователей: {error}</p>;
    }

    return (
        <div>
            <h2>Все пользователи в системе (Админ)</h2>
            {allUsers.length === 0 ? (
                <p>В системе пока нет пользователей (кроме, возможно, вас).</p>
            ) : (
                <ul>
                    {allUsers.map(user => (
                        <li key={user.id}>
                            <strong>ID: {user.id}</strong> - {user.username} ({user.email})
                            - {user.is_admin ? 'Администратор' : 'Пользователь'}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}

export default AdminUsersPage;