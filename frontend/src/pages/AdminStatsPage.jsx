import React from 'react';
import {useAuth} from '../context/AuthContext';

function AdminStatsPage() {
    const {isAdmin} = useAuth();

    if (!isAdmin) {
        return <div>Доступ запрещен.</div>;
    }

    return (
        <div>
            <h2>Статистика обменов (Админ)</h2>
            <p>Статистика будет здесь.</p>
        </div>
    );
}

export default AdminStatsPage;