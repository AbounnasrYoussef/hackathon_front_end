import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function Login() {
    const [loginId, setLoginId] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const result = await login(loginId, password);
            if (result.success) {
                navigate('/');
            } else {
                setError(result.error);
            }
        } catch (err) {
            setError('An unexpected error occurred');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-container">
            <div className="login-card">
                <div className="login-header">
                    <div className="login-logo">🏥</div>
                    <h1 className="login-title">Patient Care Platform</h1>
                    <p className="login-subtitle">Hospital Incident Management System</p>
                </div>

                {error && (
                    <div className="login-error">
                        ⚠️ {error}
                    </div>
                )}

                <form className="login-form" onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label className="form-label" htmlFor="loginId">Employee ID</label>
                        <input
                            type="text"
                            id="loginId"
                            className="form-input"
                            placeholder="Enter your employee ID"
                            value={loginId}
                            onChange={(e) => setLoginId(e.target.value)}
                            required
                            disabled={loading}
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label" htmlFor="password">Password</label>
                        <input
                            type="password"
                            id="password"
                            className="form-input"
                            placeholder="Enter your password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            disabled={loading}
                        />
                    </div>

                    <button
                        type="submit"
                        className="btn btn-primary btn-lg"
                        disabled={loading}
                    >
                        {loading ? (
                            <>
                                <span className="loading-spinner" style={{ width: 20, height: 20 }}></span>
                                Signing in...
                            </>
                        ) : (
                            'Sign In'
                        )}
                    </button>
                </form>

                <div style={{ marginTop: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '14px' }}>
                    <p>Demo Credentials:</p>
                    <p style={{ marginTop: '8px' }}>
                        <code style={{ background: 'var(--bg-secondary)', padding: '4px 8px', borderRadius: '4px' }}>
                            N01 / password123
                        </code>
                    </p>
                </div>
            </div>
        </div>
    );
}

export default Login;
