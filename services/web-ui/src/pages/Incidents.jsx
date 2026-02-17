import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import incidentService from '../services/incidentService';
import { useAuth } from '../context/AuthContext';
import { useNotifications } from '../context/NotificationContext';

function Incidents() {
    const { user } = useAuth();
    const { addToast } = useNotifications();
    const [incidents, setIncidents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [statusFilter, setStatusFilter] = useState('');
    const [severityFilter, setSeverityFilter] = useState('');

    useEffect(() => {
        fetchIncidents();
    }, []);

    const fetchIncidents = async () => {
        try {
            setLoading(true);
            const data = await incidentService.getIncidents();
            setIncidents(data);
        } catch (error) {
            console.error('Failed to fetch incidents:', error);
            addToast({ type: 'critical', title: 'Error', message: 'Failed to load incidents' });
        } finally {
            setLoading(false);
        }
    };

    const handleAcknowledge = async (e, incidentId) => {
        e.preventDefault();
        e.stopPropagation();
        try {
            await incidentService.acknowledgeIncident(incidentId, user.employee_id, user.name);
            addToast({ type: 'success', title: 'Success', message: 'Incident acknowledged' });
            fetchIncidents();
        } catch (error) {
            addToast({ type: 'critical', title: 'Error', message: 'Failed to acknowledge incident' });
        }
    };

    const handleStart = async (e, incidentId) => {
        e.preventDefault();
        e.stopPropagation();
        try {
            await incidentService.startIncident(incidentId, user.employee_id, user.name);
            addToast({ type: 'success', title: 'Success', message: 'Started working on incident' });
            fetchIncidents();
        } catch (error) {
            addToast({ type: 'critical', title: 'Error', message: 'Failed to start incident' });
        }
    };

    const handleClaim = async (e, incidentId) => {
        e.preventDefault();
        e.stopPropagation();
        try {
            await incidentService.claimIncident(incidentId, {
                employee_id: user.employee_id,
                employee_name: user.name
            });
            addToast({ type: 'success', title: 'Success', message: 'Incident claimed successfully!' });
            fetchIncidents();
        } catch (error) {
            const errorMsg = error.response?.data?.error || 'Failed to claim incident';
            addToast({ type: 'critical', title: 'Error', message: errorMsg });
        }
    };

    // Filter incidents
    const filteredIncidents = incidents.filter(incident => {
        if (statusFilter && incident.status !== statusFilter) return false;
        if (severityFilter && incident.severity !== severityFilter) return false;
        return true;
    });

    const getSeverityClass = (severity) => `severity-${severity?.toLowerCase()}`;
    const getStatusClass = (status) => `status-${status?.toLowerCase()}`;

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
                <h1 className="header-title">Incidents</h1>
                <button className="btn btn-primary" onClick={fetchIncidents}>
                    🔄 Refresh
                </button>
            </div>

            {/* Filters */}
            <div className="filters-bar">
                <div className="filter-group">
                    <span className="filter-label">Status:</span>
                    <select
                        className="filter-select form-select"
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}
                    >
                        <option value="">All Statuses</option>
                        <option value="OPEN">Open</option>
                        <option value="ASSIGNED">Assigned</option>
                        <option value="ACKNOWLEDGED">Acknowledged</option>
                        <option value="IN_PROGRESS">In Progress</option>
                        <option value="RESOLVED">Resolved</option>
                    </select>
                </div>

                <div className="filter-group">
                    <span className="filter-label">Severity:</span>
                    <select
                        className="filter-select form-select"
                        value={severityFilter}
                        onChange={(e) => setSeverityFilter(e.target.value)}
                    >
                        <option value="">All Severities</option>
                        <option value="CRITICAL">Critical</option>
                        <option value="HIGH">High</option>
                        <option value="MEDIUM">Medium</option>
                        <option value="LOW">Low</option>
                    </select>
                </div>

                <div style={{ marginLeft: 'auto', color: 'var(--text-secondary)' }}>
                    Showing {filteredIncidents.length} of {incidents.length} incidents
                </div>
            </div>

            {/* Incidents List */}
            {filteredIncidents.length === 0 ? (
                <div className="empty-state">
                    <div className="empty-state-icon">📋</div>
                    <div className="empty-state-title">No incidents found</div>
                    <p>No incidents match your current filters.</p>
                </div>
            ) : (
                <div>
                    {filteredIncidents.map(incident => (
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
                                        👤 {incident.assigned_to || 'Unassigned'}
                                    </span>
                                    <span className="incident-meta-item">
                                        ⏰ {new Date(incident.created_at).toLocaleString()}
                                    </span>
                                </div>

                                {/* Quick Actions */}
                                {incident.assigned_employee_id === user?.employee_id ? (
                                    <div className="incident-actions">
                                        {incident.status === 'ASSIGNED' && (
                                            <button
                                                className="btn btn-primary btn-sm"
                                                onClick={(e) => handleAcknowledge(e, incident.incident_id)}
                                            >
                                                ✓ Acknowledge
                                            </button>
                                        )}
                                        {incident.status === 'ACKNOWLEDGED' && (
                                            <button
                                                className="btn btn-warning btn-sm"
                                                onClick={(e) => handleStart(e, incident.incident_id)}
                                            >
                                                ▶ Start Progress
                                            </button>
                                        )}
                                        {incident.status === 'IN_PROGRESS' && (
                                            <Link
                                                to={`/incidents/${incident.incident_id}`}
                                                className="btn btn-success btn-sm"
                                                onClick={(e) => e.stopPropagation()}
                                            >
                                                ✓ Resolve
                                            </Link>
                                        )}
                                    </div>
                                ) : (
                                    ['OPEN', 'ASSIGNED', 'ACKNOWLEDGED'].includes(incident.status) && (
                                        <div className="incident-actions">
                                            <button
                                                className="btn btn-info btn-sm"
                                                onClick={(e) => handleClaim(e, incident.incident_id)}
                                            >
                                                🤝 Claim
                                            </button>
                                        </div>
                                    )
                                )}
                            </div>
                        </Link>
                    ))}
                </div>
            )}
        </div>
    );
}

export default Incidents;
