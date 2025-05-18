import React from 'react';
import {useAuth} from '../context/AuthContext';

function AdminBooksPage() {
    const {isAdmin} = useAuth();

    if (!isAdmin) {
        return <div>Доступ запрещен.</div>;
    }
    return (
        <div>
            <h2>Все книги (Админ)</h2>
            <p>Список всех книг будет здесь.</p>
        </div>
    );
}

export default AdminBooksPage;