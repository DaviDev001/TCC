// Se a página NÃO está na porta 8000 (Live Server, arquivo direto...), fala com o backend em localhost:8000.
// Para outro endereço, defina antes: <script>window.API_BASE='http://IP:PORTA'</script>
const API = window.API_BASE ?? (location.port === '8000' ? '' : 'http://localhost:8000');
const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
const R$ = (c) => (c / 100).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
const cents = (v) => Math.round(parseFloat(String(v).replace(',', '.')) * 100) || 0;
const num = (v) => parseFloat(String(v).replace(',', '.'));
const newKey = () => crypto.randomUUID?.() || Date.now() + '-' + Math.random().toString(36).slice(2);
const METHODS = { PIX: 'Pix', CREDIT: 'Crédito', DEBIT: 'Débito', CASH: 'Dinheiro', CHECK: 'Cheque', INSTALLMENT: 'Carnê' };
const S = { products: [], customers: [], suppliers: [], cart: [], pays: [], pitems: [], session: null, key: newKey() };

function toast(msg, err) {
  const t = $('#toast'); t.textContent = msg; t.className = 'show' + (err ? ' err' : '');
  clearTimeout(t._t); t._t = setTimeout(() => (t.className = ''), 4500);
}
async function api(path, method = 'GET', body) {
  const r = await fetch(API + path, {
    method, body: body ? JSON.stringify(body) : undefined,
    headers: { 'Content-Type': 'application/json', 'X-User': $('#user').value || 'system' },
  });
  const data = await r.json().catch(() => null);
  if (r.status === 405 || (r.status === 404 && !data)) throw new Error(`${method} ${API + path} → ${r.status}. A página precisa falar com o FastAPI (porta 8000). Abra http://localhost:8000`);
  if (!r.ok) {
    const d = data?.detail;
    throw new Error(Array.isArray(d) ? d.map((e) => e.loc.slice(1).join('.') + ': ' + e.msg).join('; ') : d || 'Erro ' + r.status);
  }
  return data;
}
// Envolve uma ação: mostra erros do backend em vez de quebrar silenciosamente
const safe = (fn) => async (...a) => { try { await fn(...a); } catch (e) { toast(e.message, true); } };

// ---------- navegação ----------
$$('nav button').forEach((b) => (b.onclick = () => {
  $$('nav button').forEach((x) => x.classList.toggle('on', x === b));
  $$('.tab').forEach((t) => (t.hidden = t.id !== 't-' + b.dataset.tab));
  ({ prod: loadProducts, est: loadProducts, car: loadReceivables })[b.dataset.tab]?.();
}));

// ---------- carregamentos ----------
const opts = (list, label) => list.map((x) => `<option value="${x.id}">${esc(label(x))}</option>`).join('');
const loadProducts = safe(async () => {
  S.products = await api('/products');
  const stock = await api('/stock');
  $('#plist').innerHTML = S.products.map((p) => `<option value="${esc(p.name)}">${esc(p.barcode || '')}</option>`).join('');
  const sel = opts(S.products, (p) => p.name);
  $('#pu-prod').innerHTML = sel; $('#ad-prod').innerHTML = sel;
  $('#prod-list').innerHTML = S.products.map((p) => `<tr><td>${esc(p.name)}</td><td>${esc(p.barcode || '')}</td><td>${p.unit}</td>
    <td>${R$(p.cost_cents)}</td><td>${p.current_price_cents == null ? '<small>sem preço</small>' : R$(p.current_price_cents)}</td><td>${+p.stock_balance}</td>
    <td><button class="sm" onclick="setPrice(${p.id})">Preço</button> <button class="sm" onclick="priceHistory(${p.id})">Histórico</button>
    <button class="sm" onclick="editProduct(${p.id})">Editar</button> <button class="sm danger" onclick="deactivate(${p.id})">Inativar</button></td></tr>`).join('');
  $('#est-list').innerHTML = stock.map((p) => `<tr><td>${esc(p.name)}</td><td>${p.unit}</td><td class="${+p.stock_balance <= 0 ? 'low' : ''}">${+p.stock_balance}</td></tr>`).join('');
});
const loadCustomers = safe(async () => {
  S.customers = await api('/customers');
  $('#sale-customer').innerHTML = '<option value="">— sem cliente —</option>' + opts(S.customers, (c) => c.name);
  $('#r-customer').innerHTML = '<option value="">Todos</option>' + opts(S.customers, (c) => c.name);
});
const loadSuppliers = safe(async () => { S.suppliers = await api('/suppliers'); $('#pu-sup').innerHTML = opts(S.suppliers, (s) => s.name); });

// ---------- caixa ----------
const loadSession = safe(async () => {
  S.session = await api('/cash-sessions/current');
  const open = !!S.session;
  $('#cash-open').hidden = open; $('#cash-close').hidden = !open;
  $('#cash-info').textContent = open ? `aberto (nº ${S.session.id})` : 'fechado';
  $('#cash-badge').textContent = open ? `Caixa ${S.session.id} aberto` : 'Caixa fechado';
});
const openCash = safe(async () => { await api('/cash-sessions/open', 'POST', { opening_cents: cents($('#opening').value) }); toast('Caixa aberto'); await loadSession(); });
const closeCash = safe(async () => {
  const r = await api(`/cash-sessions/${S.session.id}/close`, 'POST', { closing_cents: cents($('#closing').value) });
  toast(`Fechado. Esperado ${R$(r.expected_cents)} · contado ${R$(r.closing_cents)} · diferença ${R$(r.difference_cents)}`, r.difference_cents !== 0);
  await loadSession();
});

// ---------- venda ----------
const addItem = safe(async () => {
  const v = $('#item').value.trim(); if (!v) return;
  let p = S.products.find((x) => x.barcode === v || x.name.toLowerCase() === v.toLowerCase());
  if (!p) p = await api('/products/barcode/' + encodeURIComponent(v));
  if (p.current_price_cents == null) throw new Error(`"${p.name}" está sem preço`);
  const qty = num($('#qty').value);
  if (!(qty > 0)) throw new Error('Quantidade inválida');
  const ex = S.cart.find((i) => i.id === p.id);
  ex ? (ex.qty = +(ex.qty + qty).toFixed(3)) : S.cart.push({ id: p.id, name: p.name, price: p.current_price_cents, qty });
  $('#item').value = ''; $('#qty').value = '1'; $('#item').focus(); renderCart();
});
$('#item').addEventListener('keydown', (e) => e.key === 'Enter' && addItem());
const subtotal = () => S.cart.reduce((s, i) => s + Math.round(i.price * i.qty), 0);
const total = () => subtotal() - cents($('#discount').value);
const paid = () => S.pays.reduce((s, p) => s + p.amount_cents, 0);
function renderCart() {
  $('#cart').innerHTML = S.cart.map((i, k) => `<tr><td>${esc(i.name)}</td><td>${i.qty}</td><td>${R$(i.price)}</td><td>${R$(Math.round(i.price * i.qty))}</td><td><button class="sm danger" onclick="S.cart.splice(${k},1);renderCart()">✕</button></td></tr>`).join('');
  renderTotals();
}
function renderTotals() {
  $('#pays').innerHTML = S.pays.map((p, k) => `<tr><td>${METHODS[p.method]}</td><td>${R$(p.amount_cents)}</td><td><button class="sm danger" onclick="S.pays.splice(${k},1);renderTotals()">✕</button></td></tr>`).join('');
  const diff = total() - paid();
  $('#totals').innerHTML = `Total: <b>${R$(total())}</b><br>Pago: ${R$(paid())} · ` + (diff > 0 ? `<span class="low">Falta ${R$(diff)}</span>` : `Troco: ${R$(-diff)}`);
  $('#pamt').placeholder = diff > 0 ? (diff / 100).toFixed(2) : 'Valor R$';
}
function payFields() {
  const m = $('#pm').value, g = ['PIX', 'CREDIT', 'DEBIT'].includes(m) ? 'card' : m;
  $$('.x').forEach((e) => (e.hidden = !e.classList.contains('x-' + g)));
}
const addPay = safe(() => {
  const m = $('#pm').value, rest = total() - paid();
  const amount = $('#pamt').value ? cents($('#pamt').value) : Math.max(rest, 0);
  if (amount <= 0) throw new Error('Informe o valor do pagamento');
  let details = {};
  if (['PIX', 'CREDIT', 'DEBIT'].includes(m) && $('#nsu').value) details = { nsu: $('#nsu').value };
  if (m === 'CHECK') details = { bank: $('#ck-bank').value, number: $('#ck-num').value, holder: $('#ck-holder').value, due_date: $('#ck-due').value };
  if (m === 'INSTALLMENT') {
    if (!$('#sale-customer').value) throw new Error('Carnê exige selecionar o cliente');
    details = { installments: parseInt($('#in-n').value), first_due_date: $('#in-due').value };
  }
  S.pays.push({ method: m, amount_cents: amount, details });
  $('#pamt').value = ''; $('#nsu').value = ''; renderTotals();
});
const finishSale = safe(async () => {
  if (!S.session) throw new Error('Abra o caixa primeiro');
  if (!S.cart.length) throw new Error('Carrinho vazio');
  const body = {
    idempotency_key: S.key, cash_session_id: S.session.id,
    customer_id: +$('#sale-customer').value || null, discount_cents: cents($('#discount').value),
    items: S.cart.map((i) => ({ product_id: i.id, qty: i.qty })), payments: S.pays,
  };
  const sale = await api('/sales', 'POST', body);   // a mesma chave é reenviada em caso de falha → sem duplicar
  toast(`Venda nº ${sale.id} — ${R$(sale.total_cents)}` + (sale.change_cents ? ` · Troco ${R$(sale.change_cents)}` : ''));
  S.cart = []; S.pays = []; S.key = newKey(); $('#discount').value = '0'; renderCart(); loadProducts();
});
const cancelSale = safe(async () => {
  const id = $('#cancel-id').value; if (!id || !confirm(`Cancelar a venda ${id}?`)) return;
  await api(`/sales/${id}/cancel`, 'POST'); toast('Venda cancelada e estoque estornado'); loadProducts();
});

// ---------- produtos ----------
const createProduct = safe(async () => {
  await api('/products', 'POST', { name: $('#p-name').value, barcode: $('#p-bar').value || null, unit: $('#p-unit').value, cost_cents: cents($('#p-cost').value) });
  ['#p-name', '#p-bar', '#p-cost'].forEach((s) => ($(s).value = '')); toast('Produto cadastrado'); loadProducts();
});
const setPrice = safe(async (id) => {
  const v = prompt('Novo preço (R$):'); if (v === null) return;
  const when = prompt('Vigência (AAAA-MM-DD HH:MM) — deixe vazio para valer agora:');
  await api(`/products/${id}/prices`, 'POST', { price_cents: cents(v), effective_from: when ? when.replace(' ', 'T') : null });
  toast('Preço registrado'); loadProducts();
});
const priceHistory = safe(async (id) => {
  const h = await api(`/products/${id}/prices`);
  alert(h.length ? h.map((p) => `${new Date(p.effective_from).toLocaleString('pt-BR')} — ${R$(p.price_cents)} (${p.created_by})`).join('\n') : 'Sem histórico');
});
const editProduct = safe(async (id) => {
  const p = S.products.find((x) => x.id === id);
  const name = prompt('Nome:', p.name); if (name === null) return;
  const cost = prompt('Custo (R$):', (p.cost_cents / 100).toFixed(2)); if (cost === null) return;
  await api(`/products/${id}`, 'PUT', { name, cost_cents: cents(cost) }); toast('Produto atualizado'); loadProducts();
});
const deactivate = safe(async (id) => { if (confirm('Inativar produto?')) { await api(`/products/${id}`, 'PUT', { active: false }); loadProducts(); } });

// ---------- compras ----------
const createSupplier = safe(async () => {
  await api('/suppliers', 'POST', { name: $('#s-name').value, document: $('#s-doc').value || null, phone: $('#s-phone').value || null });
  ['#s-name', '#s-doc', '#s-phone'].forEach((s) => ($(s).value = '')); toast('Fornecedor cadastrado'); loadSuppliers();
});
function renderPurchase() {
  $('#pu-items').innerHTML = S.pitems.map((i, k) => `<tr><td>${esc(i.name)}</td><td>${i.qty}</td><td>${R$(i.unit_cost_cents)}</td><td><button class="sm danger" onclick="S.pitems.splice(${k},1);renderPurchase()">✕</button></td></tr>`).join('');
}
const addPurchaseItem = safe(() => {
  const id = +$('#pu-prod').value, qty = num($('#pu-qty').value);
  if (!id || !(qty > 0)) throw new Error('Informe produto e quantidade');
  S.pitems.push({ product_id: id, name: S.products.find((p) => p.id === id).name, qty, unit_cost_cents: cents($('#pu-cost').value) });
  $('#pu-qty').value = ''; $('#pu-cost').value = ''; renderPurchase();
});
const sendPurchase = safe(async () => {
  const items = S.pitems.map(({ product_id, qty, unit_cost_cents }) => ({ product_id, qty, unit_cost_cents }));
  const r = await api('/purchases', 'POST', { supplier_id: +$('#pu-sup').value, invoice_number: $('#pu-inv').value || null, items });
  toast(`Compra nº ${r.id} recebida — ${R$(r.total_cents)}`); S.pitems = []; $('#pu-inv').value = ''; renderPurchase(); loadProducts();
});

// ---------- estoque ----------
const adjustStock = safe(async () => {
  const r = await api('/stock/adjustments', 'POST', { product_id: +$('#ad-prod').value, qty_delta: num($('#ad-qty').value), type: $('#ad-type').value, reason: $('#ad-reason').value });
  toast('Novo saldo: ' + +r.stock_balance); $('#ad-qty').value = ''; $('#ad-reason').value = ''; loadProducts();
});

// ---------- carnê ----------
const createCustomer = safe(async () => {
  await api('/customers', 'POST', { name: $('#c-name').value, document: $('#c-doc').value || null, phone: $('#c-phone').value || null, credit_limit_cents: cents($('#c-limit').value) });
  ['#c-name', '#c-doc', '#c-phone', '#c-limit'].forEach((s) => ($(s).value = '')); toast('Cliente cadastrado'); await loadCustomers(); loadReceivables();
});
const loadReceivables = safe(async () => {
  const cid = $('#r-customer').value;
  const list = await api(`/receivables?status=${$('#r-status').value}` + (cid ? `&customer_id=${cid}` : ''));
  const today = new Date().toISOString().slice(0, 10);
  $('#rec-list').innerHTML = list.map((r) => `<tr class="${r.due_date < today && $('#r-status').value === 'OPEN' ? 'late' : ''}"><td>${r.id}</td>
    <td>${esc(S.customers.find((c) => c.id === r.customer_id)?.name)}</td><td>${r.sale_id}</td><td>${r.installment_no}</td>
    <td>${new Date(r.due_date + 'T00:00').toLocaleDateString('pt-BR')}</td><td>${R$(r.amount_cents)}</td><td>${R$(r.paid_cents)}</td>
    <td>${$('#r-status').value === 'OPEN' ? `<button class="sm" onclick="pickRec(${r.id},${r.amount_cents - r.paid_cents})">Receber</button>` : ''}</td></tr>`).join('')
    || '<tr><td colspan="8"><small>Nenhuma parcela</small></td></tr>';
});
function pickRec(id, saldo) { $('#r-id').value = id; $('#r-amt').value = (saldo / 100).toFixed(2); }
const payReceivable = safe(async () => {
  const r = await api(`/receivables/${$('#r-id').value}/pay`, 'POST', { amount_cents: cents($('#r-amt').value), method: $('#r-method').value, cash_session_id: S.session?.id ?? null });
  toast(`Parcela ${r.id}: ${r.status === 'PAID' ? 'quitada' : 'pago ' + R$(r.paid_cents)}`); loadReceivables();
});

// ---------- fechamento ----------
const loadReport = safe(async () => {
  const r = await api('/reports/daily-closing?day=' + $('#rel-day').value);
  const tbl = (o) => Object.keys(o).length ? '<table>' + Object.entries(o).map(([m, v]) => `<tr><td>${METHODS[m] || m}</td><td>${R$(v)}</td></tr>`).join('') + '</table>' : '<small>—</small>';
  $('#rel-out').innerHTML = `<h3>${r.sales_count} venda(s) em ${new Date(r.date + 'T00:00').toLocaleDateString('pt-BR')}</h3>
    <b>Vendas por forma de pagamento</b> <small>(dinheiro já descontado o troco; carnê = a receber)</small>${tbl(r.sales_by_method_cents)}
    <br><b>Parcelas recebidas no dia</b>${tbl(r.receivables_received_cents)}`;
});

// ---------- init ----------
$('#rel-day').value = new Date().toLocaleDateString('sv');
payFields(); renderTotals();
loadSession(); loadProducts(); loadCustomers(); loadSuppliers();
$('#user').onchange = loadSession;
