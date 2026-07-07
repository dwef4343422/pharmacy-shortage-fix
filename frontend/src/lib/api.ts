import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle global errors here (e.g., redirect to login on 401)
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Helper for file uploads - clears Content-Type to let browser set it with boundary
export const uploadApi = axios.create({
  baseURL: API_URL,
  headers: {
    // No Content-Type - will be set automatically by browser for FormData
  },
});