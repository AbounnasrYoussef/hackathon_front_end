import { useState, useEffect } from 'react';
import oncallService from '../services/oncallService';
import { useNotifications } from '../context/NotificationContext';

function OnCall() {
    const [employees, setEmployees] = useState([]);
    const [loading, setLoading] = useState(true);
    const [roleFilter, setRoleFilter] = useState('');
    const { addToast } = useNotifications();

    useEffect(() => {
        fetchSchedules();
    }, []);

    const fetchSchedules = async () => {
        try {
            setLoading(true);
            const data = await oncallService.getSchedules();
            setEmployees(data.employees || data);
        } catch (error) {
            console.error('Failed to fetch schedules:', error);
            addToast({ type: 'critical', title: 'Error', message: 'Failed to load schedules' });
        } finally {
            setLoading(false);
        }
    };

    // Get unique roles
    const roles = [...new Set(employees.map(e => e.role))].sort();

    // Filter employees
    const filteredEmployees = roleFilter
        ? employees.filter(e => e.role === roleFilter)
        : employees;

    // Count logged in
    const loggedInCount = employees.filter(e => e.is_logged_in).length;

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
                <h1 className="header-title">On-Call Schedule</h1>
                <button className="btn btn-primary" onClick={fetchSchedules}>
                    🔄 Refresh
                </button>
            </div>

            {/* Stats */}
            <div className="stats-grid" style={{ marginBottom: '24px' }}>
                <div className="stat-card success">
                    <div className="stat-icon">👤</div>
                    <div className="stat-value">{loggedInCount}</div>
                    <div className="stat-label">Currently Logged In</div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon">👥</div>
                    <div className="stat-value">{employees.length}</div>
                    <div className="stat-label">Total Staff</div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon">🏷️</div>
                    <div className="stat-value">{roles.length}</div>
                    <div className="stat-label">Roles</div>
                </div>
            </div>

            {/* Filters */}
            <div className="filters-bar">
                <div className="filter-group">
                    <span className="filter-label">Role:</span>
                    <select
                        className="filter-select form-select"
                        value={roleFilter}
                        onChange={(e) => setRoleFilter(e.target.value)}
                    >
                        <option value="">All Roles</option>
                        {roles.map(role => (
                            <option key={role} value={role}>{role.replace('_', ' ')}</option>
                        ))}
                    </select>
                </div>
            </div>

            {/* Employees Grid */}
            <div className="grid-3">
                {filteredEmployees.map(employee => (
                    <div key={employee.employee_id} className="card" style={{ position: 'relative' }}>
                        {/* Status indicator */}
                        <div style={{
                            position: 'absolute',
                            top: '16px',
                            right: '16px',
                            width: '12px',
                            height: '12px',
                            borderRadius: '50%',
                            background: employee.is_logged_in ? 'var(--success)' : 'var(--text-muted)',
                            boxShadow: employee.is_logged_in ? '0 0 8px var(--success)' : 'none'
                        }}></div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
                            <div style={{
                                width: '48px',
                                height: '48px',
                                background: 'linear-gradient(135deg, var(--primary), var(--accent))',
                                borderRadius: '50%',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontWeight: 600,
                                fontSize: '18px'
                            }}>
                                {employee.name?.split(' ').map(n => n[0]).join('')}
                            </div>
                            <div>
                                <div style={{ fontWeight: 600, fontSize: '16px' }}>{employee.name}</div>
                                <div style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
                                    {employee.role?.replace('_', ' ')}
                                </div>
                            </div>
                        </div>

                        <div style={{ display: 'grid', gap: '8px', fontSize: '14px', color: 'var(--text-secondary)' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <span>Email</span>
                                <span style={{ color: 'var(--text-primary)' }}>{employee.email}</span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <span>Phone</span>
                                <span style={{ color: 'var(--text-primary)' }}>{employee.phone}</span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <span>Tier</span>
                                <span style={{ color: 'var(--text-primary)' }}>Tier {employee.tier}</span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <span>Shift</span>
                                <span style={{ color: 'var(--text-primary)' }}>
                                    {employee.shift_start_time?.slice(0, 5)} - {employee.shift_end_time?.slice(0, 5)}
                                </span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <span>Status</span>
                                <span className={`status-badge ${employee.is_logged_in ? 'status-resolved' : 'status-open'}`}>
                                    {employee.is_logged_in ? 'Online' : 'Offline'}
                                </span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default OnCall;
