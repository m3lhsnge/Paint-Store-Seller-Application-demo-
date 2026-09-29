// ─── REPORTS PAGE ─────────────────────────────────────────────────────
registerPage('#reports', 'Raporlar', async () => {
  return renderReports();
}, { roles: ['ADMIN', 'YETKILI'] });

async function renderReports() {
  const recipes = await api.getRecipes();

  // Müşteri bazlı gruplama
  const byCustomer = {};
  recipes.forEach(r => {
    const key = r.customer_name || 'Bilinmeyen';
    if (!byCustomer[key]) byCustomer[key] = { count: 0, totalCost: 0, totalSell: 0 };
    byCustomer[key].count++;
    byCustomer[key].totalCost += parseFloat(r.total_cost || 0);
    byCustomer[key].totalSell += parseFloat(r.final_selling_price || 0);
  });

  const totalCost = recipes.reduce((s, r) => s + parseFloat(r.total_cost || 0), 0);
  const totalSell = recipes.reduce((s, r) => s + parseFloat(r.final_selling_price || 0), 0);
  const totalProfit = totalSell - totalCost;
  const avgMargin = recipes.length ? recipes.reduce((s, r) => s + parseFloat(r.margin_percentage || 0), 0) / recipes.length : 0;

  return `
  <div class="stats-grid report-summary">
    <div class="stat-card">
      <div class="stat-icon blue">${icons.barChart}</div>
      <div class="stat-info">
        <div class="stat-label">Toplam Reçete</div>
        <div class="stat-value">${recipes.length}</div>
      </div>
    </div>
    <div class="stat-card">
      <div class="stat-icon orange">${icons.box}</div>
      <div class="stat-info">
        <div class="stat-label">Toplam Maliyet</div>
        <div class="stat-value" style="font-size:1.2rem">${fmtTL(totalCost)}</div>
      </div>
    </div>
    <div class="stat-card">
      <div class="stat-icon green">${icons.barChart}</div>
      <div class="stat-info">
        <div class="stat-label">Toplam Satış</div>
        <div class="stat-value" style="font-size:1.2rem">${fmtTL(totalSell)}</div>
      </div>
    </div>
    <div class="stat-card">
      <div class="stat-icon red">${icons.barChart}</div>
      <div class="stat-info">
        <div class="stat-label">Toplam Kar</div>
        <div class="stat-value" style="font-size:1.2rem;color:var(--success)">${fmtTL(totalProfit)}</div>
        <div class="stat-sub">Ort. %${fmt(avgMargin, 1)} marj</div>
      </div>
    </div>
  </div>

  <div class="card mb-4">
    <div class="card-header">
      <span class="card-title">Firma Bazlı Özet</span>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Firma</th>
            <th>Reçete Sayısı</th>
            <th>Toplam Maliyet</th>
            <th>Toplam Satış</th>
            <th>Kar</th>
          </tr>
        </thead>
        <tbody>
          ${Object.entries(byCustomer).length === 0 ? `<tr><td colspan="5"><div class="empty-state"><p>Veri yok</p></div></td></tr>` :
            Object.entries(byCustomer).sort((a,b) => b[1].totalSell - a[1].totalSell).map(([name, d]) => `
            <tr>
              <td><strong>${esc(name)}</strong></td>
              <td>${d.count}</td>
              <td>${fmtTL(d.totalCost)}</td>
              <td>${fmtTL(d.totalSell)}</td>
              <td style="color:var(--success);font-weight:600">${fmtTL(d.totalSell - d.totalCost)}</td>
            </tr>`).join('')}
        </tbody>
      </table>
    </div>
  </div>

  <div class="card">
    <div class="card-header">
      <span class="card-title">Tüm Reçeteler</span>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Renk</th>
            <th>Boya Kodu</th>
            <th>Müşteri</th>
            <th>Ağırlık</th>
            <th>Maliyet</th>
            <th>Marj</th>
            <th>Satış</th>
            <th>Kar</th>
            <th>Tarih</th>
          </tr>
        </thead>
        <tbody>
          ${recipes.map(r => `
          <tr>
            <td>${r.target_hex_code ? `<span class="color-swatch" style="background:${esc(r.target_hex_code)}"></span>` : '—'}</td>
            <td><strong>${esc(r.custom_paint_code)}</strong></td>
            <td>${esc(r.customer_name) || '—'}</td>
            <td>${fmt(r.total_weight_gr)} g</td>
            <td>${fmtTL(r.total_cost)}</td>
            <td>%${r.margin_percentage}</td>
            <td>${fmtTL(r.final_selling_price)}</td>
            <td style="color:var(--success);font-weight:600">${fmtTL(parseFloat(r.final_selling_price) - parseFloat(r.total_cost))}</td>
            <td class="text-muted text-sm">${new Date(r.created_at).toLocaleDateString('tr-TR')}</td>
          </tr>`).join('')}
        </tbody>
      </table>
    </div>
  </div>`;
}
