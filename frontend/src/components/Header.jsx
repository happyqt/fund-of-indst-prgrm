import React from 'react';
import {NavLink, useNavigate} from 'react-router-dom';
import {useAuth} from '../context/AuthContext';
import './Header.css';

function Header() {
    const {isAuthenticated, user, logout, isAdmin} = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const navClass = ({isActive}) => isActive ? 'active' : '';

    return (
        <header className="app-header">
            <NavLink to="/" className="logo-link">
                <h1>📚 BookSwap</h1>
            </NavLink>
            <nav>
                <ul className="nav-links">
                    <li><NavLink to="/books" className={navClass}>Все книги</NavLink></li>
                    {isAuthenticated ? (
                        <>
                            <li><NavLink to="/my-books" className={navClass}>Мои книги</NavLink></li>
                            <li><NavLink to="/add-book" className={navClass}>Добавить</NavLink></li>
                            <li><NavLink to="/exchanges" className={navClass}>Обмены</NavLink></li>
                            {isAdmin && (
                                <>
                                    <li><NavLink to="/admin/stats" className={navClass}>Статистика</NavLink></li>
                                    <li><NavLink to="/admin/books" className={navClass}>Все книги (А)</NavLink></li>
                                    <li><NavLink to="/admin/users" className={navClass}>Пользователи (А)</NavLink></li>
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
                            <li><NavLink to="/login" className={navClass}>Войти</NavLink></li>
                            <li><NavLink to="/register" className={navClass}>Регистрация</NavLink></li>
                        </>
                    )}
                </ul>
            </nav>
        </header>
    );
}

export default Header;