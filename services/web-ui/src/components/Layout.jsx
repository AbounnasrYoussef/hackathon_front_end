import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useNotifications } from '../context/NotificationContext';

function Layout() {
    const { user, logout } = useAuth();
    const { unreadCount, toasts, removeToast } = useNotifications();
    const navigate = useNavigate();

    const handleLogout = async () => {
        await logout();
        navigate('/login');
    };

    return (
        <div className="app-container">
            {/* Sidebar */}
            <aside className="sidebar">
                <div className="sidebar-header">
                    <div className="sidebar-logo">
                        <span>🏥</span>
                        <span>PatientCare</span>
                    </div>
                </div>

                <nav className="sidebar-nav">
                    <NavLink to="/" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                        <span>📊</span>
                        <span>Dashboard</span>
                    </NavLink>

                    <NavLink to="/incidents" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                        <span>📋</span>
                        <span>Incidents</span>
                    </NavLink>

                    <NavLink to="/alerts" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                        <span>🚨</span>
                        <span>Alerts</span>
                    </NavLink>

                    <NavLink to="/oncall" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                        <span>👥</span>
                        <span>On-Call</span>
                    </NavLink>

                    <NavLink to="/metrics" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                        <span>📈</span>
                        <span>Metrics</span>
                    </NavLink>
                </nav>

                {/* User section at bottom */}
                <div style={{ padding: '16px', borderTop: '1px solid var(--border)' }}>
                    <div className="user-profile" onClick={handleLogout} title="Click to logout">
                        <div className="user-avatar">
                            {user?.name?.split(' ').map(n => n[0]).join('') || 'U'}
                        </div>
                        <div className="user-info">
                            <div className="user-name">{user?.name || 'User'}</div>
                            <div className="user-role">{user?.role?.replace('_', ' ') || 'Staff'}</div>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="main-content">
                {/* Top bar with notifications */}
                <div style={{
                    display: 'flex',
                    justifyContent: 'flex-end',
                    marginBottom: '16px'
                }}>
                    <button className="notification-btn" title="Notifications">
                        🔔
                        {unreadCount > 0 && (
                            <span className="notification-badge">{unreadCount > 99 ? '99+' : unreadCount}</span>
                        )}
                    </button>
                </div>

                {/* Page content */}
                <Outlet />
            </main>

            {/* Toast Notifications */}
            <div className="toast-container">
                {toasts.map(toast => (
                    <div key={toast.id} className={`toast toast-${toast.type}`}>
                        <span className="toast-icon">
                            {toast.type === 'success' ? '✅' :
                                toast.type === 'critical' ? '🚨' :
                                    toast.type === 'warning' ? '⚠️' : 'ℹ️'}
                        </span>
                        <div className="toast-content">
                            <div className="toast-title">{toast.title}</div>
                            <div className="toast-message">{toast.message}</div>
                        </div>
                        <button
                            style={{
                                background: 'none',
                                border: 'none',
                                color: 'var(--text-secondary)',
                                cursor: 'pointer',
                                fontSize: '16px'
                            }}
                            onClick={() => removeToast(toast.id)}
                        >
                            ✕
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default Layout;
