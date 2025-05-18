import React, {createContext, useState, useContext, useEffect} from 'react';

const AuthContext = createContext(null);

export const AuthProvider = ({children}) => {
    const [user, setUser] = useState(null);
    const [authHeader, setAuthHeader] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    // Загрузка состояния из localStorage при инициализации
    useEffect(() => {
        try {
            const storedUser = localStorage.getItem('user');
            const storedAuthHeader = localStorage.getItem('authHeader');

            if (storedUser && storedAuthHeader) {
                setUser(JSON.parse(storedUser));
                setAuthHeader(storedAuthHeader);
            }
        } catch (e) {
            console.error("Failed to load auth state from localStorage", e);
            localStorage.removeItem('user');
            localStorage.removeItem('authHeader');
        }
        setIsLoading(false);
    }, []);

    const login = async (username, password) => {
        setIsLoading(true);
        setError(null);

        const credentials = btoa(`${username}:${password}`); // base64 encode
        const basicAuthHeader = `Basic ${credentials}`;

        try {
            const response = await fetch('/api/users/me', {
                method: 'GET',
                headers: {
                    'Authorization': basicAuthHeader,
                },
            });

            if (response.ok) {
                const userData = await response.json();
                setUser(userData);
                setAuthHeader(basicAuthHeader);
                localStorage.setItem('user', JSON.stringify(userData));
                localStorage.setItem('authHeader', basicAuthHeader);
                setIsLoading(false);
                return true;
            } else {
                const errorData = await response.json();
                setError(errorData.message || `Ошибка входа: ${response.status}`);
                setUser(null);
                setAuthHeader(null);
                localStorage.removeItem('user');
                localStorage.removeItem('authHeader');
                setIsLoading(false);
                return false;
            }
        } catch (err) {
            console.error("Login error:", err);
            setError('Произошла ошибка при попытке входа. Проверьте ваше соединение.');
            setUser(null);
            setAuthHeader(null);
            localStorage.removeItem('user');
            localStorage.removeItem('authHeader');
            setIsLoading(false);
            return false;
        }
    };

    const logout = () => {
        setUser(null);
        setAuthHeader(null);
        localStorage.removeItem('user');
        localStorage.removeItem('authHeader');
    };

    const getAuthHeader = () => {
        return authHeader;
    };

    const isAdmin = user ? user.is_admin : false;

    const value = {
        user,
        authHeader,
        isAuthenticated: !!user,
        isAdmin,
        isLoading,
        error,
        login,
        logout,
        getAuthHeader,
        setError,
    };

    return (
        <AuthContext.Provider value={value}>
            {!isLoading && children}
        </AuthContext.Provider>
    );
};


export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};