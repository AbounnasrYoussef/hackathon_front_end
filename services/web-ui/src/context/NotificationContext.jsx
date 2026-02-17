import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { io } from 'socket.io-client';
import { useAuth } from './AuthContext';
import notificationService from '../services/notificationService';

const NotificationContext = createContext(null);

const NOTIFICATION_SERVICE_URL = 'http://localhost:8004';

export function NotificationProvider({ children }) {
    const { user, isAuthenticated } = useAuth();
    const [socket, setSocket] = useState(null);
    const [notifications, setNotifications] = useState([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const [toasts, setToasts] = useState([]);

    // Connect to WebSocket when authenticated
    useEffect(() => {
        if (isAuthenticated && user) {
            const newSocket = io(NOTIFICATION_SERVICE_URL, {
                transports: ['websocket', 'polling']
            });

            newSocket.on('connect', () => {
                console.log('🔌 Connected to notification service');
                // Register employee for notifications
                newSocket.emit('register_employee', { employee_id: user.employee_id });
            });

            newSocket.on('disconnect', () => {
                console.log('🔌 Disconnected from notification service');
            });

            newSocket.on('incident_notification', (data) => {
                console.log('📬 Received notification:', data);
                // Add to notifications list
                setNotifications(prev => [data, ...prev]);
                setUnreadCount(prev => prev + 1);
                // Show toast
                addToast({
                    type: data.severity?.toLowerCase() || 'info',
                    title: data.title,
                    message: data.message
                });
            });

            setSocket(newSocket);

            // Fetch existing notifications
            fetchNotifications();

            return () => {
                newSocket.close();
            };
        }
    }, [isAuthenticated, user]);

    const fetchNotifications = async () => {
        if (!user) return;
        try {
            const data = await notificationService.getNotifications(user.employee_id);
            setNotifications(data.notifications || []);
            setUnreadCount(data.unread_count || 0);
        } catch (error) {
            console.error('Failed to fetch notifications:', error);
        }
    };

    const markAsRead = async (notificationId) => {
        try {
            await notificationService.markAsRead(notificationId);
            setNotifications(prev =>
                prev.map(n => n.notification_id === notificationId ? { ...n, is_read: true } : n)
            );
            setUnreadCount(prev => Math.max(0, prev - 1));
        } catch (error) {
            console.error('Failed to mark notification as read:', error);
        }
    };

    const markAllAsRead = async () => {
        if (!user) return;
        try {
            await notificationService.markAllAsRead(user.employee_id);
            setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
            setUnreadCount(0);
        } catch (error) {
            console.error('Failed to mark all notifications as read:', error);
        }
    };

    const addToast = useCallback((toast) => {
        const id = Date.now();
        setToasts(prev => [...prev, { ...toast, id }]);
        // Auto-remove after 5 seconds
        setTimeout(() => {
            setToasts(prev => prev.filter(t => t.id !== id));
        }, 5000);
    }, []);

    const removeToast = useCallback((id) => {
        setToasts(prev => prev.filter(t => t.id !== id));
    }, []);

    const value = {
        notifications,
        unreadCount,
        toasts,
        markAsRead,
        markAllAsRead,
        addToast,
        removeToast,
        refreshNotifications: fetchNotifications
    };

    return (
        <NotificationContext.Provider value={value}>
            {children}
        </NotificationContext.Provider>
    );
}

export function useNotifications() {
    const context = useContext(NotificationContext);
    if (!context) {
        throw new Error('useNotifications must be used within a NotificationProvider');
    }
    return context;
}
