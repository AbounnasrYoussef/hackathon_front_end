import { oncallApi } from './api';

const oncallService = {
    // Employee login
    login: async (login, password) => {
        const response = await oncallApi.post('/oncall/login', { login, password });
        return response.data;
    },

    // Employee logout
    logout: async (employeeId) => {
        const response = await oncallApi.post('/oncall/logout', { employee_id: employeeId });
        return response.data;
    },

    // Get current on-call person for a role
    getCurrentOnCall: async (role) => {
        const response = await oncallApi.get('/oncall/current', { params: { role } });
        return response.data;
    },

    // Assign incident to on-call person
    assignIncident: async (incidentId, employeeId) => {
        const response = await oncallApi.post('/oncall/assign', {
            incident_id: incidentId,
            employee_id: employeeId
        });
        return response.data;
    },

    // Get all employees and their status
    getSchedules: async () => {
        const response = await oncallApi.get('/oncall/schedules');
        return response.data;
    },

    // Health check
    healthCheck: async () => {
        const response = await oncallApi.get('/health');
        return response.data;
    }
};

export default oncallService;
