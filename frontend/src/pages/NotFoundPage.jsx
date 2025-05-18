import React from 'react';
import {Link} from 'react-router-dom';

function NotFoundPage() {
    return (
        <div>
            <h1>404 - Страница не найдена</h1>
            <p>Извините, запрашиваемая вами страница не существует.</p>
            <Link to="/">Вернуться на главную</Link>
        </div>
    );
}

export default NotFoundPage;