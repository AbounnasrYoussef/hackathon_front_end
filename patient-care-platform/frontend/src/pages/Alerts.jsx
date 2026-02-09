import { useState, useEffect } from 'react';
import alertService from '../services/alertService';
import { useNotifications } from '../context/NotificationContext';

function Alerts() {
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [triggerLoading, setTriggerLoading] = useState(false);
    const { addToast } = useNotifications();

    useEffect(() => {
        fetchAlerts();
    }, []);

    const fetchAlerts = async () => {
        try {
            setLoading(true);
            const data = await alertService.getAllAlerts();
            setAlerts(data);
        } catch (error) {
            console.error('Failed to fetch alerts:', error);
            addToast({ type: 'critical', title: 'Error', message: 'Failed to load alerts' });
        } finally {
            setLoading(false);
        }
    };

    const handleTriggerAlert = async () => {
        setTriggerLoading(true);
        try {
            const newAlert = await alertService.triggerManualAlert();
            addToast({
                type: 'success',
                title: 'Alert Created',
                message: `New alert ${newAlert.alert_id} generated`
            });
            fetchAlerts();
        } catch (error) {
            addToast({ type: 'critical', title: 'Error', message: 'Failed to trigger alert' });
        } finally {
            setTriggerLoading(false);
        }
    };

    const getSeverityClass = (severity) => `badge-${severity?.toLowerCase()}`;

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
                <h1 className="header-title">Alerts</h1>
                <div className="header-actions">
                    <button className="btn btn-secondary" onClick={fetchAlerts}>
                        🔄 Refresh
                    </button>
                    <button
                        className="btn btn-danger"
                        onClick={handleTriggerAlert}
                        disabled={triggerLoading}
                    >
                        {triggerLoading ? '⏳ Generating...' : '🚨 Trigger Test Alert'}
                    </button>
                </div>
            </div>

            <div className="card">
                <p style={{ marginBottom: '16px', color: 'var(--text-secondary)' }}>
                    Showing {alerts.length} alerts. Alerts are automatically generated every 2-5 minutes.
                </p>

                <div className="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Alert ID</th>
                                <th>Patient</th>
                                <th>Room</th>
                                <th>Type</th>
                                <th>Severity</th>
                                <th>Value</th>
                                <th>Created</th>
                            </tr>
                        </thead>
                        <tbody>
                            {alerts.length === 0 ? (
                                <tr>
                                    <td colSpan="7" style={{ textAlign: 'center', padding: '32px' }}>
                                        No alerts found. Click "Trigger Test Alert" to create one.
                                    </td>
                                </tr>
                            ) : (
                                alerts.map(alert => (
                                    <tr key={alert.alert_id}>
                                        <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>{alert.alert_id}</td>
                                        <td>{alert.patient_id}</td>
                                        <td>{alert.room || 'N/A'}</td>
                                        <td>{alert.alert_type?.replace('_', ' ')}</td>
                                        <td>
                                            <span className={`badge ${getSeverityClass(alert.severity)}`}>
                                                {alert.severity}
                                            </span>
                                        </td>
                                        <td>{alert.value}</td>
                                        <td>{new Date(alert.created_at).toLocaleString()}</td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}

export default Alerts;
