import { incidentApi } from './api';

const incidentService = {
    // Get all incidents with optional status filter
    getIncidents: async (status = null) => {
        const params = status ? { status } : {};
        const response = await incidentApi.get('/incidents', { params });
        return response.data;
    },

    // Get specific incident details with history
    getIncident: async (incidentId) => {
        const response = await incidentApi.get(`/incidents/${incidentId}`);
        return response.data;
    },

    // Claim an incident (allow any staff to take it)
    claimIncident: async (incidentId, data) => {
        const response = await incidentApi.patch(`/incidents/${incidentId}/claim`, data);
        return response.data;
    },

    // Acknowledge an incident (ASSIGNED → ACKNOWLEDGED)
    acknowledgeIncident: async (incidentId, employeeId, employeeName) => {
        const response = await incidentApi.patch(`/incidents/${incidentId}/acknowledge`, {
            employee_id: employeeId,
            employee_name: employeeName
        });
        return response.data;
    },

    // Start working on incident (ACKNOWLEDGED → IN_PROGRESS)
    startIncident: async (incidentId, employeeId, employeeName) => {
        const response = await incidentApi.patch(`/incidents/${incidentId}/start`, {
            employee_id: employeeId,
            employee_name: employeeName
        });
        return response.data;
    },

    // Add a progress note
    addNote: async (incidentId, employeeId, employeeName, note) => {
        const response = await incidentApi.post(`/incidents/${incidentId}/notes`, {
            employee_id: employeeId,
            employee_name: employeeName,
            note
        });
        return response.data;
    },

    // Resolve incident (IN_PROGRESS → RESOLVED)
    resolveIncident: async (incidentId, employeeId, employeeName, resolutionNotes) => {
        const response = await incidentApi.patch(`/incidents/${incidentId}/resolve`, {
            employee_id: employeeId,
            employee_name: employeeName,
            resolution_notes: resolutionNotes
        });
        return response.data;
    },

    // Get performance metrics
    getMetrics: async () => {
        const response = await incidentApi.get('/incidents/metrics');
        return response.data;
    },

    // Health check
    healthCheck: async () => {
        const response = await incidentApi.get('/health');
        return response.data;
    }
};

export default incidentService;
