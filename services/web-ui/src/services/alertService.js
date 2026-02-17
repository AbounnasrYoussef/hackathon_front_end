import { alertApi } from './api';

const alertService = {
    // Get all alerts
    getAllAlerts: async () => {
        const response = await alertApi.get('/alerts');
        return response.data;
    },

    // Trigger a manual alert (for testing)
    triggerManualAlert: async () => {
        const response = await alertApi.post('/alerts/manual');
        return response.data;
    },

    // Health check
    healthCheck: async () => {
        const response = await alertApi.get('/health');
        return response.data;
    }
};

export default alertService;
