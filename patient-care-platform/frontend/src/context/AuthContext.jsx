import { createContext, useContext, useState, useEffect } from 'react';
import oncallService from '../services/oncallService';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Check for saved user in localStorage
        const savedUser = localStorage.getItem('user');
        if (savedUser) {
            setUser(JSON.parse(savedUser));
        }
        setLoading(false);
    }, []);

    const login = async (loginId, password) => {
        try {
            const response = await oncallService.login(loginId, password);
            if (response.success) {
                const userData = response.employee;
                setUser(userData);
                localStorage.setItem('user', JSON.stringify(userData));
                return { success: true, user: userData };
            } else {
                return { success: false, error: response.error || 'Login failed' };
            }
        } catch (error) {
            console.error('Login error:', error);
            return {
                success: false,
                error: error.response?.data?.error || 'Connection failed. Please check if services are running.'
            };
        }
    };

    const logout = async () => {
        try {
            if (user) {
                await oncallService.logout(user.employee_id);
            }
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            setUser(null);
            localStorage.removeItem('user');
        }
    };

    const value = {
        user,
        loading,
        login,
        logout,
        isAuthenticated: !!user
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
