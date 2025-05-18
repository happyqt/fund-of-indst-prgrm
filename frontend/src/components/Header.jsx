import React from 'react';
import {Link, useNavigate} from 'react-router-dom';
import {useAuth} from '../context/AuthContext';
import './Header.css';

function Header() {
    const {isAuthenticated, user, logout, isAdmin} = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <header className="app-header">
            <Link to="/" className="logo-link"><h1>BookSwap</h1></Link>
            <nav>
                <ul className="nav-links">
                    <li><Link to="/books">Все книги</Link></li>
                    {isAuthenticated ? (
                        <>
                            <li><Link to="/my-books">Мои книги</Link></li>
                            <li><Link to="/add-book">Добавить книгу</Link></li>
                            <li><Link to="/exchanges">Мои обмены</Link></li>
                            {isAdmin && (
                                <>
                                    <li><Link to="/admin/stats">Статистика</Link></li>
                                    <li><Link to="/admin/books">Все книги (Админ)</Link></li>
                                    <li><Link to="/admin/users">Все пользователи (Админ)</Link></li>
                                </>
                            )}
                            <li>
                                <button onClick={handleLogout} className="nav-button">
                                    Выйти ({user?.username})
                                </button>
                            </li>
                        </>
                    ) : (
                        <>
                            <li><Link to="/login">Войти</Link></li>
                            <li><Link to="/register">Регистрация</Link></li>
                        </>
                    )}
                </ul>
            </nav>
        </header>
    );
}

export default Header;