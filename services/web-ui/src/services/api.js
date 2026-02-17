import axios from 'axios';

// API Base URLs for microservices
// Uses relative paths so requests route through nginx proxy (or Vite dev proxy)
const API_URLS = {
  alert: '',
  incident: '',
  oncall: '',
  notification: ''
};

// Create axios instances for each service
export const alertApi = axios.create({
  baseURL: API_URLS.alert,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

export const incidentApi = axios.create({
  baseURL: API_URLS.incident,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

export const oncallApi = axios.create({
  baseURL: API_URLS.oncall,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

export const notificationApi = axios.create({
  baseURL: API_URLS.notification,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Response interceptor for error handling
const handleResponse = (response) => response;

const handleError = (error) => {
  console.error('API Error:', error);
  if (error.response) {
    // Server responded with error
    console.error('Response data:', error.response.data);
    console.error('Response status:', error.response.status);
  } else if (error.request) {
    // Request made but no response
    console.error('No response received');
  }
  return Promise.reject(error);
};

alertApi.interceptors.response.use(handleResponse, handleError);
incidentApi.interceptors.response.use(handleResponse, handleError);
oncallApi.interceptors.response.use(handleResponse, handleError);
notificationApi.interceptors.response.use(handleResponse, handleError);

export default API_URLS;
