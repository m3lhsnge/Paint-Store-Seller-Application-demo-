// ─── RECIPE BUILDER (NEW RECIPE) ──────────────────────────────────────
let _mats = [], _custs = [], _items = [], _simResult = null;

registerPage('#recipes/new', 'Yeni Reçete Oluştur', renderRecipeNew, {
  navRoute: '#recipes',
  init: initRecipeNew,
});

async function renderRecipeNew() {
  [_mats, _custs] = await Promise.all([api.getMaterials(), api.getCustomers()]);
  _items = [];
  _simResult = null;

  return `
  <div class="flex items-center gap-3 mb-4">
    <button class="btn btn-ghost btn-sm" onclick="location.hash='#recipes'">${icons.arrowLeft} Geri</button>
  </div>

  <div class="recipe-layout">
    <!-- SOL: Form -->
    <div>
      <!-- Boya Kodu + Firma -->
      <div class="card mb-4">
        <div class="card-body">
          <div class="recipe-header-row">
            <div class="form-group" style="margin:0">
              <label>Boya Kodu *</label>
              <input type="text" id="rec-code" class="form-control" placeholder="GRI-METAL-001">
            </div>
            <div class="form-group" style="margin:0">
              <label>Firma <span class="text-muted text-xs">(opsiyonel)</span></label>
              <select id="rec-customer" class="form-select">
                <option value="">— Firma seçin (opsiyonel) —</option>
                ${_custs.map(c => `<option value="${c.id}">${esc(c.company_name)}</option>`).join('')}
              </select>
            </div>
          </div>
          <div class="form-group mt-1" style="margin-bottom:0">
            <label>Notlar</label>
            <input type="text" id="rec-notes" class="form-control" placeholder="İsteğe bağlı not...">
          </div>
        </div>
      </div>

      <!-- Hammadde Tablosu -->
      <div class="card">
        <div class="card-header">
          <span class="card-title">Hammadde Listesi</span>
        </div>
        <div class="table-wrap recipe-items-table">
          <table>
            <thead>
              <tr>
                <th width="28">#</th>
                <th>Hammadde</th>
                <th>Kategori</th>
                <th>Miktar (g)</th>
                <th>Birim ₺/KG</th>
                <th>Satır Maliyeti</th>
                <th width="40"></th>
              </tr>
            </thead>
            <tbody id="items-tbody"></tbody>
          </table>
        </div>
        <div style="padding:.75rem 1.25rem; border-top:1px solid var(--border)">
          <button class="btn btn-secondary btn-sm" id="btn-add-item">
            ${icons.plus} Hammadde Ekle
          </button>
        </div>
      </div>
    </div>

    <!-- SAĞ: Özet -->
    <div class="summary-panel">
      <div class="summary-label">Toplam Maliyet</div>
      <div class="summary-value" id="sum-cost">0,00 ₺</div>
      <div class="summary-sub">Toplam Ağırlık</div>
      <div style="font-size:1rem;font-weight:600;color:var(--text-muted)" id="sum-weight">0 g</div>

      <div class="summary-divider"></div>

      <div class="summary-label">KG Birim Maliyet</div>
      <div style="font-size:1rem;font-weight:600;color:var(--text)" id="sum-cpkg">— ₺/KG</div>

      <div id="sum-color-wrap" style="display:none">
        <div class="color-preview" id="sum-color-box"></div>
        <div class="text-xs text-muted" id="sum-color-hex" style="text-align:center;margin-top:.25rem"></div>
      </div>

      <div class="summary-divider"></div>

      <div class="form-group">
        <label>Kar Marjı (%)</label>
        <input type="number" id="rec-margin" class="form-control" value="25" min="0" max="999" step="1">
      </div>
      <div class="summary-label" style="margin-top:.5rem">Satış Fiyatı</div>
      <div style="font-size:1.1rem;font-weight:700;color:var(--success)" id="sum-sell">— ₺</div>

      <div class="summary-divider"></div>

      <button class="btn btn-primary w-full btn-lg" id="btn-save-recipe">
        REÇETEYİ KAYDET
      </button>
    </div>
  </div>`;
}

function initRecipeNew() {
  renderItems();

  document.getElementById('btn-add-item')?.addEventListener('click', () => {
    _items.push({ material_id: _mats[0]?.id || '', weight_gr: 100 });
    renderItems();
    runSimulate();
  });

  document.getElementById('rec-margin')?.addEventListener('input', updateSell);
  document.getElementById('btn-save-recipe')?.addEventListener('click', saveRecipe);
}

function renderItems() {
  const tbody = document.getElementById('items-tbody');
  if (!tbody) return;
  if (!_items.length) {
    tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state" style="padding:1.5rem">
      <p>Hammadde eklemek için aşağıdaki butona tıklayın</p></div></td></tr>`;
    return;
  }
  tbody.innerHTML = _items.map((item, i) => {
    const mat = _mats.find(m => m.id == item.material_id) || _mats[0];
    const linePrice = mat ? (item.weight_gr / 1000) * parseFloat(mat.price_per_kg) : 0;
    const grouped = {};
    _mats.forEach(m => {
      const c = m.category_name || 'Diğer';
      if (!grouped[c]) grouped[c] = [];
      grouped[c].push(m);
    });
    const optionsHtml = Object.keys(grouped).map(cat => `
      <optgroup label="${esc(cat)}">
        ${grouped[cat].map(m => `<option value="${m.id}" ${m.id==item.material_id?'selected':''}>${esc(m.name)}</option>`).join('')}
      </optgroup>
    `).join('');

    return `
    <tr data-idx="${i}">
      <td style="color:var(--text-muted);font-size:.8rem">${i+1}</td>
      <td>
        <select class="form-select item-mat" data-idx="${i}" style="min-width:160px;font-size:.85rem;padding:.45rem .75rem">
          ${optionsHtml}
        </select>
      </td>
      <td><span class="badge badge-gray" style="font-size:.72rem">${esc(mat?.category_name) || '—'}</span></td>
      <td>
        <div class="flex items-center gap-2">
          <input type="number" class="qty-input item-qty" data-idx="${i}"
            value="${item.weight_gr}" min="0.01" step="any"
            style="width:90px">
          <span class="text-muted text-xs">g</span>
        </div>
      </td>
      <td class="text-sm">${mat ? fmtTL(mat.price_per_kg) : '—'}</td>
      <td><strong>${fmtTL(linePrice)}</strong></td>
      <td>
        <button class="btn btn-ghost btn-icon btn-sm item-remove" data-idx="${i}" style="color:var(--danger)">${icons.trash}</button>
      </td>
    </tr>`;
  }).join('');

  // Eventleri bind et (renderdan sonra)
  bindItemEvents();
}

function bindItemEvents() {
  document.querySelectorAll('.item-mat').forEach(sel => {
    sel.addEventListener('change', (e) => {
      const idx = parseInt(e.target.dataset.idx);
      _items[idx].material_id = parseInt(e.target.value);
      // Sadece o satırın görünen değerlerini güncelle, input'u yeniden render etme
      const row = e.target.closest('tr');
      const mat = _mats.find(m => m.id == _items[idx].material_id);
      if (mat && row) {
        row.cells[2].innerHTML = `<span class="badge badge-gray" style="font-size:.72rem">${esc(mat.category_name) || '—'}</span>`;
        row.cells[4].textContent = fmtTL(mat.price_per_kg);
        const w = _items[idx].weight_gr;
        row.cells[5].innerHTML = `<strong>${fmtTL((w/1000)*parseFloat(mat.price_per_kg))}</strong>`;
      }
      runSimulate();
    });
  });

  document.querySelectorAll('.item-qty').forEach(inp => {
    // input event: sadece _items'ı güncelle + satır maliyetini güncelle, tabloyu yeniden render etme
    inp.addEventListener('input', (e) => {
      const idx = parseInt(e.target.dataset.idx);
      const val = parseFloat(e.target.value);
      if (isNaN(val) || val <= 0) return;
      _items[idx].weight_gr = val;
      // Sadece o satırın toplam maliyetini güncelle
      const mat = _mats.find(m => m.id == _items[idx].material_id);
      if (mat) {
        const row = e.target.closest('tr');
        if (row) row.cells[5].innerHTML = `<strong>${fmtTL((val/1000)*parseFloat(mat.price_per_kg))}</strong>`;
      }
      runSimulate();
    });
  });

  document.querySelectorAll('.item-remove').forEach(btn => {
    btn.addEventListener('click', (e) => {
      _items.splice(parseInt(e.currentTarget.dataset.idx), 1);
      renderItems();
      runSimulate();
    });
  });
}

let _simTimer = null;
async function runSimulate() {
  clearTimeout(_simTimer);
  _simTimer = setTimeout(async () => {
    const validItems = _items.filter(i => i.material_id && i.weight_gr > 0);
    if (!validItems.length) { _simResult = null; updateSummary(null); return; }
    try {
      const res = await api.simulate({
        items: validItems.map(i => ({
          raw_material_id: parseInt(i.material_id),
          weight_gr: parseFloat(i.weight_gr)
        }))
      });
      _simResult = res;
      updateSummary(res);
    } catch(e) { console.warn('Simulate error:', e.message); }
  }, 500);
}

function updateSummary(res) {
  document.getElementById('sum-cost').textContent   = res ? fmtTL(res.total_cost) : '0,00 ₺';
  document.getElementById('sum-weight').textContent = res ? fmt(res.total_weight_gr) + ' g' : '0 g';
  document.getElementById('sum-cpkg').textContent   = res ? fmtTL(res.cost_per_kg) + '/KG' : '— ₺/KG';

  const colorWrap = document.getElementById('sum-color-wrap');
  const colorBox  = document.getElementById('sum-color-box');
  const colorHex  = document.getElementById('sum-color-hex');

  if (res?.mixed_hex_code) {
    colorWrap.style.display = '';
    colorBox.style.background = res.mixed_hex_code;
    colorBox.textContent = res.mixed_hex_code;
    colorBox.style.color = isLight(res.mixed_hex_code) ? '#333' : '#fff';
    const rgb = hexToRgb(res.mixed_hex_code);
    colorHex.textContent = `HEX: ${res.mixed_hex_code}  ·  RGB: ${rgb}`;
  } else {
    colorWrap.style.display = 'none';
  }

  updateSell();
}

function updateSell() {
  const marginEl = document.getElementById('rec-margin');
  const margin = marginEl ? (parseFloat(marginEl.value) ?? 0) : 0;
  if (!_simResult) { document.getElementById('sum-sell').textContent = '— ₺'; return; }
  const sell = _simResult.total_cost * (1 + margin / 100);
  document.getElementById('sum-sell').textContent = fmtTL(sell);
}

async function saveRecipe() {
  const btn = document.getElementById('btn-save-recipe');
  const code = document.getElementById('rec-code').value.trim();
  const customerVal = document.getElementById('rec-customer').value;
  const marginEl = document.getElementById('rec-margin');
  const margin = marginEl && marginEl.value !== '' ? parseFloat(marginEl.value) : null;
  const notes = document.getElementById('rec-notes').value.trim() || null;

  if (!code) { toast('Boya kodu boş olamaz', 'error'); return; }
  if (!_items.length) { toast('En az bir hammadde ekleyin', 'error'); return; }

  const validItems = _items.filter(i => i.material_id && i.weight_gr > 0);
  if (!validItems.length) { toast('Geçerli hammadde kaydı yok', 'error'); return; }

  const payload = {
    custom_paint_code: code,
    customer_id: customerVal ? parseInt(customerVal) : null,
    margin_percentage: margin,
    notes,
    items: validItems.map(i => ({
      raw_material_id: parseInt(i.material_id),
      weight_gr: parseFloat(i.weight_gr)
    })),
  };

  try {
    setLoading(btn, true);
    await api.createRecipe(payload);
    toast('Reçete kaydedildi!', 'success');
    setTimeout(() => { location.hash = '#recipes'; }, 600);
  } catch(e) { toast(e.message, 'error'); } finally { setLoading(btn, false); }
}
