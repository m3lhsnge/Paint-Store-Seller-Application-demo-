// ─── AUTH HELPERS ─────────────────────────────────────────────────────
const auth = {
  save(token, user) {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
  },

  clear() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },

  getUser() {
    try { return JSON.parse(localStorage.getItem('user')); }
    catch { return null; }
  },

  getToken() {
    return localStorage.getItem('token');
  },

  isLoggedIn() {
    return !!this.getToken();
  },

  hasRole(...roles) {
    const user = this.getUser();
    return user && roles.includes(user.role);
  },

  logout() {
    this.clear();
    window.location.href = 'login.html';
  }
};
