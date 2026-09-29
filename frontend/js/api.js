// ─── API BASE ─────────────────────────────────────────────────────────
// Farklı ortam için sayfada script'lerden ÖNCE window.API_BASE_URL tanımlayın
const BASE_URL = (window.API_BASE_URL || 'http://localhost:8001') + '/api';

function getToken() {
  return localStorage.getItem('token');
}

async function request(method, path, body = null) {
  const headers = { 'Content-Type': 'application/json' };
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const opts = { method, headers };
  if (body) opts.body = JSON.stringify(body);

  const res = await fetch(BASE_URL + path, opts);

  if (res.status === 401) {
    localStorage.clear();
    window.location.href = 'login.html';
    return;
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Sunucu hatası' }));
    throw new Error(err.detail || 'Hata oluştu');
  }

  if (res.status === 204) return null;
  return res.json();
}

// ─── AUTH ──────────────────────────────────────────────────────────────
const api = {
  login: (username, password) =>
    request('POST', '/auth/login', { username, password }),

  me: () => request('GET', '/auth/me'),

  switchBranch: (branch_name) => request('POST', '/auth/switch-branch', { branch_name }),

  // ─── MATERIALS ──────────────────────────────────────────────────────
  getMaterials: () => request('GET', '/materials'),
  getCategories: () => request('GET', '/materials/categories'),
  createMaterial: (data) => request('POST', '/materials', data),
  updateMaterial: (id, data) => request('PUT', `/materials/${id}`, data),
  deleteMaterial: (id) => request('DELETE', `/materials/${id}`),
  createCategory: (data) => request('POST', '/materials/categories', data),

  // ─── CUSTOMERS ──────────────────────────────────────────────────────
  getCustomers: () => request('GET', '/customers'),
  createCustomer: (data) => request('POST', '/customers', data),
  updateCustomer: (id, data) => request('PUT', `/customers/${id}`, data),
  deleteCustomer: (id) => request('DELETE', `/customers/${id}`),

  // ─── RECIPES ────────────────────────────────────────────────────────
  getRecipes: () => request('GET', '/recipes'),
  getRecipe: (id) => request('GET', `/recipes/${id}`),
  createRecipe: (data) => request('POST', '/recipes', data),
  deleteRecipe: (id) => request('DELETE', `/recipes/${id}`),
  simulate: (data) => request('POST', '/recipes/simulate', data),
};
