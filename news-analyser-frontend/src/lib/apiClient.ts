import axios from 'axios'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api/v1',
  timeout: 15_000,
  headers: { 'Content-Type': 'application/json' },
})

// Unwrap ApiResponse<T>.data on success
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message =
      error.response?.data?.error?.message ??
      error.message ??
      'An unexpected error occurred'
    return Promise.reject(new Error(message))
  }
)
