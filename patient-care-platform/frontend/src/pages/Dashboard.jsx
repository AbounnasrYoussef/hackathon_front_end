import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import incidentService from '../services/incidentService';
import { useAuth } from '../context/AuthContext';

function Dashboard() {
    const { user } = useAuth();
    const [incidents, setIncidents] = useState([]);
    const [metrics, setMetrics] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchData();
        // Auto-refresh every 30 seconds
        const interval = setInterval(fetchData, 30000);
        return () => clearInterval(interval);
    }, []);

    const fetchData = async () => {
        try {
            const [incidentsData, metricsData] = await Promise.all([
                incidentService.getIncidents(),
                incidentService.getMetrics()
            ]);
            setIncidents(incidentsData);
            setMetrics(metricsData);
        } catch (error) {
            console.error('Failed to fetch dashboard data:', error);
        } finally {
            setLoading(false);
        }
    };

    // Calculate stats
    const openIncidents = incidents.filter(i => i.status === 'OPEN').length;
    const assignedIncidents = incidents.filter(i => i.status === 'ASSIGNED').length;
    const inProgressIncidents = incidents.filter(i => i.status === 'IN_PROGRESS').length;
    const criticalIncidents = incidents.filter(i => i.severity === 'CRITICAL' && i.status !== 'RESOLVED').length;

    // My assigned incidents
    const myIncidents = incidents.filter(i =>
        i.assigned_employee_id === user?.employee_id &&
        i.status !== 'RESOLVED'
    );

    const formatTime = (seconds) => {
        if (!seconds) return 'N/A';
        if (seconds < 60) return `${seconds}s`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
        return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
    };

    const getSeverityClass = (severity) => {
        return `severity-${severity?.toLowerCase()}`;
    };

    const getStatusClass = (status) => {
        return `status-${status?.toLowerCase()}`;
    };

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
                <h1 className="header-title">Dashboard</h1>
                <button className="btn btn-primary" onClick={fetchData}>
                    🔄 Refresh
                </button>
            </div>

            {/* Stats Grid */}
            <div className="stats-grid">
                <div className="stat-card critical">
                    <div className="stat-icon">🚨</div>
                    <div className="stat-value">{criticalIncidents}</div>
                    <div className="stat-label">Critical Incidents</div>
                </div>

                <div className="stat-card warning">
                    <div className="stat-icon">📋</div>
                    <div className="stat-value">{openIncidents}</div>
                    <div className="stat-label">Open Incidents</div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon">👤</div>
                    <div className="stat-value">{assignedIncidents}</div>
                    <div className="stat-label">Assigned</div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon">⚡</div>
                    <div className="stat-value">{inProgressIncidents}</div>
                    <div className="stat-label">In Progress</div>
                </div>
            </div>

            {/* Metrics Cards */}
            {metrics && (
                <div className="stats-grid" style={{ marginBottom: '24px' }}>
                    <div className="stat-card success">
                        <div className="stat-icon">⏱️</div>
                        <div className="stat-value">{formatTime(metrics.avg_response_time_seconds)}</div>
                        <div className="stat-label">Avg Response Time</div>
                    </div>

                    <div className="stat-card success">
                        <div className="stat-icon">✅</div>
                        <div className="stat-value">{formatTime(metrics.avg_resolution_time_seconds)}</div>
                        <div className="stat-label">Avg Resolution Time</div>
                    </div>

                    <div className="stat-card success">
                        <div className="stat-icon">📊</div>
                        <div className="stat-value">{metrics.resolved_count || 0}</div>
                        <div className="stat-label">Resolved Today</div>
                    </div>
                </div>
            )}

            {/* My Incidents */}
            <div className="card">
                <div className="card-header">
                    <h2 className="card-title">My Active Incidents</h2>
                    <Link to="/incidents" className="btn btn-secondary btn-sm">
                        View All →
                    </Link>
                </div>

                {myIncidents.length === 0 ? (
                    <div className="empty-state">
                        <div className="empty-state-icon">✨</div>
                        <div className="empty-state-title">No active incidents</div>
                        <p>You don't have any incidents assigned to you.</p>
                    </div>
                ) : (
                    <div>
                        {myIncidents.slice(0, 5).map(incident => (
                            <Link
                                key={incident.incident_id}
                                to={`/incidents/${incident.incident_id}`}
                                style={{ textDecoration: 'none' }}
                            >
                                <div className={`incident-card ${getSeverityClass(incident.severity)}`}>
                                    <div className="incident-header">
                                        <div>
                                            <span className="incident-id">{incident.incident_id}</span>
                                            <span className={`badge badge-${incident.severity?.toLowerCase()}`} style={{ marginLeft: '12px' }}>
                                                {incident.severity}
                                            </span>
                                        </div>
                                        <span className={`status-badge ${getStatusClass(incident.status)}`}>
                                            {incident.status?.replace('_', ' ')}
                                        </span>
                                    </div>
                                    <div className="incident-meta">
                                        <span className="incident-meta-item">
                                            🏥 Patient: {incident.patient_id}
                                        </span>
                                        <span className="incident-meta-item">
                                            🚪 Room: {incident.room || 'N/A'}
                                        </span>
                                        <span className="incident-meta-item">
                                            ⏰ {new Date(incident.created_at).toLocaleTimeString()}
                                        </span>
                                    </div>
                                </div>
                            </Link>
                        ))}
                    </div>
                )}
            </div>

            {/* Recent All Incidents */}
            <div className="card" style={{ marginTop: '24px' }}>
                <div className="card-header">
                    <h2 className="card-title">Recent Incidents</h2>
                </div>

                <div className="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Incident ID</th>
                                <th>Patient</th>
                                <th>Severity</th>
                                <th>Status</th>
                                <th>Assigned To</th>
                                <th>Created</th>
                            </tr>
                        </thead>
                        <tbody>
                            {incidents.slice(0, 10).map(incident => (
                                <tr key={incident.incident_id}>
                                    <td>
                                        <Link to={`/incidents/${incident.incident_id}`} style={{ fontWeight: 600 }}>
                                            {incident.incident_id}
                                        </Link>
                                    </td>
                                    <td>{incident.patient_id}</td>
                                    <td>
                                        <span className={`badge badge-${incident.severity?.toLowerCase()}`}>
                                            {incident.severity}
                                        </span>
                                    </td>
                                    <td>
                                        <span className={`status-badge ${getStatusClass(incident.status)}`}>
                                            {incident.status?.replace('_', ' ')}
                                        </span>
                                    </td>
                                    <td>{incident.assigned_to || '—'}</td>
                                    <td>{new Date(incident.created_at).toLocaleString()}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}

export default Dashboard;
