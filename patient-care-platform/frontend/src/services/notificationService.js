import { notificationApi } from './api';

const notificationService = {
    // Get all notifications for an employee
    getNotifications: async (employeeId) => {
        const response = await notificationApi.get(`/notifications/${employeeId}`);
        return response.data;
    },

    // Mark a notification as read
    markAsRead: async (notificationId) => {
        const response = await notificationApi.patch(`/notifications/${notificationId}/read`);
        return response.data;
    },

    // Mark all notifications as read for an employee
    markAllAsRead: async (employeeId) => {
        const response = await notificationApi.patch(`/notifications/${employeeId}/read-all`);
        return response.data;
    },

    // Mark all notifications for a specific incident as read
    markIncidentNotificationsRead: async (incidentId) => {
        const response = await notificationApi.patch(`/incidents/${incidentId}/notifications/read`);
        return response.data;
    },

    // Health check
    healthCheck: async () => {
        const response = await notificationApi.get('/health');
        return response.data;
    }
};

export default notificationService;
