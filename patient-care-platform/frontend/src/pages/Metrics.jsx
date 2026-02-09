import { useState, useEffect } from 'react';
import incidentService from '../services/incidentService';
import { useNotifications } from '../context/NotificationContext';

function Metrics() {
    const [metrics, setMetrics] = useState(null);
    const [incidents, setIncidents] = useState([]);
    const [loading, setLoading] = useState(true);
    const { addToast } = useNotifications();

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [metricsData, incidentsData] = await Promise.all([
                incidentService.getMetrics(),
                incidentService.getIncidents()
            ]);
            setMetrics(metricsData);
            setIncidents(incidentsData);
        } catch (error) {
            console.error('Failed to fetch metrics:', error);
            addToast({ type: 'critical', title: 'Error', message: 'Failed to load metrics' });
        } finally {
            setLoading(false);
        }
    };

    const formatTime = (seconds) => {
        if (!seconds) return '0s';
        if (seconds < 60) return `${Math.round(seconds)}s`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
        const hours = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${mins}m`;
    };

    // Calculate stats from incidents
    const statusCounts = incidents.reduce((acc, inc) => {
        acc[inc.status] = (acc[inc.status] || 0) + 1;
        return acc;
    }, {});

    const severityCounts = incidents.reduce((acc, inc) => {
        acc[inc.severity] = (acc[inc.severity] || 0) + 1;
        return acc;
    }, {});

    const totalIncidents = incidents.length;

    if (loading) {
        return (
            <div className="loading-container">
                <div className="loading-spinner"></div>
            </div>
        );
    }

    return (
        <div>
            <div className="header">
                <h1 className="header-title">Metrics & Analytics</h1>
                <button className="btn btn-primary" onClick={fetchData}>
                    🔄 Refresh
                </button>
            </div>

            {/* Key Metrics */}
            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-icon">⏱️</div>
                    <div className="stat-value">{formatTime(metrics?.avg_response_time_seconds)}</div>
                    <div className="stat-label">Avg Response Time</div>
                </div>

                <div className="stat-card success">
                    <div className="stat-icon">✅</div>
                    <div className="stat-value">{formatTime(metrics?.avg_resolution_time_seconds)}</div>
                    <div className="stat-label">Avg Resolution Time</div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon">📊</div>
                    <div className="stat-value">{totalIncidents}</div>
                    <div className="stat-label">Total Incidents</div>
                </div>

                <div className="stat-card success">
                    <div className="stat-icon">🎯</div>
                    <div className="stat-value">{statusCounts['RESOLVED'] || 0}</div>
                    <div className="stat-label">Resolved</div>
                </div>
            </div>

            <div className="grid-2" style={{ marginTop: '24px' }}>
                {/* By Status */}
                <div className="card">
                    <h3 className="card-title" style={{ marginBottom: '24px' }}>Incidents by Status</h3>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                        {['OPEN', 'ASSIGNED', 'ACKNOWLEDGED', 'IN_PROGRESS', 'RESOLVED'].map(status => {
                            const count = statusCounts[status] || 0;
                            const percentage = totalIncidents > 0 ? (count / totalIncidents) * 100 : 0;

                            return (
                                <div key={status}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                                        <span className={`status-badge status-${status.toLowerCase()}`}>
                                            {status.replace('_', ' ')}
                                        </span>
                                        <span style={{ fontWeight: 600 }}>{count}</span>
                                    </div>
                                    <div style={{
                                        height: '8px',
                                        background: 'var(--bg-primary)',
                                        borderRadius: '4px',
                                        overflow: 'hidden'
                                    }}>
                                        <div style={{
                                            height: '100%',
                                            width: `${percentage}%`,
                                            background: status === 'RESOLVED' ? 'var(--success)' :
                                                status === 'IN_PROGRESS' ? 'var(--critical)' :
                                                    status === 'OPEN' ? 'var(--danger)' :
                                                        status === 'ASSIGNED' ? 'var(--warning)' : 'var(--primary)',
                                            borderRadius: '4px',
                                            transition: 'width 0.5s ease'
                                        }}></div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* By Severity */}
                <div className="card">
                    <h3 className="card-title" style={{ marginBottom: '24px' }}>Incidents by Severity</h3>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                        {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map(severity => {
                            const count = severityCounts[severity] || 0;
                            const percentage = totalIncidents > 0 ? (count / totalIncidents) * 100 : 0;

                            return (
                                <div key={severity}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                                        <span className={`badge badge-${severity.toLowerCase()}`}>
                                            {severity}
                                        </span>
                                        <span style={{ fontWeight: 600 }}>{count}</span>
                                    </div>
                                    <div style={{
                                        height: '8px',
                                        background: 'var(--bg-primary)',
                                        borderRadius: '4px',
                                        overflow: 'hidden'
                                    }}>
                                        <div style={{
                                            height: '100%',
                                            width: `${percentage}%`,
                                            background: severity === 'CRITICAL' ? 'var(--danger)' :
                                                severity === 'HIGH' ? 'var(--warning)' :
                                                    severity === 'MEDIUM' ? 'var(--primary)' : 'var(--success)',
                                            borderRadius: '4px',
                                            transition: 'width 0.5s ease'
                                        }}></div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>

            {/* Additional Metrics */}
            {metrics && (
                <div className="card" style={{ marginTop: '24px' }}>
                    <h3 className="card-title" style={{ marginBottom: '24px' }}>Performance Summary</h3>

                    <div className="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Metric</th>
                                    <th>Value</th>
                                    <th>Details</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>Average Response Time</td>
                                    <td style={{ fontWeight: 600 }}>{formatTime(metrics.avg_response_time_seconds)}</td>
                                    <td style={{ color: 'var(--text-secondary)' }}>Time from incident creation to acknowledgment</td>
                                </tr>
                                <tr>
                                    <td>Average Resolution Time</td>
                                    <td style={{ fontWeight: 600 }}>{formatTime(metrics.avg_resolution_time_seconds)}</td>
                                    <td style={{ color: 'var(--text-secondary)' }}>Time from acknowledgment to resolution</td>
                                </tr>
                                <tr>
                                    <td>Total Resolved</td>
                                    <td style={{ fontWeight: 600 }}>{metrics.resolved_count || 0}</td>
                                    <td style={{ color: 'var(--text-secondary)' }}>Incidents successfully resolved</td>
                                </tr>
                                <tr>
                                    <td>Open Incidents</td>
                                    <td style={{ fontWeight: 600 }}>{statusCounts['OPEN'] || 0}</td>
                                    <td style={{ color: 'var(--text-secondary)' }}>Incidents waiting for assignment</td>
                                </tr>
                                <tr>
                                    <td>Active Incidents</td>
                                    <td style={{ fontWeight: 600 }}>
                                        {(statusCounts['ASSIGNED'] || 0) + (statusCounts['ACKNOWLEDGED'] || 0) + (statusCounts['IN_PROGRESS'] || 0)}
                                    </td>
                                    <td style={{ color: 'var(--text-secondary)' }}>Currently being worked on</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
}

export default Metrics;
