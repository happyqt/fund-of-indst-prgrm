import React, {useState, useEffect} from 'react';
import {useNavigate, useLocation} from 'react-router-dom';
import {useAuth} from '../context/AuthContext';
import './Form.css';

function LoginPage() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const {login, error: authError, setError: setAuthError, isAuthenticated} = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    useEffect(() => {
        if (isAuthenticated) {
            const home = "/";
            navigate(home, {replace: true});
        }
    }, [isAuthenticated, navigate, location.state]);

    // Сбрасываем ошибку при размонтировании или изменении username/password
    useEffect(() => {
        return () => {
            setAuthError(null);
        };
    }, [setAuthError, username, password]);


    const handleSubmit = async (event) => {
        event.preventDefault();
        setAuthError(null);
        const success = await login(username, password);
        if (success) {
            const home = "/";
            navigate(home, {replace: true});
        }

    };

    return (
        <div className="form-container">
            <h2>Вход</h2>
            <form onSubmit={handleSubmit}>
                <div>
                    <label htmlFor="username">Имя пользователя:</label>
                    <input
                        type="text"
                        id="username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        required
                    />
                </div>
                <div>
                    <label htmlFor="password">Пароль:</label>
                    <input
                        type="password"
                        id="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                </div>
                {authError && <p className="error-message">{authError}</p>}
                <button type="submit">Войти</button>
            </form>
        </div>
    );
}

export default LoginPage;