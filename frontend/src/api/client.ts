import axios, { AxiosRequestConfig, InternalAxiosRequestConfig } from 'axios';
import { ApiError } from '@/types/api';

const DEFAULT_BASE_URL = 'http://localhost:8000/api/v1';
const TIMEOUT_MS = 30000;
const MAX_RETRIES = 2;
const RETRY_DELAY_MS = 1000;

function getBaseURL(): string {
  const env = (import.meta as { env?: { VITE_API_URL?: string } }).env?.VITE_API_URL;
  if (typeof env === 'string' && env.trim()) return env.trim();
  return DEFAULT_BASE_URL;
}

const apiClient = axios.create({
  baseURL: getBaseURL(),
  headers: { 'Content-Type': 'application/json' },
  timeout: TIMEOUT_MS,
});

function isRetryableError(error: unknown): boolean {
  const apiErr = error instanceof ApiError ? error : ApiError.fromAxios(error);
  return apiErr.retryable;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function requestWithRetry<T>(config: InternalAxiosRequestConfig, retriesLeft: number): Promise<T> {
  try {
    const response = await apiClient.request<T>(config);
    return response.data;
  } catch (error) {
    const apiError = error instanceof ApiError ? error : ApiError.fromAxios(error);
    if (retriesLeft > 0 && isRetryableError(apiError)) {
      await sleep(RETRY_DELAY_MS * (MAX_RETRIES - retriesLeft + 1));
      return requestWithRetry(config, retriesLeft - 1);
    }
    throw apiError;
  }
}

// Request interceptor: optional auth / logging
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Add authentication headers when needed
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: normalize all errors to ApiError (no retry here; retry is in requestWithRetry)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const apiError = ApiError.fromAxios(error);
    console.error('API Error:', {
      status: apiError.status,
      code: apiError.code,
      message: apiError.message,
    });
    return Promise.reject(apiError);
  }
);

/**
 * Execute a request with optional retry for transient failures (5xx, timeout, network).
 * Use this for non-streaming calls that should be retried automatically.
 */
export async function apiRequest<T>(config: AxiosRequestConfig): Promise<T> {
  return requestWithRetry(config as InternalAxiosRequestConfig, MAX_RETRIES);
}

export default apiClient;
