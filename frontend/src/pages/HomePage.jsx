import React, {useState, useEffect} from 'react';
import {Link} from 'react-router-dom';
import {useAuth} from '../context/AuthContext';
import './HomePage.css';

function HomePage() {
    const {isAuthenticated} = useAuth();
    const [stats, setStats] = useState(null);

    useEffect(() => {
        // Загружаем кол-во книг для отображения на главной
        fetch('/api/books?per_page=1')
            .then(r => r.ok ? r.json() : null)
            .then(data => {
                if (data && !Array.isArray(data)) {
                    setStats({total_books: data.total});
                }
            })
            .catch(() => {});
    }, []);

    return (
        <div className="home-page">
            <section className="hero">
                <div className="hero-content">
                    <div className="hero-badge">Платформа обмена книгами</div>
                    <h1 className="hero-title">
                        Найдите книгу,<br />поделитесь своей
                    </h1>
                    <p className="hero-subtitle">
                        BookSwap — сервис для обмена книгами в вашем кампусе,
                        школе или офисе. Добавьте свои книги, найдите нужные
                        и договоритесь об обмене с другими читателями.
                    </p>
                    <div className="hero-actions">
                        <Link to="/books" className="btn-hero-primary">
                            Смотреть книги
                        </Link>
                        {!isAuthenticated && (
                            <Link to="/register" className="btn-hero-secondary">
                                Зарегистрироваться
                            </Link>
                        )}
                        {isAuthenticated && (
                            <Link to="/add-book" className="btn-hero-secondary">
                                Добавить книгу
                            </Link>
                        )}
                    </div>
                    {stats && (
                        <p className="hero-stat">
                            📖 Сейчас доступно <strong>{stats.total_books}</strong> книг для обмена
                        </p>
                    )}
                </div>
            </section>

            <section className="features">
                <div className="feature-card">
                    <span className="feature-icon">🔍</span>
                    <h3>Найдите книгу</h3>
                    <p>Ищите по названию или автору среди всех доступных книг в системе.</p>
                </div>
                <div className="feature-card">
                    <span className="feature-icon">🤝</span>
                    <h3>Предложите обмен</h3>
                    <p>Укажите свою книгу и место встречи — владелец получит ваше предложение.</p>
                </div>
                <div className="feature-card">
                    <span className="feature-icon">⭐</span>
                    <h3>Оставьте отзыв</h3>
                    <p>Делитесь впечатлениями о книгах с рейтингом и комментарием.</p>
                </div>
            </section>
        </div>
    );
}

export default HomePage;