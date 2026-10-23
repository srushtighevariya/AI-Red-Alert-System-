import axios from "axios";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

// An expired or invalid login token: clear the session and return to the login page.
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const isLoginRequest = error.config?.url?.startsWith("/auth/");

    if (error.response?.status === 401 && !isLoginRequest && localStorage.getItem("access_token")) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");
      window.location.reload();
    }

    return Promise.reject(error);
  }
);

export default apiClient;
