import axios from "axios";

const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export const api = axios.create({
  baseURL: apiBase,
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers = config.headers ?? {};
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});
