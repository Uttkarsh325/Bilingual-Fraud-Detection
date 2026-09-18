import axios, { AxiosInstance } from "axios";

// Always call through the Next.js API proxy routes (/api/...).
// This keeps the backend URL server-side, eliminates CORS issues,
// and works regardless of where the backend is deployed.
const BASE_URL = "/api";

export const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 60_000, // 60 s — voice processing may be slow
});

// Attach auth token if present (stored in localStorage by auth flow)
apiClient.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("fg_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Surface API error messages cleanly
apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    const message =
      err.response?.data?.detail ||
      err.response?.data?.message ||
      err.message ||
      "An unexpected error occurred";
    return Promise.reject(new Error(message));
  }
);
