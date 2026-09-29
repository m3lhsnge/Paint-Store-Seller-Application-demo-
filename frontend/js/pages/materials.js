// ─── MATERIALS PAGE ───────────────────────────────────────────────────
let _materials = [], _categories = [];
const canManage = () => auth.hasRole('ADMIN', 'YETKILI');

registerPage('#materials', 'Hammaddeler', async () => {
  [_materials, _categories] = await Promise.all([api.getMaterials(), api.getCategories()]);
  return buildMaterialsHTML();
});

function buildMaterialsHTML() {
  const grouped = {};
  _categories.forEach(c => { grouped[c.id] = { cat: c, items: [] }; });
  _materials.forEach(m => {
    if (grouped[m.category_id]) grouped[m.category_id].items.push(m);
    else grouped[0] = grouped[0] || { cat: { id: 0, name: 'Diğer' }, items: [] },
         grouped[0].items.push(m);
  });

  const sections = Object.values(grouped)
    .filter(g => g.items.length > 0)
    .map(g => `
    <div class="card mb-4">
      <div class="card-header" style="background:var(--bg)">
        <div class="flex items-center gap-3">
          <span class="card-title">${esc(g.cat.name)}</span>
          ${g.cat.allowed_branch
            ? `<span class="badge badge-warning" style="font-size:.7rem">${esc(g.cat.allowed_branch)}</span>`
            : `<span class="badge badge-success" style="font-size:.7rem">Genel</span>`}
          <span class="badge badge-gray">${g.items.length} malzeme</span>
        </div>
        ${canManage() ? `
        <button class="btn btn-secondary btn-sm" onclick="openAddMat(${g.cat.id})">
          ${icons.plus} Ekle
        </button>` : ''}
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th style="width:44px">Renk</th>
              <th>Hammadde Adı</th>
              <th style="width:180px;text-align:right">Birim Fiyat (₺/KG)</th>
              <th style="width:130px;text-align:center">Görünürlük</th>
              ${canManage() ? '<th style="width:160px;text-align:right">İşlem</th>' : ''}
            </tr>
          </thead>
          <tbody>
            ${g.items.map(m => `
            <tr>
              <td style="width:44px">
                ${m.hex_code
                  ? `<span class="color-swatch js-color" style="background:${esc(m.hex_code)};cursor:pointer"
                       data-hex="${esc(m.hex_code)}" data-name="${esc(m.name)}" title="Renk detayı"></span>`
                  : '<span style="color:var(--text-light);font-size:.8rem">—</span>'}
              </td>
              <td><strong>${esc(m.name)}</strong></td>
              <td style="text-align:right"><span style="font-weight:600">${fmt(m.price_per_kg)} ₺</span><span class="text-muted text-xs"> /KG</span></td>
              <td style="text-align:center">${m.allowed_branch
                    ? `<span class="badge badge-warning">${esc(m.allowed_branch)}</span>`
                    : '<span class="badge badge-success">Genel</span>'}</td>
              ${canManage() ? `
              <td style="text-align:right">
                <div class="td-actions" style="justify-content:flex-end">
                  <button class="btn btn-secondary btn-sm" onclick="editMat(${m.id})" title="Düzenle">
                    ${icons.edit} <span>Düzenle</span>
                  </button>
                  <button class="btn btn-danger btn-sm" onclick="deleteMat(${m.id})" title="Sil">
                    ${icons.trash}
                  </button>
                </div>
              </td>` : ''}
            </tr>`).join('')}
          </tbody>
        </table>
      </div>
    </div>`).join('');

  return `
  <div class="flex justify-between items-center mb-4">
    <span class="badge badge-gray">${_materials.length} hammadde · ${_categories.length} kategori</span>
    ${canManage() ? `
    <div class="flex gap-2">
      <button class="btn btn-secondary btn-sm" id="btn-add-cat">+ Kategori Ekle</button>
      <button class="btn btn-primary btn-sm" onclick="openAddMat(null)">+ Hammadde Ekle</button>
    </div>` : ''}
  </div>

  ${sections || `<div class="card"><div class="empty-state"><p>Henüz hammadde eklenmemiş</p></div></div>`}

  <!-- Hammadde Modal -->
  <div class="modal-overlay" id="modal-mat">
    <div class="modal">
      <div class="modal-header">
        <span class="modal-title" id="modal-mat-title">Hammadde Ekle</span>
        <button class="modal-close" onclick="closeModal('modal-mat')">${icons.x}</button>
      </div>
      <div class="modal-body">
        <input type="hidden" id="mat-id">
        <div class="form-group">
          <label>Hammadde Adı</label>
          <input type="text" id="mat-name" class="form-control" placeholder="Pigment Red 101">
        </div>
        <div class="form-group">
          <label>Kategori</label>
          <select id="mat-category" class="form-select">
            ${_categories.map(c => `<option value="${c.id}">${esc(c.name)}</option>`).join('')}
          </select>
        </div>
        <div class="form-group">
          <label>Birim Fiyat (₺/KG)</label>
          <input type="number" id="mat-price" class="form-control" placeholder="120.00" step="0.01" min="0">
        </div>
        <div class="form-group" style="margin-bottom:0">
          <label>HEX Renk Kodu <span class="text-muted text-xs">(opsiyonel — sadece pigmentler için)</span></label>
          <div class="flex gap-2 items-center">
            <input type="text" id="mat-hex" class="form-control" placeholder="#FF0000" maxlength="7">
            <input type="color" id="mat-hex-picker" style="width:38px;height:38px;border:1.5px solid var(--border);border-radius:var(--radius-sm);cursor:pointer;padding:2px;background:var(--surface)">
          </div>
        </div>
        <div class="form-group" style="margin-top:1rem;margin-bottom:0">
          <label>Görünürlük (Şube Kısıtlaması)</label>
          <select id="mat-branch" class="form-select">
            <option value="">Genel — Tüm Şubeler</option>
            <option value="Şube A">Şube A</option>
            <option value="Şube B">Şube B</option>
          </select>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" onclick="closeModal('modal-mat')">İptal</button>
        <button class="btn btn-primary" id="btn-save-mat">Kaydet</button>
      </div>
    </div>
  </div>

  <!-- Kategori Modal -->
  <div class="modal-overlay" id="modal-cat">
    <div class="modal">
      <div class="modal-header">
        <span class="modal-title">Kategori Ekle</span>
        <button class="modal-close" onclick="closeModal('modal-cat')">${icons.x}</button>
      </div>
      <div class="modal-body">
        <div class="form-group" style="margin-bottom:0">
          <label>Kategori Adı</label>
          <input type="text" id="cat-name" class="form-control" placeholder="Pigmentler">
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" onclick="closeModal('modal-cat')">İptal</button>
        <button class="btn btn-primary" id="btn-save-cat">Kaydet</button>
      </div>
    </div>
  </div>`;
}

// ─── ADD MAT WITH PRESET CATEGORY ────────────────────────────────────
window.openAddMat = (catId) => {
  document.getElementById('modal-mat-title').textContent = 'Hammadde Ekle';
  document.getElementById('mat-id').value = '';
  document.getElementById('mat-name').value = '';
  document.getElementById('mat-price').value = '';
  document.getElementById('mat-hex').value = '';
  document.getElementById('mat-hex-picker').value = '#ffffff';
  document.getElementById('mat-branch').value = '';
  if (catId !== null) {
    const sel = document.getElementById('mat-category');
    if (sel) sel.value = catId;
  }
  openModal('modal-mat');
};

window.__init_materials = () => {
  if (!canManage()) return;

  // Renk picker senkronizasyonu
  document.getElementById('mat-hex')?.addEventListener('input', e => {
    const v = e.target.value;
    if (/^#[0-9a-fA-F]{6}$/.test(v))
      document.getElementById('mat-hex-picker').value = v;
  });
  document.getElementById('mat-hex-picker')?.addEventListener('input', e => {
    document.getElementById('mat-hex').value = e.target.value;
  });

  document.getElementById('btn-add-cat')?.addEventListener('click', () => {
    document.getElementById('cat-name').value = '';
    openModal('modal-cat');
  });

  document.getElementById('btn-save-mat')?.addEventListener('click', async () => {
    const btn = document.getElementById('btn-save-mat');
    const id = document.getElementById('mat-id').value;
    const hexVal = document.getElementById('mat-hex').value.trim();
    const branchVal = document.getElementById('mat-branch').value;
    const data = {
      name: document.getElementById('mat-name').value.trim(),
      category_id: parseInt(document.getElementById('mat-category').value),
      price_per_kg: parseFloat(document.getElementById('mat-price').value),
      hex_code: /^#[0-9a-fA-F]{6}$/.test(hexVal) ? hexVal : null,
      allowed_branch: branchVal || null,
    };
    if (!data.name || isNaN(data.price_per_kg)) { toast('Lütfen ad ve fiyat girin', 'error'); return; }
    try {
      setLoading(btn, true);
      if (id) await api.updateMaterial(id, data);
      else await api.createMaterial(data);
      closeModal('modal-mat');
      toast(id ? 'Hammadde güncellendi' : 'Hammadde eklendi');
      router.refresh();
    } catch(e) { toast(e.message, 'error'); } finally { setLoading(btn, false); }
  });

  document.getElementById('btn-save-cat')?.addEventListener('click', async () => {
    const btn = document.getElementById('btn-save-cat');
    const name = document.getElementById('cat-name').value.trim();
    if (!name) { toast('Kategori adı boş olamaz', 'error'); return; }
    try {
      setLoading(btn, true);
      await api.createCategory({ name });
      closeModal('modal-cat');
      toast('Kategori eklendi');
      router.refresh();
    } catch(e) { toast(e.message, 'error'); } finally { setLoading(btn, false); }
  });
};

window.editMat = (id) => {
  const m = _materials.find(x => x.id === id);
  if (!m) return;
  document.getElementById('modal-mat-title').textContent = 'Hammadde Düzenle';
  document.getElementById('mat-id').value = m.id;
  document.getElementById('mat-name').value = m.name;
  document.getElementById('mat-price').value = m.price_per_kg;
  document.getElementById('mat-hex').value = m.hex_code || '';
  document.getElementById('mat-hex-picker').value = m.hex_code || '#ffffff';
  document.getElementById('mat-branch').value = m.allowed_branch || '';
  const sel = document.getElementById('mat-category');
  if (sel) sel.value = m.category_id;
  openModal('modal-mat');
};

window.deleteMat = async (id) => {
  if (!confirm('Bu hammaddeyi silmek istediğinize emin misiniz?')) return;
  try {
    await api.deleteMaterial(id);
    toast('Hammadde silindi');
    router.refresh();
  } catch(e) { toast(e.message, 'error'); }
};
