import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import incidentService from '../services/incidentService';
import { useAuth } from '../context/AuthContext';

function Dashboard() {
    const { user } = useAuth();
    const [incidents, setIncidents] = useState([]);
    const [metrics, setMetrics] = useState(null);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState({});

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

    const handleAcknowledge = async (incidentId, e) => {
        e.preventDefault();
        e.stopPropagation();
        setActionLoading(prev => ({ ...prev, [incidentId]: true }));
        try {
            await incidentService.acknowledgeIncident(incidentId, user.employee_id, user.name);
            fetchData();
        } catch (error) {
            console.error('Failed to acknowledge incident:', error);
            alert('Failed to acknowledge incident');
        } finally {
            setActionLoading(prev => ({ ...prev, [incidentId]: false }));
        }
    };

    const handleStart = async (incidentId, e) => {
        e.preventDefault();
        e.stopPropagation();
        setActionLoading(prev => ({ ...prev, [incidentId]: true }));
        try {
            await incidentService.startIncident(incidentId, user.employee_id, user.name);
            fetchData();
        } catch (error) {
            console.error('Failed to start incident:', error);
            alert('Failed to start incident');
        } finally {
            setActionLoading(prev => ({ ...prev, [incidentId]: false }));
        }
    };

    // Calculate personal stats - only incidents assigned to me
    const myIncidents = incidents.filter(i => i.assigned_employee_id === user?.employee_id);
    
    const myOpenIncidents = myIncidents.filter(i => i.status === 'OPEN').length;
    const myAssignedIncidents = myIncidents.filter(i => i.status === 'ASSIGNED').length;
    const myInProgressIncidents = myIncidents.filter(i => i.status === 'IN_PROGRESS').length;
    const myCriticalIncidents = myIncidents.filter(i => i.severity === 'CRITICAL' && i.status !== 'RESOLVED').length;
    const myResolvedIncidents = myIncidents.filter(i => i.status === 'RESOLVED').length;

    // My active incidents (not resolved)
    const myActiveIncidents = myIncidents.filter(i => i.status !== 'RESOLVED');

    // Calculate my personal performance metrics
    const myResolvedIncidentsWithTime = myIncidents.filter(i => 
        i.status === 'RESOLVED' && i.response_time_seconds
    );
    const myAvgResponseTime = myResolvedIncidentsWithTime.length > 0
        ? Math.round(myResolvedIncidentsWithTime.reduce((sum, i) => sum + (i.response_time_seconds || 0), 0) / myResolvedIncidentsWithTime.length)
        : null;
    const myAvgResolutionTime = myResolvedIncidentsWithTime.length > 0
        ? Math.round(myResolvedIncidentsWithTime.reduce((sum, i) => sum + (i.resolution_time_seconds || 0), 0) / myResolvedIncidentsWithTime.length)
        : null;

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
                <h1 className="header-title">My Dashboard</h1>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: '14px', fontWeight: '600', color: 'var(--text-primary)' }}>{user?.name}</div>
                        <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{user?.role?.replace('_', ' ')} • ID: {user?.login}</div>
                    </div>
                    <button className="btn btn-primary" onClick={fetchData}>
                        🔄 Refresh
                    </button>
                </div>
            </div>

            {/* Personal Stats Grid */}
            <div className="stats-grid">
                <div className="stat-card critical">
                    <div className="stat-icon">🚨</div>
                    <div className="stat-value">{myCriticalIncidents}</div>
                    <div className="stat-label">My Critical Cases</div>
                </div>

                <div className="stat-card warning">
                    <div className="stat-icon">📋</div>
                    <div className="stat-value">{myAssignedIncidents}</div>
                    <div className="stat-label">Assigned to Me</div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon">⚡</div>
                    <div className="stat-value">{myInProgressIncidents}</div>
                    <div className="stat-label">In Progress</div>
                </div>

                <div className="stat-card success">
                    <div className="stat-icon">✅</div>
                    <div className="stat-value">{myResolvedIncidents}</div>
                    <div className="stat-label">Resolved by Me</div>
                </div>
            </div>

            {/* My Performance Metrics */}
            <div className="stats-grid" style={{ marginBottom: '24px' }}>
                <div className="stat-card success">
                    <div className="stat-icon">⏱️</div>
                    <div className="stat-value">{formatTime(myAvgResponseTime)}</div>
                    <div className="stat-label">My Avg Response Time</div>
                </div>

                <div className="stat-card success">
                    <div className="stat-icon">🏁</div>
                    <div className="stat-value">{formatTime(myAvgResolutionTime)}</div>
                    <div className="stat-label">My Avg Resolution Time</div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon">📊</div>
                    <div className="stat-value">{myActiveIncidents.length}</div>
                    <div className="stat-label">Active Cases</div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon">📈</div>
                    <div className="stat-value">{myIncidents.length}</div>
                    <div className="stat-label">Total Assigned</div>
                </div>
            </div>

            {/* My Incidents */}
            <div className="card">
                <div className="card-header">
                    <h2 className="card-title">My Active Incidents ({myActiveIncidents.length})</h2>
                    <Link to="/incidents" className="btn btn-secondary btn-sm">
                        View All →
                    </Link>
                </div>

                {myActiveIncidents.length === 0 ? (
                    <div className="empty-state">
                        <div className="empty-state-icon">✨</div>
                        <div className="empty-state-title">No active incidents</div>
                        <p>You don't have any incidents assigned to you.</p>
                    </div>
                ) : (
                    <div>
                        {myActiveIncidents.map(incident => (
                            <div
                                key={incident.incident_id}
                                className={`incident-card ${getSeverityClass(incident.severity)}`}
                                style={{ marginBottom: '12px' }}
                            >
                                <Link
                                    to={`/incidents/${incident.incident_id}`}
                                    style={{ textDecoration: 'none', flex: 1 }}
                                >
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
                                </Link>
                                
                                {/* Action Buttons */}
                                <div style={{ display: 'flex', gap: '8px', marginTop: '12px', paddingTop: '12px', borderTop: '1px solid var(--border-color)' }}>
                                    {incident.status === 'ASSIGNED' && (
                                        <button
                                            className="btn btn-success btn-sm"
                                            onClick={(e) => handleAcknowledge(incident.incident_id, e)}
                                            disabled={actionLoading[incident.incident_id]}
                                        >
                                            {actionLoading[incident.incident_id] ? '...' : '✓ Acknowledge'}
                                        </button>
                                    )}
                                    {incident.status === 'ACKNOWLEDGED' && (
                                        <button
                                            className="btn btn-primary btn-sm"
                                            onClick={(e) => handleStart(incident.incident_id, e)}
                                            disabled={actionLoading[incident.incident_id]}
                                        >
                                            {actionLoading[incident.incident_id] ? '...' : '▶ Start Progress'}
                                        </button>
                                    )}
                                    {incident.status === 'IN_PROGRESS' && (
                                        <Link 
                                            to={`/incidents/${incident.incident_id}`}
                                            className="btn btn-warning btn-sm"
                                            style={{ textDecoration: 'none' }}
                                        >
                                            🏁 Resolve →
                                        </Link>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

export default Dashboard;
