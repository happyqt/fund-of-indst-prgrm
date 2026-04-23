import React, {useState, useEffect} from 'react';
import {useAuth} from '../context/AuthContext';

function StatBar({label, count, total, colorClass}) {
    const pct = total > 0 ? Math.round((count / total) * 100) : 0;
    return (
        <div className="stat-bar-item">
            <div className="stat-bar-header">
                <span className="stat-bar-label">{label}</span>
                <span className="stat-bar-value">{count} <small>({pct}%)</small></span>
            </div>
            <div className="stat-bar-track">
                <div
                    className={`stat-bar-fill ${colorClass}`}
                    style={{width: `${pct}%`}}
                />
            </div>
        </div>
    );
}

function AdminStatsPage() {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const {isLoading: authLoading, isAdmin, getAuthHeader} = useAuth();

    useEffect(() => {
        if (authLoading) return;

        const fetchStats = async () => {
            setLoading(true);
            setError(null);
            setStats(null);

            try {
                const response = await fetch('/api/admin/exchanges/stats', {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': getAuthHeader(),
                    },
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.message || `Ошибка загрузки статистики: ${response.status}`);
                }

                const data = await response.json();
                setStats(data);
            } catch (err) {
                console.error("Failed to fetch exchange stats:", err);
                setError('Не удалось загрузить статистику обменов. Попробуйте позже.');
            } finally {
                setLoading(false);
            }
        };

        fetchStats();
    }, [authLoading, isAdmin, getAuthHeader]);

    if (authLoading || loading) {
        return <p>Загрузка статистики обменов...</p>;
    }

    if (error) {
        return <p className="error-message">Ошибка: {error}</p>;
    }

    return (
        <div className="admin-stats-container">
            <h2>Статистика обменов</h2>
            {stats === null ? (
                <p>Статистика недоступна.</p>
            ) : (
                <>
                    <div className="stat-summary-cards">
                        <div className="stat-card">
                            <span className="stat-card-number">{stats.total_exchanges}</span>
                            <span className="stat-card-label">Всего обменов</span>
                        </div>
                        <div className="stat-card accent-green">
                            <span className="stat-card-number">{stats.accepted_count}</span>
                            <span className="stat-card-label">Завершено</span>
                        </div>
                        <div className="stat-card accent-yellow">
                            <span className="stat-card-number">{stats.pending_count}</span>
                            <span className="stat-card-label">Ожидают</span>
                        </div>
                        <div className="stat-card accent-red">
                            <span className="stat-card-number">{stats.rejected_count + stats.cancelled_count}</span>
                            <span className="stat-card-label">Отклонено / отменено</span>
                        </div>
                    </div>

                    <div className="stat-bars-section">
                        <h3>Распределение по статусам</h3>
                        <StatBar
                            label="Принятые (accepted)"
                            count={stats.accepted_count}
                            total={stats.total_exchanges}
                            colorClass="bar-green"
                        />
                        <StatBar
                            label="Ожидают (pending)"
                            count={stats.pending_count}
                            total={stats.total_exchanges}
                            colorClass="bar-yellow"
                        />
                        <StatBar
                            label="Отклонённые (rejected)"
                            count={stats.rejected_count}
                            total={stats.total_exchanges}
                            colorClass="bar-red"
                        />
                        <StatBar
                            label="Отменённые (cancelled)"
                            count={stats.cancelled_count}
                            total={stats.total_exchanges}
                            colorClass="bar-gray"
                        />
                    </div>
                </>
            )}
        </div>
    );
}

export default AdminStatsPage;