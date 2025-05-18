import React from 'react';
import {useAuth} from '../context/AuthContext';

function AdminUsersPage() {
    const {isAdmin} = useAuth();

    if (!isAdmin) {
        return <div>Доступ запрещен.</div>;
    }
    return (
        <div>
            <h2>Все пользователи (Админ)</h2>
            <p>Список всех пользователей будет здесь.</p>
        </div>
    );
}

export default AdminUsersPage;