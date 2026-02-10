import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import incidentService from '../services/incidentService';
import { useAuth } from '../context/AuthContext';
import { useNotifications } from '../context/NotificationContext';

function IncidentDetail() {
    const { incidentId } = useParams();
    const navigate = useNavigate();
    const { user } = useAuth();
    const { addToast } = useNotifications();

    const [incident, setIncident] = useState(null);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState(false);

    // Modal states
    const [showNoteModal, setShowNoteModal] = useState(false);
    const [showResolveModal, setShowResolveModal] = useState(false);
    const [noteText, setNoteText] = useState('');
    const [resolutionNotes, setResolutionNotes] = useState('');

    useEffect(() => {
        fetchIncident();
    }, [incidentId]);

    const fetchIncident = async () => {
        try {
            setLoading(true);
            const data = await incidentService.getIncident(incidentId);
            // Backend returns { incident: {...}, history: [...] }
            // Merge them together for convenience
            if (data.incident) {
                setIncident({ ...data.incident, history: data.history || [] });
            } else {
                setIncident(data);
            }
        } catch (error) {
            console.error('Failed to fetch incident:', error);
            addToast({ type: 'critical', title: 'Error', message: 'Failed to load incident' });
        } finally {
            setLoading(false);
        }
    };

    const handleAcknowledge = async () => {
        setActionLoading(true);
        try {
            await incidentService.acknowledgeIncident(incidentId, user.employee_id, user.name);
            addToast({ type: 'success', title: 'Success', message: 'Incident acknowledged' });
            fetchIncident();
        } catch (error) {
            addToast({ type: 'critical', title: 'Error', message: 'Failed to acknowledge incident' });
        } finally {
            setActionLoading(false);
        }
    };

    const handleStart = async () => {
        setActionLoading(true);
        try {
            await incidentService.startIncident(incidentId, user.employee_id, user.name);
            addToast({ type: 'success', title: 'Success', message: 'Started working on incident' });
            fetchIncident();
        } catch (error) {
            addToast({ type: 'critical', title: 'Error', message: 'Failed to start incident' });
        } finally {
            setActionLoading(false);
        }
    };

    const handleAddNote = async () => {
        if (!noteText.trim()) return;
        setActionLoading(true);
        try {
            await incidentService.addNote(incidentId, user.employee_id, user.name, noteText);
            addToast({ type: 'success', title: 'Success', message: 'Note added' });
            setNoteText('');
            setShowNoteModal(false);
            fetchIncident();
        } catch (error) {
            addToast({ type: 'critical', title: 'Error', message: 'Failed to add note' });
        } finally {
            setActionLoading(false);
        }
    };

    const handleResolve = async () => {
        if (!resolutionNotes.trim()) {
            addToast({ type: 'warning', title: 'Required', message: 'Resolution notes are required' });
            return;
        }
        if (resolutionNotes.trim().length < 10) {
            addToast({ type: 'warning', title: 'Too Short', message: 'Resolution notes must be at least 10 characters' });
            return;
        }
        setActionLoading(true);
        try {
            await incidentService.resolveIncident(incidentId, user.employee_id, user.name, resolutionNotes);
            addToast({ type: 'success', title: 'Success', message: 'Incident resolved!' });
            setShowResolveModal(false);
            fetchIncident();
        } catch (error) {
            const errorMsg = error.response?.data?.error || 'Failed to resolve incident';
            console.error('Resolve error:', error.response?.data);
            addToast({ type: 'critical', title: 'Error', message: errorMsg });
        } finally {
            setActionLoading(false);
        }
    };

    const formatDate = (dateStr) => {
        if (!dateStr) return 'N/A';
        return new Date(dateStr).toLocaleString();
    };

    const formatDuration = (seconds) => {
        if (!seconds) return 'N/A';
        if (seconds < 60) return `${seconds} seconds`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes`;
        return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
    };

    const formatActionName = (action) => {
        const actionMap = {
            'CREATED': '📝 Incident Created',
            'ASSIGNED': '👤 Assigned',
            'CLAIMED': '🤝 Claimed',
            'ACKNOWLEDGED': '✓ Acknowledged',
            'STARTED_PROGRESS': '▶ Started Progress',
            'NOTE_ADDED': '📝 Note Added',
            'INCIDENT_RESOLVED': '✅ Resolved',
            'STATUS_CHANGED': '🔄 Status Changed'
        };
        return actionMap[action] || action?.replace('_', ' ');
    };

    const getStatusClass = (status) => `status-${status?.toLowerCase()}`;
    const canPerformActions = incident?.assigned_employee_id === user?.employee_id;
    const canClaimIncident = incident && ['OPEN', 'ASSIGNED', 'ACKNOWLEDGED'].includes(incident.status) && incident.assigned_employee_id !== user?.employee_id;

    const handleClaim = async () => {
        if (!user) return;
        
        setActionLoading(true);
        try {
            await incidentService.claimIncident(incident.incident_id, {
                employee_id: user.employee_id,
                employee_name: user.name
            });
            addToast({ type: 'success', title: 'Success', message: 'Incident claimed successfully!' });
            fetchIncident();
        } catch (error) {
            const errorMsg = error.response?.data?.error || 'Failed to claim incident';
            addToast({ type: 'critical', title: 'Error', message: errorMsg });
        } finally {
            setActionLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="loading-container">
                <div className="loading-spinner"></div>
            </div>
        );
    }

    if (!incident) {
        return (
            <div className="empty-state">
                <div className="empty-state-icon">❌</div>
                <div className="empty-state-title">Incident not found</div>
                <Link to="/incidents" className="btn btn-primary" style={{ marginTop: '16px' }}>
                    ← Back to Incidents
                </Link>
            </div>
        );
    }

    return (
        <div>
            <div className="header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <Link to="/incidents" className="btn btn-secondary btn-icon">
                        ←
                    </Link>
                    <div>
                        <h1 className="header-title">{incident.incident_id}</h1>
                        <span className={`status-badge ${getStatusClass(incident.status)}`} style={{ marginTop: '4px' }}>
                            {incident.status?.replace('_', ' ')}
                        </span>
                    </div>
                </div>

                {/* Claim Button - for staff who are NOT assigned */}
                {canClaimIncident && (
                    <div className="header-actions">
                        <button
                            className="btn btn-info"
                            onClick={handleClaim}
                            disabled={actionLoading}
                        >
                            🤝 Claim This Incident
                        </button>
                    </div>
                )}

                {/* Action Buttons - for assigned staff */}
                {canPerformActions && incident.status !== 'RESOLVED' && (
                    <div className="header-actions">
                        {incident.status === 'ASSIGNED' && (
                            <button
                                className="btn btn-primary"
                                onClick={handleAcknowledge}
                                disabled={actionLoading}
                            >
                                ✓ Acknowledge
                            </button>
                        )}
                        {incident.status === 'ACKNOWLEDGED' && (
                            <button
                                className="btn btn-warning"
                                onClick={handleStart}
                                disabled={actionLoading}
                            >
                                ▶ Start Progress
                            </button>
                        )}
                        {incident.status === 'IN_PROGRESS' && (
                            <>
                                <button
                                    className="btn btn-secondary"
                                    onClick={() => setShowNoteModal(true)}
                                >
                                    📝 Add Note
                                </button>
                                <button
                                    className="btn btn-success"
                                    onClick={() => setShowResolveModal(true)}
                                >
                                    ✓ Resolve
                                </button>
                            </>
                        )}
                    </div>
                )}
            </div>

            <div className="grid-2">
                {/* Incident Details */}
                <div className="card">
                    <h3 className="card-title" style={{ marginBottom: '16px' }}>Incident Details</h3>

                    <div style={{ display: 'grid', gap: '12px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                            <span style={{ color: 'var(--text-secondary)' }}>Severity</span>
                            <span className={`badge badge-${incident.severity?.toLowerCase()}`}>{incident.severity}</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                            <span style={{ color: 'var(--text-secondary)' }}>Patient ID</span>
                            <span style={{ fontWeight: 600 }}>{incident.patient_id}</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                            <span style={{ color: 'var(--text-secondary)' }}>Room</span>
                            <span style={{ fontWeight: 600 }}>{incident.room || 'N/A'}</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                            <span style={{ color: 'var(--text-secondary)' }}>Alert ID</span>
                            <span style={{ fontFamily: 'monospace', fontSize: '14px' }}>{incident.alert_id}</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                            <span style={{ color: 'var(--text-secondary)' }}>Assigned To</span>
                            <span style={{ fontWeight: 600 }}>{incident.assigned_to || 'Unassigned'}</span>
                        </div>
                    </div>
                </div>

                {/* Timeline */}
                <div className="card">
                    <h3 className="card-title" style={{ marginBottom: '16px' }}>Timestamps</h3>

                    <div style={{ display: 'grid', gap: '12px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                            <span style={{ color: 'var(--text-secondary)' }}>Created</span>
                            <span>{formatDate(incident.created_at)}</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                            <span style={{ color: 'var(--text-secondary)' }}>Assigned</span>
                            <span>{formatDate(incident.assigned_at)}</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                            <span style={{ color: 'var(--text-secondary)' }}>Acknowledged</span>
                            <span>{formatDate(incident.acknowledged_at)}</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                            <span style={{ color: 'var(--text-secondary)' }}>In Progress</span>
                            <span>{formatDate(incident.in_progress_at)}</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                            <span style={{ color: 'var(--text-secondary)' }}>Resolved</span>
                            <span>{formatDate(incident.resolved_at)}</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Metrics */}
            {(incident.response_time_seconds || incident.resolution_time_seconds) && (
                <div className="stats-grid" style={{ marginTop: '24px' }}>
                    <div className="stat-card">
                        <div className="stat-icon">⚡</div>
                        <div className="stat-value">{formatDuration(incident.response_time_seconds)}</div>
                        <div className="stat-label">Response Time</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-icon">🔧</div>
                        <div className="stat-value">{formatDuration(incident.resolution_time_seconds)}</div>
                        <div className="stat-label">Resolution Time</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-icon">⏱️</div>
                        <div className="stat-value">{formatDuration(incident.total_time_seconds)}</div>
                        <div className="stat-label">Total Time</div>
                    </div>
                </div>
            )}

            {/* Resolution Notes */}
            {incident.resolution_notes && (
                <div className="card" style={{ marginTop: '24px' }}>
                    <h3 className="card-title" style={{ marginBottom: '16px' }}>Resolution Notes</h3>
                    <p style={{ background: 'var(--bg-primary)', padding: '16px', borderRadius: '8px', lineHeight: '1.6' }}>
                        {incident.resolution_notes}
                    </p>
                </div>
            )}

            {/* History Timeline */}
            {incident.history && incident.history.length > 0 && (
                <div className="card" style={{ marginTop: '24px' }}>
                    <h3 className="card-title" style={{ marginBottom: '24px' }}>Activity History</h3>
                    <div className="timeline">
                        {incident.history.map((entry, index) => (
                            <div key={index} className="timeline-item">
                                <div className="timeline-time">{formatDate(entry.timestamp)}</div>
                                <div className="timeline-content">
                                    <div className="timeline-action">{formatActionName(entry.action)}</div>
                                    <div className="timeline-actor">by {entry.employee_name || 'System'}</div>
                                    {entry.note && (
                                        <p style={{ marginTop: '8px', color: 'var(--text-secondary)', fontSize: '14px' }}>
                                            {entry.note}
                                        </p>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Add Note Modal */}
            {showNoteModal && (
                <div className="modal-overlay" onClick={() => setShowNoteModal(false)}>
                    <div className="modal" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3 className="modal-title">Add Progress Note</h3>
                            <button className="modal-close" onClick={() => setShowNoteModal(false)}>✕</button>
                        </div>
                        <div className="modal-body">
                            <div className="form-group">
                                <label className="form-label">Note</label>
                                <textarea
                                    className="form-input"
                                    placeholder="Enter your progress update..."
                                    value={noteText}
                                    onChange={(e) => setNoteText(e.target.value)}
                                    rows={4}
                                />
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn-secondary" onClick={() => setShowNoteModal(false)}>
                                Cancel
                            </button>
                            <button
                                className="btn btn-primary"
                                onClick={handleAddNote}
                                disabled={actionLoading || !noteText.trim()}
                            >
                                Add Note
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Resolve Modal */}
            {showResolveModal && (
                <div className="modal-overlay" onClick={() => setShowResolveModal(false)}>
                    <div className="modal" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3 className="modal-title">Resolve Incident</h3>
                            <button className="modal-close" onClick={() => setShowResolveModal(false)}>✕</button>
                        </div>
                        <div className="modal-body">
                            <div className="form-group">
                                <label className="form-label">Resolution Notes (Required)</label>
                                <textarea
                                    className="form-input"
                                    placeholder="Describe how the incident was resolved..."
                                    value={resolutionNotes}
                                    onChange={(e) => setResolutionNotes(e.target.value)}
                                    rows={5}
                                />
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn-secondary" onClick={() => setShowResolveModal(false)}>
                                Cancel
                            </button>
                            <button
                                className="btn btn-success"
                                onClick={handleResolve}
                                disabled={actionLoading || !resolutionNotes.trim()}
                            >
                                ✓ Resolve Incident
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default IncidentDetail;
