import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
});

// Add request interceptor for logging/auth if needed
apiClient.interceptors.request.use(
  (config) => {
    // TODO: Add authentication headers if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Unified error handling
    const errorMessage =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred';

    // Provide user-friendly error messages based on status code
    let userFriendlyMessage = errorMessage;
    if (error.response?.status === 404) {
      userFriendlyMessage = 'Resource not found. Please check your session ID.';
    } else if (error.response?.status === 400) {
      userFriendlyMessage = `Invalid request: ${errorMessage}`;
    } else if (error.response?.status === 409) {
      userFriendlyMessage = 'Game session has ended or is invalid.';
    } else if (error.response?.status >= 500) {
      userFriendlyMessage = 'Server error. Please try again later.';
    } else if (error.code === 'ECONNABORTED') {
      userFriendlyMessage = 'Request timeout. Please check your connection.';
    }

    console.error('API Error:', {
      status: error.response?.status,
      message: errorMessage,
      data: error.response?.data,
    });

    // Create enhanced error object
    const enhancedError = new Error(userFriendlyMessage);
    (enhancedError as any).status = error.response?.status;
    (enhancedError as any).originalError = error;

    return Promise.reject(enhancedError);
  }
);

export default apiClient;
