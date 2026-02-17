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
        const response = await notificationApi.patch(`/notifications/employee/${employeeId}/mark-all-read`);
        return response.data;
    },

    // Mark all notifications for a specific incident as read
    markIncidentNotificationsRead: async (incidentId, employeeId) => {
        const response = await notificationApi.patch(`/notifications/incident/${incidentId}/mark-read`, {
            employee_id: employeeId
        });
        return response.data;
    },

    // Health check
    healthCheck: async () => {
        const response = await notificationApi.get('/health');
        return response.data;
    }
};

export default notificationService;
