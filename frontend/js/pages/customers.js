// ─── CUSTOMERS PAGE ───────────────────────────────────────────────────
let _customers = [];

registerPage('#customers', 'Müşteriler', async () => {
  _customers = await api.getCustomers();

  return `
  <div class="flex justify-between items-center mb-4">
    <span class="badge badge-gray">${_customers.length} firma</span>
    <button class="btn btn-primary btn-sm" id="btn-add-cust">+ Firma Ekle</button>
  </div>

  <div class="card">
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Firma Adı</th>
            <th>İletişim</th>
            <th>Şube</th>
            <th>Kayıt Tarihi</th>
            <th>İşlem</th>
          </tr>
        </thead>
        <tbody id="cust-tbody">
          ${renderCustRows()}
        </tbody>
      </table>
    </div>
  </div>

  <!-- Firma Modal -->
  <div class="modal-overlay" id="modal-cust">
    <div class="modal">
      <div class="modal-header">
        <span class="modal-title" id="modal-cust-title">Firma Ekle</span>
        <button class="modal-close" onclick="closeModal('modal-cust')">${icons.x}</button>
      </div>
      <div class="modal-body">
        <input type="hidden" id="cust-id">
        <div class="form-group">
          <label>Firma Adı</label>
          <input type="text" id="cust-name" class="form-control" placeholder="Mert Metal Sanayi A.Ş.">
        </div>
        <div class="form-group">
          <label>İletişim Bilgisi</label>
          <textarea id="cust-contact" class="form-control" rows="2" placeholder="Telefon, e-posta..."></textarea>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" onclick="closeModal('modal-cust')">İptal</button>
        <button class="btn btn-primary" id="btn-save-cust">Kaydet</button>
      </div>
    </div>
  </div>`;
});

function renderCustRows() {
  if (!_customers.length) return `<tr><td colspan="5"><div class="empty-state"><p>Henüz firma eklenmemiş</p></div></td></tr>`;
  return _customers.map(c => `
    <tr>
      <td><strong>${esc(c.company_name)}</strong></td>
      <td class="text-muted text-sm">${esc(c.contact_info) || '—'}</td>
      <td><span class="badge badge-primary">${esc(c.branch_name)}</span></td>
      <td class="text-muted text-sm">${new Date(c.created_at).toLocaleDateString('tr-TR')}</td>
      <td class="td-actions">
        <button class="btn btn-ghost btn-icon btn-sm" title="Düzenle" onclick="editCust(${c.id})">${icons.edit}</button>
        <button class="btn btn-ghost btn-icon btn-sm" title="Sil" style="color:var(--danger)" onclick="deleteCust(${c.id})">${icons.trash}</button>
      </td>
    </tr>`).join('');
}

window.__init_customers = () => {
  document.getElementById('btn-add-cust')?.addEventListener('click', () => {
    document.getElementById('modal-cust-title').textContent = 'Firma Ekle';
    document.getElementById('cust-id').value = '';
    document.getElementById('cust-name').value = '';
    document.getElementById('cust-contact').value = '';
    openModal('modal-cust');
  });

  document.getElementById('btn-save-cust')?.addEventListener('click', async () => {
    const btn = document.getElementById('btn-save-cust');
    const id = document.getElementById('cust-id').value;
    const data = {
      company_name: document.getElementById('cust-name').value.trim(),
      contact_info: document.getElementById('cust-contact').value.trim() || null,
    };
    if (!data.company_name) { toast('Firma adı boş olamaz', 'error'); return; }
    try {
      setLoading(btn, true);
      if (id) await api.updateCustomer(id, data);
      else await api.createCustomer(data);
      closeModal('modal-cust');
      toast(id ? 'Firma güncellendi' : 'Firma eklendi');
      router.refresh();
    } catch(e) { toast(e.message, 'error'); } finally { setLoading(btn, false); }
  });
};

window.editCust = (id) => {
  const c = _customers.find(x => x.id === id);
  if (!c) return;
  document.getElementById('modal-cust-title').textContent = 'Firma Düzenle';
  document.getElementById('cust-id').value = c.id;
  document.getElementById('cust-name').value = c.company_name;
  document.getElementById('cust-contact').value = c.contact_info || '';
  openModal('modal-cust');
};

window.deleteCust = async (id) => {
  if (!confirm('Bu firmayı silmek istediğinize emin misiniz?')) return;
  try {
    await api.deleteCustomer(id);
    toast('Firma silindi');
    router.refresh();
  } catch(e) { toast(e.message, 'error'); }
};
