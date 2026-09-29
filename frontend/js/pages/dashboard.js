// ─── DASHBOARD ────────────────────────────────────────────────────────
registerPage('#dashboard', 'Anasayfa', async () => {
  const [recipes, materials, customers] = await Promise.all([
    api.getRecipes(),
    api.getMaterials(),
    api.getCustomers(),
  ]);

  const totalCost = recipes.reduce((s, r) => s + parseFloat(r.total_cost || 0), 0);
  const avgCostPerKg = recipes.length
    ? recipes.reduce((s, r) => s + parseFloat(r.cost_per_kg || 0), 0) / recipes.length
    : 0;

  const recentRecipes = [...recipes].sort((a, b) => new Date(b.created_at) - new Date(a.created_at)).slice(0, 5);

  return `
  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-icon blue">${icons.droplet}</div>
      <div class="stat-info">
        <div class="stat-label">Toplam Reçete</div>
        <div class="stat-value">${recipes.length}</div>
        <div class="stat-sub">Bu şubeye ait</div>
      </div>
    </div>
    <div class="stat-card">
      <div class="stat-icon green">${icons.box}</div>
      <div class="stat-info">
        <div class="stat-label">Hammadde</div>
        <div class="stat-value">${materials.length}</div>
        <div class="stat-sub">Aktif malzeme</div>
      </div>
    </div>
    <div class="stat-card">
      <div class="stat-icon orange">${icons.users}</div>
      <div class="stat-info">
        <div class="stat-label">Müşteri / Firma</div>
        <div class="stat-value">${customers.length}</div>
        <div class="stat-sub">Kayıtlı firma</div>
      </div>
    </div>
    <div class="stat-card">
      <div class="stat-icon red">${icons.barChart}</div>
      <div class="stat-info">
        <div class="stat-label">Ort. KG Maliyet</div>
        <div class="stat-value">${fmt(avgCostPerKg)}</div>
        <div class="stat-sub">₺ / KG</div>
      </div>
    </div>
  </div>

  <div class="card">
    <div class="card-header">
      <span class="card-title">Son Reçeteler</span>
      <button class="btn btn-primary btn-sm" onclick="location.hash='#recipes'">Tümünü Gör</button>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Renk</th>
            <th>Boya Kodu</th>
            <th>Müşteri</th>
            <th>Ağırlık</th>
            <th>KG Maliyet</th>
            <th>Satış Fiyatı</th>
            <th>Tarih</th>
          </tr>
        </thead>
        <tbody>
          ${recentRecipes.length === 0 ? `<tr><td colspan="7"><div class="empty-state"><p>Henüz reçete yok</p></div></td></tr>` :
            recentRecipes.map(r => `
            <tr>
              <td><span class="color-swatch" style="background:${esc(r.target_hex_code) || '#ccc'}"></span></td>
              <td><strong>${esc(r.custom_paint_code)}</strong></td>
              <td>${esc(r.customer_name) || '—'}</td>
              <td>${fmt(r.total_weight_gr)} g</td>
              <td>${fmtTL(r.cost_per_kg)}</td>
              <td>${fmtTL(r.final_selling_price)}</td>
              <td class="text-muted text-sm">${new Date(r.created_at).toLocaleDateString('tr-TR')}</td>
            </tr>`).join('')}
        </tbody>
      </table>
    </div>
  </div>`;
});
