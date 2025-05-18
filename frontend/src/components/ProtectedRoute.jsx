import React from 'react';
import {Navigate} from 'react-router-dom';
import {useAuth} from '../context/AuthContext';

// Защищает маршрут, требующий аутентификации
function ProtectedRoute({children}) {
    const {isAuthenticated, isLoading} = useAuth();

    if (isLoading) {
        return null;
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" replace/>;
    }

    return children;
}

function AdminProtectedRoute({children}) {
    const {isAuthenticated, isAdmin, isLoading} = useAuth();

    if (isLoading) {
        return null;
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" replace/>;
    }

    if (!isAdmin) {
        return <div>Доступ запрещен. У вас нет прав администратора.</div>;
    }

    return children;
}


export {ProtectedRoute, AdminProtectedRoute};