import React from 'react';
import {Link} from 'react-router-dom';
import './Header.css';

function Header() {
    return (
        <header className="app-header">
            <nav>
                <ul className="nav-links">
                    <li><Link to="/">Главная</Link></li>
                    <li><Link to="/books">Все книги</Link></li>
                    <li><Link to="/login">Войти</Link></li>
                    <li><Link to="/register">Регистрация</Link></li>
                </ul>
            </nav>
        </header>
    );
}

export default Header;