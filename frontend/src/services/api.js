import axios from "axios";

const BASE = import.meta.env.VITE_API_URL || "/api";

const TOKENS = {
  get access() {
    return localStorage.getItem("tc_access");
  },
  get refresh() {
    return localStorage.getItem("tc_refresh");
  },
  set({ access, refresh }) {
    if (access) localStorage.setItem("tc_access", access);
    if (refresh) localStorage.setItem("tc_refresh", refresh);
  },
  clear() {
    localStorage.removeItem("tc_access");
    localStorage.removeItem("tc_refresh");
  },
};

const api = axios.create({ baseURL: BASE });

api.interceptors.request.use((config) => {
  const token = TOKENS.access;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let refreshing = null;

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    const status = error.response?.status;

    if (status === 401 && !original._retry && TOKENS.refresh) {
      original._retry = true;
      try {
        refreshing =
          refreshing ||
          axios.post(`${BASE}/auth/refresh/`, { refresh: TOKENS.refresh });
        const { data } = await refreshing;
        refreshing = null;
        TOKENS.set({ access: data.access });
        original.headers.Authorization = `Bearer ${data.access}`;
        return api(original);
      } catch (e) {
        refreshing = null;
        TOKENS.clear();
        window.dispatchEvent(new Event("tc:logout"));
      }
    }
    return Promise.reject(error);
  }
);

// -------------------------------------------------------------------- Auth
export const authApi = {
  register: (payload) => api.post("/auth/register/", payload),
  login: async (payload) => {
    const { data } = await api.post("/auth/login/", payload);
    TOKENS.set(data);
    return data;
  },
  me: () => api.get("/auth/me/").then((r) => r.data),
  logout: () => TOKENS.clear(),
  hasSession: () => Boolean(TOKENS.access),
};

// ---------------------------------------------------------------- Articles
export const newsApi = {
  articles: (params) => api.get("/articles/", { params }).then((r) => r.data),
  article: (slug) => api.get(`/articles/${slug}/`).then((r) => r.data),
  trending: () => api.get("/articles/trending/").then((r) => r.data),
  sources: () => api.get("/sources/").then((r) => r.data),
  categories: () => api.get("/categories/").then((r) => r.data),
  tags: () => api.get("/tags/").then((r) => r.data),
};

// ------------------------------------------------------------------- Saved
export const savedApi = {
  list: () => api.get("/saved/").then((r) => r.data),
  save: (articleId) => api.post("/saved/", { article_id: articleId }),
  remove: (articleId) => api.delete(`/saved/by-article/${articleId}/`),
};

export default api;
