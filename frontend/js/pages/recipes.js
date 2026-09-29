// ─── RECIPES PAGE (LIST) ──────────────────────────────────────────────
let _recipes = [];

registerPage('#recipes', 'Boyalar & Reçeteler', async () => {
  _recipes = await api.getRecipes();

  return `
  <div class="flex justify-between items-center mb-4">
    <span class="badge badge-gray">${_recipes.length} reçete</span>
    <button class="btn btn-primary btn-sm" id="btn-new-recipe">+ Yeni Reçete</button>
  </div>

  <div class="card">
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Renk</th>
            <th>Boya Kodu</th>
            <th>Müşteri</th>
            <th>Ağırlık</th>
            <th>Maliyet (KG)</th>
            <th>Kar Marjı</th>
            <th>Satış Fiyatı</th>
            <th>Tarih</th>
            <th>İşlem</th>
          </tr>
        </thead>
        <tbody>
          ${_recipes.length === 0 ? `<tr><td colspan="9"><div class="empty-state">
            <p>Henüz reçete oluşturulmamış. İlk reçetenizi oluşturun!</p>
            </div></td></tr>` :
            _recipes.map(r => `
            <tr>
              <td>${r.target_hex_code
                  ? `<span class="color-swatch js-color" style="background:${esc(r.target_hex_code)};cursor:pointer"
                       data-hex="${esc(r.target_hex_code)}" data-name="${esc(r.custom_paint_code)}" title="Renk detayı"></span>`
                  : '—'}</td>
              <td><strong>${esc(r.custom_paint_code)}</strong></td>
              <td>${esc(r.customer_name) || '<span class="text-muted">—</span>'}</td>
              <td>${fmt(r.total_weight_gr)} g</td>
              <td>${fmtTL(r.cost_per_kg)}</td>
              <td>${r.margin_percentage != null ? `%${r.margin_percentage}` : '—'}</td>
              <td><strong>${fmtTL(r.final_selling_price)}</strong></td>
              <td class="text-muted text-sm">${new Date(r.created_at).toLocaleDateString('tr-TR')}</td>
              <td class="td-actions">
                <button class="btn btn-ghost btn-icon btn-sm" title="Detay" onclick="viewRecipe(${r.id})">${icons.eye}</button>
                ${auth.hasRole('ADMIN','YETKILI') ? `<button class="btn btn-ghost btn-icon btn-sm" title="Sil" style="color:var(--danger)" onclick="deleteRecipe(${r.id})">${icons.trash}</button>` : ''}
              </td>
            </tr>`).join('')}
        </tbody>
      </table>
    </div>
  </div>

  <!-- Detay Modal -->
  <div class="modal-overlay" id="modal-recipe-detail">
    <div class="modal" style="max-width:600px">
      <div class="modal-header">
        <span class="modal-title" id="detail-title">Reçete Detayı</span>
        <button class="modal-close" onclick="closeModal('modal-recipe-detail')">${icons.x}</button>
      </div>
      <div class="modal-body" id="detail-body"></div>
      <div class="modal-footer">
        <button class="btn btn-secondary" onclick="closeModal('modal-recipe-detail')">Kapat</button>
      </div>
    </div>
  </div>`;
});

window.__init_recipes = () => {
  document.getElementById('btn-new-recipe')?.addEventListener('click', () => {
    location.hash = '#recipes/new';
  });
};

window.deleteRecipe = async (id) => {
  if (!confirm('Bu reçeteyi silmek istediğinize emin misiniz?')) return;
  try {
    await api.deleteRecipe(id);
    toast('Reçete silindi');
    router.refresh();
  } catch(e) { toast(e.message, 'error'); }
};

window.viewRecipe = async (id) => {
  try {
    const r = await api.getRecipe(id);
    document.getElementById('detail-title').textContent = r.custom_paint_code;
    document.getElementById('detail-body').innerHTML = `
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1rem">
        <div>
          <div class="stat-label">Müşteri</div><div class="font-medium">${esc(r.customer_name) || '—'}</div>
        </div>
        <div>
          <div class="stat-label">Tarih</div><div class="font-medium">${new Date(r.created_at).toLocaleDateString('tr-TR')}</div>
        </div>
        <div>
          <div class="stat-label">Toplam Ağırlık</div><div class="font-medium">${fmt(r.total_weight_gr)} g</div>
        </div>
        <div>
          <div class="stat-label">Toplam Maliyet</div><div class="font-medium">${fmtTL(r.total_cost)}</div>
        </div>
        <div>
          <div class="stat-label">KG Maliyet</div><div class="font-medium">${fmtTL(r.cost_per_kg)}</div>
        </div>
        <div>
          <div class="stat-label">Satış Fiyatı (%${r.margin_percentage} kar)</div>
          <div class="font-bold" style="color:var(--success);font-size:1.1rem">${fmtTL(r.final_selling_price)}</div>
        </div>
      </div>
      ${r.target_hex_code ? (() => {
        const rr=parseInt(r.target_hex_code.slice(1,3),16), gg=parseInt(r.target_hex_code.slice(3,5),16), bb=parseInt(r.target_hex_code.slice(5,7),16);
        const light=(rr*299+gg*587+bb*114)/1000>128;
        return `<div class="color-preview" style="background:${r.target_hex_code};color:${light?'#333':'#fff'}">
          ${r.target_hex_code} &nbsp;·&nbsp; RGB: ${rr}, ${gg}, ${bb}
        </div>`;
      })() : ''}
      <div class="summary-divider"></div>
      <div class="card-title mb-4">Hammadde Listesi</div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>#</th><th>Hammadde</th><th>Miktar (g)</th><th>Birim ₺/KG</th><th>Satır Maliyeti</th></tr></thead>
          <tbody>
            ${(r.items || []).map((item, i) => `
              <tr>
                <td>${i+1}</td>
                <td>${esc(item.raw_material_name || item.material_name) || '—'}</td>
                <td>${fmt(item.weight_gr)}</td>
                <td>${fmtTL(item.unit_price_at_time)}</td>
                <td>${fmtTL(item.line_cost)}</td>
              </tr>`).join('')}
          </tbody>
        </table>
      </div>`;
    openModal('modal-recipe-detail');
  } catch(e) { toast(e.message, 'error'); }
};
