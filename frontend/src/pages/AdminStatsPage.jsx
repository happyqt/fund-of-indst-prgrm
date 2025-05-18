import React, {useState, useEffect} from 'react';
import {useAuth} from '../context/AuthContext';

function AdminStatsPage() {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const {isLoading: authLoading, isAdmin, getAuthHeader} = useAuth();

    useEffect(() => {
        if (authLoading) {
            return;
        }


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
                    throw new Error(errorData.message || `Error loading exchange statistics: ${response.status}`);
                }

                const data = await response.json();
                setStats(data);
            } catch (err) {
                console.error("Failed to fetch exchange stats for admin:", err);
                setError('Failed to load exchange statistics. Please try again later.');
            } finally {
                setLoading(false);
            }
        };

        fetchStats();

    }, [authLoading, isAdmin]);

    if (authLoading || loading) {
        return <p>Loading exchange statistics (Admin)...</p>;
    }


    if (error) {
        return <p className="error-message">Error loading exchange statistics: {error}</p>;
    }

    return (
        <div>
            <h2>Exchange Statistics (Admin)</h2>
            {stats === null ? (
                <p>No statistics available or failed to load.</p>
            ) : (
                <div>
                    <p><strong>Total Exchanges:</strong> {stats.total_exchanges}</p>
                    <p><strong>Pending Exchanges:</strong> {stats.pending_count}</p>
                    <p><strong>Accepted Exchanges:</strong> {stats.accepted_count}</p>
                    <p><strong>Rejected Exchanges:</strong> {stats.rejected_count}</p>
                    <p><strong>Cancelled Exchanges:</strong> {stats.cancelled_count}</p>
                </div>
            )}
        </div>
    );
}

export default AdminStatsPage;