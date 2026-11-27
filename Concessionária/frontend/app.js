// Fala com o FastAPI: mesma origem na porta 8000; senão http://localhost:8000
const API = window.API_BASE ?? (location.port === '8000' ? '' : 'http://localhost:8000');
const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
const R$ = (c) => ((c || 0) / 100).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
const cents = (v) => { v = String(v ?? '').trim(); if (v.includes(',')) v = v.replace(/\./g, '').replace(',', '.'); return Math.round(parseFloat(v) * 100) || 0; };
const dt = (s) => new Date(s).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
const badge = (s) => `<span class="badge b-${s}">${s}</span>`;
const PAY = { PIX: 'Pix', TED: 'TED', DINHEIRO: 'Dinheiro', CARTAO: 'Cartão', CHEQUE: 'Cheque', FINANCIAMENTO: 'Financiamento', TROCA: 'Troca' };
const S = { vehicles: [], customers: [], sellers: [], leads: [], pays: [] };

function toast(m, err) { const t = $('#toast'); t.textContent = m; t.className = 'show' + (err ? ' err' : ''); clearTimeout(t._t); t._t = setTimeout(() => (t.className = ''), 4500); }
async function api(path, method = 'GET', body) {
  let r;
  try {
    r = await fetch(API + path, { method, body: body ? JSON.stringify(body) : undefined, headers: { 'Content-Type': 'application/json', 'X-User': $('#user').value || 'beta-1' } });
  } catch {
    throw new Error(`Sem conexão com o backend (${API || location.origin}). Confirme que o uvicorn está rodando e abra http://localhost:8000`);
  }
  const data = await r.json().catch(() => null);
  if (r.status === 405 || (r.status === 404 && !data)) throw new Error(`${method} ${API + path} → ${r.status}. Abra o sistema por http://localhost:8000`);
  if (!r.ok) { const d = data?.detail; throw new Error(Array.isArray(d) ? d.map((e) => e.loc.slice(1).join('.') + ': ' + e.msg).join('; ') : d || 'Erro ' + r.status); }
  return data;
}
const safe = (fn) => async (...a) => { try { await fn(...a); } catch (e) { toast(e.message, true); } };
const opts = (list, label, empty) => (empty ? `<option value="">${empty}</option>` : '') + list.map((x) => `<option value="${x.id}">${esc(label(x))}</option>`).join('');

// ---------- navegação ----------
const LOAD = { dash: () => loadDash(), est: () => loadVehicles(), lead: () => loadRefs().then(renderBoard), td: () => loadDrives(), venda: () => loadRefs().then(() => { loadSales(); renderSale(); }), cli: () => loadCustomers(), vend: () => loadRefs().then(renderSellers) };
function go(tab) {
  $$('nav button').forEach((b) => b.classList.toggle('on', b.dataset.tab === tab));
  $$('.tab').forEach((t) => (t.hidden = t.id !== 't-' + tab));
  LOAD[tab]?.();
}
$$('nav button').forEach((b) => (b.onclick = () => go(b.dataset.tab)));

// ---------- dados de referência ----------
const loadRefs = safe(async () => {
  [S.vehicles, S.customers, S.sellers, S.leads] = await Promise.all([api('/vehicles'), api('/customers'), api('/sellers'), api('/leads')]);
  const live = S.vehicles.filter((v) => v.status !== 'VENDIDO');
  const vlabel = (v) => `${v.desc} · ${v.plate || '0 km'}`;
  $('#l-vehicle').innerHTML = opts(live, vlabel, '— veículo de interesse —');
  $('#td-vehicle').innerHTML = opts(live, vlabel);
  const sale = S.vehicles.filter((v) => ['DISPONIVEL', 'RESERVADO'].includes(v.status) && v.price_cents > 0);
  const cur = $('#s-vehicle').value;
  $('#s-vehicle').innerHTML = opts(sale, (v) => `${vlabel(v)} — ${R$(v.price_cents)}`, '— selecione —'); $('#s-vehicle').value = cur;
  $('#s-customer').innerHTML = opts(S.customers, (c) => c.name, '— selecione —');
  const act = S.sellers.filter((s) => s.active);
  $('#s-seller').innerHTML = opts(act, (s) => s.name, '— selecione —');
  $('#l-seller').innerHTML = opts(act, (s) => s.name, '— vendedor —'); $('#td-seller').innerHTML = opts(act, (s) => s.name, '— vendedor —');
  $('#s-lead').innerHTML = opts(S.leads.filter((l) => !['GANHO', 'PERDIDO'].includes(l.status)), (l) => `${l.name} (${l.status})`, '— nenhum —');
});

// ---------- dashboard ----------
const loadDash = safe(async () => {
  const d = await api('/dashboard?month=' + $('#d-month').value);
  const k = (t, v, alt) => `<div class="kpi ${alt ? 'alt' : ''}"><small>${t}</small><b>${v}</b></div>`;
  $('#kpis').innerHTML = k('Veículos em estoque', d.stock.count) + k('Valor em estoque', R$(d.stock.value_cents)) + k('Vendas no mês', d.sales.count) +
    k('Faturamento', R$(d.sales.revenue_cents)) + k('Lucro bruto', R$(d.sales.profit_cents)) + k('Comissões', R$(d.sales.commission_cents), 1) +
    k('Tempo médio em estoque', d.stock.avg_days + ' dias', 1) + k('Parados > 90 dias', d.stock.stale_over_90, 1) + k('Test-drives (7 dias)', d.test_drives_next_7_days, 1);
  const bars = (o) => { const m = Math.max(1, ...Object.values(o)); return Object.entries(o).map(([n, v]) => `<div class="bar"><span>${n}</span><i style="width:${(v / m) * 60}%"></i><b>${v}</b></div>`).join('') || '<small>Sem dados</small>'; };
  $('#d-status').innerHTML = bars(d.stock.by_status); $('#d-funnel').innerHTML = bars(d.leads);
  $('#d-rank').innerHTML = d.ranking.map((r) => `<tr><td>${esc(r.seller)}</td><td>${r.sales}</td><td>${R$(r.revenue_cents)}</td><td>${R$(r.commission_cents)}</td></tr>`).join('') || '<tr><td colspan="4"><small>Nenhuma venda no mês</small></td></tr>';
});

// ---------- estoque ----------
const loadVehicles = safe(async () => {
  const q = encodeURIComponent($('#e-q').value), st = $('#e-status').value;
  const list = await api(`/vehicles?q=${q}` + (st ? `&status=${st}` : ''));
  $('#v-list').innerHTML = list.map((v) => { const m = v.price_cents - v.cost_cents; return `<tr><td><b>${esc(v.desc)}</b><br><small>${v.condition} · ${v.fuel} · ${v.transmission}</small></td><td>${esc(v.color)}</td><td>${esc(v.plate || '—')}</td><td>${v.km.toLocaleString('pt-BR')}</td>
    <td>${R$(v.cost_cents)}</td><td>${R$(v.price_cents)}</td><td class="${m < 0 ? 'low' : 'good'}">${R$(m)}</td><td>${badge(v.status)}</td>
    <td><button class="sm ghost" onclick="openVehicle(${v.id})">Detalhes</button> ${['DISPONIVEL', 'RESERVADO'].includes(v.status) ? `<button class="sm" onclick="startSale(${v.id})">Vender</button>` : ''}</td></tr>`; }).join('') || '<tr><td colspan="9"><small>Nenhum veículo</small></td></tr>';
});
const createVehicle = safe(async () => {
  const g = (i) => $('#v-' + i).value.trim() || null;
  await api('/vehicles', 'POST', { brand: g('brand'), model: g('model'), version: g('version'), year_fab: +g('yf'), year_model: +g('ym'), color: g('color'), plate: g('plate'), chassis: g('chassis'),
    km: +g('km') || 0, fuel: $('#v-fuel').value, transmission: $('#v-trans').value, condition: $('#v-cond').value, purchase_cents: cents($('#v-cost').value), price_cents: cents($('#v-price').value), notes: g('notes') });
  $$('#v-form input').forEach((i) => (i.value = '')); $('#v-form').hidden = true; toast('Veículo cadastrado'); loadVehicles();
});
const openVehicle = safe(async (id) => {
  const [v, h] = await Promise.all([api('/vehicles/' + id), api(`/vehicles/${id}/history`)]);
  const open = v.status !== 'VENDIDO';
  $('#dlg-body').innerHTML = `<h3>${esc(v.desc)} ${badge(v.status)}</h3>
    <p>${esc(v.color)} · ${v.km.toLocaleString('pt-BR')} km · Placa ${esc(v.plate || '—')} · Chassi ${esc(v.chassis || '—')}<br>
    Compra ${R$(v.purchase_cents)} + despesas ${R$(v.expenses_cents)} = <b>custo ${R$(v.cost_cents)}</b> · Preço <b>${R$(v.price_cents)}</b> · Margem <b>${R$(v.price_cents - v.cost_cents)}</b></p>
    ${open ? `<div class="row"><button class="sm" onclick="editPrice(${id})">Alterar preço</button>
      ${['DISPONIVEL', 'RESERVADO', 'MANUTENCAO'].filter((s) => s !== v.status).map((s) => `<button class="sm ghost" onclick="setStatus(${id},'${s}')">→ ${s}</button>`).join('')}
      <button class="sm danger" onclick="setStatus(${id},'BAIXADO')">Baixar do estoque</button></div>` : ''}
    <h3 style="margin-top:14px">Despesas / preparação</h3>
    <table>${v.expenses.map((e) => `<tr><td>${esc(e.description)}</td><td>${R$(e.amount_cents)}</td><td><small>${dt(e.created_at)}</small></td></tr>`).join('') || '<tr><td><small>Nenhuma</small></td></tr>'}</table>
    ${open ? `<div class="row" style="margin-top:8px"><input id="x-desc" placeholder="Ex.: polimento, pneus…" style="flex:1"><input id="x-amt" placeholder="R$" size="9"><button class="sm" onclick="addExpense(${id})">+ Despesa</button></div>` : ''}
    <h3 style="margin-top:14px">Histórico de alterações</h3><small>${h.map((x) => `${dt(x.at)} — ${x.action} (${esc(x.user)})`).join('<br>') || '—'}</small><br><br>`;
  $('#dlg').showModal();
});
const addExpense = safe(async (id) => { await api(`/vehicles/${id}/expenses`, 'POST', { description: $('#x-desc').value, amount_cents: cents($('#x-amt').value) }); toast('Despesa lançada'); openVehicle(id); loadVehicles(); });
const setStatus = safe(async (id, st) => { await api(`/vehicles/${id}/status`, 'PATCH', { status: st }); toast('Status: ' + st); $('#dlg').close(); loadVehicles(); });
const editPrice = safe(async (id) => { const p = prompt('Novo preço de venda (R$):'); if (p === null) return; await api('/vehicles/' + id, 'PUT', { price_cents: cents(p) }); toast('Preço atualizado'); $('#dlg').close(); loadVehicles(); });
function startSale(id) { $('#dlg').open && $('#dlg').close(); S.pays = []; go('venda'); setTimeout(() => { $('#s-vehicle').value = id; renderSale(); }, 400); }

// ---------- leads ----------
const COLS = ['NOVO', 'CONTATO', 'VISITA', 'PROPOSTA', 'GANHO', 'PERDIDO'], NEXT = { NOVO: 'CONTATO', CONTATO: 'VISITA', VISITA: 'PROPOSTA' };
function renderBoard() {
  $('#board').innerHTML = COLS.map((c) => { const ls = S.leads.filter((l) => l.status === c);
    return `<div class="col"><h4>${c} (${ls.length})</h4>${ls.map((l) => `<div class="lead"><b>${esc(l.name)}</b><small>${esc(l.phone || '')} · ${l.source}</small><small>${esc(l.vehicle || 'sem veículo')}</small>${l.lost_reason ? `<small>Motivo: ${esc(l.lost_reason)}</small>` : ''}
      <div class="row">${NEXT[c] ? `<button class="sm" onclick="moveLead(${l.id},'${NEXT[c]}')">→ ${NEXT[c]}</button>` : ''}${c === 'PROPOSTA' ? `<button class="sm" onclick="sellLead(${l.id})">Vender</button>` : ''}
      ${!['GANHO', 'PERDIDO'].includes(c) ? `<button class="sm danger" onclick="loseLead(${l.id})">Perdido</button>` : ''}</div></div>`).join('')}</div>`; }).join('');
}
const reloadLeads = async () => { await loadRefs(); renderBoard(); };
const createLead = safe(async () => {
  await api('/leads', 'POST', { name: $('#l-name').value, phone: $('#l-phone').value || null, email: $('#l-email').value || null, source: $('#l-source').value, vehicle_id: +$('#l-vehicle').value || null, seller_id: +$('#l-seller').value || null, notes: $('#l-notes').value || null });
  ['#l-name', '#l-phone', '#l-email', '#l-notes'].forEach((s) => ($(s).value = '')); toast('Lead criado'); reloadLeads();
});
const moveLead = safe(async (id, status) => { await api('/leads/' + id, 'PATCH', { status }); reloadLeads(); });
const loseLead = safe(async (id) => { const r = prompt('Motivo da perda:'); if (!r) return; await api('/leads/' + id, 'PATCH', { status: 'PERDIDO', lost_reason: r }); reloadLeads(); });
function sellLead(id) { const l = S.leads.find((x) => x.id === id); go('venda'); setTimeout(() => { if (l.vehicle_id) $('#s-vehicle').value = l.vehicle_id; $('#s-lead').value = id; if (l.seller_id) $('#s-seller').value = l.seller_id; renderSale(); }, 400); }

// ---------- test-drive ----------
const loadDrives = safe(async () => {
  await loadRefs(); const l = await api('/test-drives');
  $('#td-list').innerHTML = l.map((t) => `<tr><td>${dt(t.scheduled_at)}</td><td>${esc(t.vehicle)}</td><td>${esc(t.customer_name)}</td><td>${esc(t.phone || '')}</td><td>${badge(t.status)}</td>
    <td>${t.status === 'AGENDADO' ? `<button class="sm" onclick="driveStatus(${t.id},'REALIZADO')">Realizado</button> <button class="sm danger" onclick="driveStatus(${t.id},'CANCELADO')">Cancelar</button>` : ''}</td></tr>`).join('') || '<tr><td colspan="6"><small>Nenhum agendamento</small></td></tr>';
});
const scheduleDrive = safe(async () => {
  await api('/test-drives', 'POST', { vehicle_id: +$('#td-vehicle').value, customer_name: $('#td-name').value, phone: $('#td-phone').value || null, cnh: $('#td-cnh').value || null, seller_id: +$('#td-seller').value || null, scheduled_at: $('#td-when').value });
  ['#td-name', '#td-phone', '#td-cnh'].forEach((s) => ($(s).value = '')); toast('Test-drive agendado'); loadDrives();
});
const driveStatus = safe(async (id, status) => { await api('/test-drives/' + id, 'PATCH', { status }); loadDrives(); });

// ---------- vendas ----------
const selVehicle = () => S.vehicles.find((v) => v.id === +$('#s-vehicle').value);
const finalCents = () => (selVehicle()?.price_cents || 0) - cents($('#s-discount').value);
const paidCents = () => S.pays.reduce((s, p) => s + p.amount_cents, 0);
function renderSale() {
  const v = selVehicle(), fin = finalCents(), diff = fin - paidCents();
  $('#s-sum').innerHTML = v ? `Preço: ${R$(v.price_cents)} · Custo: ${R$(v.cost_cents)}<br>Valor final: <b>${R$(fin)}</b><br>Lucro estimado: <span class="${fin - v.cost_cents < 0 ? 'low' : 'good'}">${R$(fin - v.cost_cents)}</span><br>Pago: ${R$(paidCents())} · ${diff === 0 ? '<span class="good">Fechado ✔</span>' : `<span class="low">${diff > 0 ? 'Falta' : 'Excede'} ${R$(Math.abs(diff))}</span>`}` : '<small>Selecione um veículo</small>';
  $('#s-pays').innerHTML = S.pays.map((p, k) => `<tr><td>${PAY[p.method]}${p.details.bank ? ` · ${esc(p.details.bank)} ${p.details.installments}x` : ''}${p.details.plate ? ` · ${esc(p.details.brand)} ${esc(p.details.model)} ${esc(p.details.plate)}` : ''}</td><td>${R$(p.amount_cents)}</td><td><button class="sm danger" onclick="S.pays.splice(${k},1);renderSale()">✕</button></td></tr>`).join('');
}
function payFields() { const m = $('#pm').value; $$('.x').forEach((e) => (e.hidden = !e.classList.contains('x-' + m))); }
const addPay = safe(() => {
  const m = $('#pm').value, amt = $('#pamt').value ? cents($('#pamt').value) : finalCents() - paidCents();
  if (amt <= 0) throw new Error('Informe o valor do pagamento');
  let details = {};
  if (m === 'FINANCIAMENTO') details = { bank: $('#f-bank').value, installments: parseInt($('#f-n').value) };
  if (m === 'TROCA') details = { brand: $('#t-brand').value, model: $('#t-model').value, year: parseInt($('#t-year').value), plate: $('#t-plate').value, color: $('#t-color').value, km: parseInt($('#t-km').value) || 0 };
  S.pays.push({ method: m, amount_cents: amt, details }); $('#pamt').value = ''; renderSale();
});
const finishSale = safe(async () => {
  const s = await api('/sales', 'POST', { vehicle_id: +$('#s-vehicle').value, customer_id: +$('#s-customer').value, seller_id: +$('#s-seller').value, lead_id: +$('#s-lead').value || null,
    discount_cents: cents($('#s-discount').value), approved_by: $('#s-approved').value || null, payments: S.pays });
  toast(`Venda nº ${s.id} fechada — ${R$(s.final_cents)} · lucro ${R$(s.profit_cents)} · comissão ${R$(s.commission_cents)}`);
  S.pays = []; $('#s-discount').value = '0'; $('#s-approved').value = ''; $('#s-vehicle').value = ''; await loadRefs(); renderSale(); loadSales();
});
const loadSales = safe(async () => {
  const l = await api('/sales?month=' + $('#s-month').value);
  $('#s-list').innerHTML = l.map((s) => `<tr><td>${s.id}</td><td>${dt(s.created_at)}</td><td>${esc(s.vehicle)}<br><small>${esc(s.plate || '')}</small></td><td>${esc(s.customer)}</td><td>${esc(s.seller)}</td><td>${R$(s.final_cents)}${s.discount_cents ? `<br><small>desc. ${R$(s.discount_cents)}${s.approved_by ? ' (' + esc(s.approved_by) + ')' : ''}</small>` : ''}</td>
    <td class="${s.profit_cents < 0 ? 'low' : ''}">${R$(s.profit_cents)}</td><td>${R$(s.commission_cents)}</td><td><small>${s.payments.map((p) => PAY[p.method]).join(' + ')}</small></td>
    <td>${s.status === 'FECHADA' ? `<button class="sm danger" onclick="cancelSale(${s.id})">Cancelar</button>` : badge(s.status)}</td></tr>`).join('') || '<tr><td colspan="10"><small>Nenhuma venda no mês</small></td></tr>';
});
const cancelSale = safe(async (id) => { if (!confirm(`Cancelar a venda ${id}? O veículo volta ao estoque.`)) return; await api(`/sales/${id}/cancel`, 'POST'); toast('Venda cancelada'); await loadRefs(); loadSales(); });

// ---------- clientes e vendedores ----------
const loadCustomers = safe(async () => {
  const l = await api('/customers?q=' + encodeURIComponent($('#c-q').value));
  $('#c-list').innerHTML = l.map((c) => `<tr><td>${esc(c.name)}</td><td>${esc(c.document)}</td><td>${esc(c.phone || '')}</td><td>${esc(c.email || '')}</td><td>${esc(c.city || '')}</td></tr>`).join('') || '<tr><td colspan="5"><small>Nenhum cliente</small></td></tr>';
});
const createCustomer = safe(async () => {
  await api('/customers', 'POST', { name: $('#c-name').value, document: $('#c-doc').value, phone: $('#c-phone').value || null, email: $('#c-email').value || null, city: $('#c-city').value || null });
  ['#c-name', '#c-doc', '#c-phone', '#c-email', '#c-city'].forEach((s) => ($(s).value = '')); toast('Cliente cadastrado'); loadCustomers();
});
function renderSellers() {
  $('#sl-list').innerHTML = S.sellers.map((s) => `<tr><td>${esc(s.name)}</td><td>${s.commission_pct}%</td><td>${badge(s.active ? 'DISPONIVEL' : 'BAIXADO')}</td><td><button class="sm ghost" onclick="toggleSeller(${s.id})">${s.active ? 'Desativar' : 'Ativar'}</button></td></tr>`).join('');
}
const createSeller = safe(async () => { await api('/sellers', 'POST', { name: $('#sl-name').value, commission_pct: $('#sl-pct').value.replace(',', '.') }); $('#sl-name').value = ''; toast('Vendedor cadastrado'); await loadRefs(); renderSellers(); });
const toggleSeller = safe(async (id) => { await api(`/sellers/${id}/toggle`, 'PATCH'); await loadRefs(); renderSellers(); });

// ---------- init ----------
const ym = new Date().toLocaleDateString('sv').slice(0, 7);
$('#d-month').value = ym; $('#s-month').value = ym;
payFields(); loadDash(); loadRefs();
