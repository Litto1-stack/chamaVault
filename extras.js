// Extras on top of app.js: payment page, ledger check, loans (request -> vote -> payout -> installments), member statement.
// Uses app.js globals: state, save, render, showView, money, toast, sendSms, memberById, contribution, currentTotal, groupGoal, openModal, closeModal, PIN.
const $ = selector => document.querySelector(selector);
const val = id => document.getElementById(id)?.value ?? "";
const whole = text => { const clean = String(text).replace(/[,\s]/g, ""); return /^\d{1,9}$/.test(clean) ? Number(clean) : null; };
const stamp = () => new Date().toLocaleString("en-KE", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
const everyone = () => `All ${state.members.length} members`;
const nameOf = id => memberById(id)?.name || "Member";
const memberOptions = (selected, keep = () => true) => state.members.filter(keep).map(m => `<option value="${m.id}" ${m.id === selected ? "selected" : ""}>${escapeHtml(m.fullName)}</option>`).join("");
const LABEL = { contribution: "Monthly contribution", penalty: "Late penalty", installment: "Loan installment", savings: "Extra savings", welfare: "Welfare fund" };
const LATE_DAYS = 4;   // the demo treats an "overdue" member as 4 days late

function ensureExtras() {
  Object.assign(state.chama, { maxLoan: state.chama.maxLoan ?? 15000, interest: state.chama.interest ?? 10, approval: state.chama.approval ?? 60 });
  state.loans ||= [{ id: "L0", memberId: "w", principal: 8000, total: 8800, per: 2900, count: 3, paid: 1, repaid: 3000, status: "active", reason: "Emergency school fees" }];
  state.loanRequests ||= [];
  state.scoreLog ||= [];
  state.loans = state.loans.filter(l => memberById(l.memberId));
  state.loanRequests = state.loanRequests.filter(r => memberById(r.memberId));
}

// ---------- money rules ----------
const lateDays = m => m.lateDays ?? (m.status === "overdue" ? LATE_DAYS : 0);
const penaltyOwed = m => Math.max(0, lateDays(m) * Number(state.chama.latePenalty || 0) - (m.penaltyPaid || 0));
const loanOf = id => state.loans.find(l => l.memberId === id && l.status === "active");
const poolBalance = () => state.transactions.reduce((sum, tx) => sum + tx.amount, 0);
// Treasurer PIN check (payouts). Locks after 5 wrong tries. The PIN is never logged.
function pinOk(pin) {
  if ((state.pinFails || 0) >= 5) { toast("Too many wrong PIN attempts. Reset the demo from the ? menu.", true); return false; }
  if (pin !== state.treasurer.pin) { state.pinFails = (state.pinFails || 0) + 1; save(); toast("That PIN isn’t right. Check the treasurer PIN and try again.", true); return false; }
  state.pinFails = 0; return true;
}
function addScore(member, delta, reason) {
  member.score = Math.max(300, Math.min(850, member.score + delta));
  state.scoreLog.unshift({ memberId: member.id, delta, reason, time: stamp() });
}
function addTx(memberId, amount, kind, method, by, ref) {
  const tx = { id: `t${Date.now()}${Math.floor(Math.random() * 90 + 10)}`, memberId, amount, time: stamp(), method, by, balance: 0, status: "normal", kind, ref };
  state.transactions.unshift(tx);
  return tx;
}

// ---------- payment page ----------
let payAs = null;
function payItems(m) {
  const items = [];
  if (m.status !== "paid") items.push({ key: "contribution", amount: contribution(), fixed: true });
  if (penaltyOwed(m) > 0) items.push({ key: "penalty", amount: penaltyOwed(m), max: penaltyOwed(m) });
  const loan = loanOf(m.id);
  if (loan) items.push({ key: "installment", amount: Math.min(loan.per, loan.total - loan.repaid), fixed: true });
  items.push({ key: "savings", amount: 500, max: 500000 }, { key: "welfare", amount: 200, max: 500000 });
  return items;
}

function cardErrors(name, number, expiry, cvv) {
  const errors = [], digits = number.replace(/[\s-]/g, ""), m = /^(\d{2})\s*\/\s*(\d{2})$/.exec(expiry.trim()), now = new Date();
  if (name.trim().length < 2) errors.push("Enter the name on the card.");
  if (!/^\d{13,19}$/.test(digits)) errors.push("Card number must be 13 to 19 digits.");
  if (!m || +m[1] < 1 || +m[1] > 12) errors.push("Expiry must look like MM/YY.");
  else if (2000 + +m[2] < now.getFullYear() || (2000 + +m[2] === now.getFullYear() && +m[1] < now.getMonth() + 1)) errors.push("This card has expired.");
  if (!/^\d{3,4}$/.test(cvv)) errors.push("CVV must be 3 or 4 digits.");
  return errors;
}

function renderPay(preset = {}) {
  if (preset.memberId && memberById(preset.memberId)) payAs = preset.memberId;
  if (!memberById(payAs)) payAs = (state.members.find(m => m.status === "overdue") || state.members.find(m => m.status === "pending") || state.members[0]).id;
  const m = memberById(payAs), items = payItems(m), selected = items.some(i => i.key === preset.item) ? preset.item : items[0].key;
  $("#pay-content").innerHTML = `<div class="pay-grid"><form id="pay-form" class="surface pad" autocomplete="off" novalidate>
    <div class="form-field"><label for="pay-member">PAYING AS (DEMO)</label><select id="pay-member">${memberOptions(payAs)}</select></div>
    <div class="form-field"><label for="pay-item">1. WHAT ARE YOU PAYING FOR?</label><select id="pay-item">${items.map(i => `<option value="${i.key}" data-amount="${i.amount}" data-fixed="${i.fixed ? 1 : 0}" data-max="${i.max || ""}" ${i.key === selected ? "selected" : ""}>${LABEL[i.key]}${i.fixed ? ` (KES ${money(i.amount)})` : ""}</option>`).join("")}</select></div>
    <div class="form-field"><label for="pay-amount">2. AMOUNT (KES)</label><input id="pay-amount" class="amount-input" inputmode="numeric" /><small class="field-hint" id="pay-hint"></small></div>
    <div class="form-field"><label>3. PAY WITH</label><div class="method-tabs"><label><input type="radio" name="pay-method" value="M-Pesa" checked /><span>📱 M-Pesa</span></label><label><input type="radio" name="pay-method" value="Card" /><span>💳 Card</span></label></div></div>
    <div id="pay-mpesa-box"><p class="modal-note">A simulated STK push goes to <strong>${escapeHtml(m.phone)}</strong>. Enter your M-Pesa PIN to approve.</p><div class="form-field"><label for="mpesa-pin">M-PESA PIN</label><input id="mpesa-pin" type="password" inputmode="numeric" maxlength="4" placeholder="Any 4 digits (demo)" /></div></div>
    <div id="pay-card-box" hidden><div class="demo-banner">Demo only. Card details are checked for format and never stored or logged.</div>
      <div class="form-field"><label for="card-name">NAME ON CARD</label><input id="card-name" maxlength="60" /></div><div class="form-field"><label for="card-number">CARD NUMBER</label><input id="card-number" inputmode="numeric" maxlength="23" placeholder="13 to 19 digits" /></div>
      <div class="form-row"><div class="form-field"><label for="card-expiry">EXPIRY (MM/YY)</label><input id="card-expiry" maxlength="5" placeholder="08/29" /></div><div class="form-field"><label for="card-cvv">CVV</label><input id="card-cvv" type="password" inputmode="numeric" maxlength="4" /></div></div></div>
    <button class="button button-green pay-submit" type="submit">Pay now</button></form>
    <aside class="surface pad"><div class="eyebrow">THIS CYCLE</div><h2 class="sub-h">${escapeHtml(m.fullName)}</h2>
      <div class="rule-row"><span>Contribution</span><strong>${m.status === "paid" ? "Paid ✓" : m.status === "overdue" ? `Overdue · ${lateDays(m)} days` : "Pending"}</strong></div>
      <div class="rule-row"><span>Penalty (KES ${money(state.chama.latePenalty)}/day)</span><strong>${penaltyOwed(m) ? `KES ${money(penaltyOwed(m))}` : "None"}</strong></div>
      <div class="rule-row"><span>Credit score</span><strong>${m.score}</strong></div></aside></div>`;
  const form = $("#pay-form"), item = $("#pay-item"), amount = $("#pay-amount");
  const syncItem = () => { const o = item.selectedOptions[0]; amount.value = o.dataset.amount; amount.readOnly = o.dataset.fixed === "1"; $("#pay-hint").textContent = amount.readOnly ? "Fixed amount" : `You can change this (up to KES ${money(o.dataset.max)})`; };
  const syncMethod = () => { const card = form.querySelector("input[name=pay-method]:checked").value === "Card"; $("#pay-card-box").hidden = !card; $("#pay-mpesa-box").hidden = card; };
  $("#pay-member").addEventListener("change", event => renderPay({ memberId: event.target.value }));
  item.addEventListener("change", syncItem);
  form.querySelectorAll("input[name=pay-method]").forEach(radio => radio.addEventListener("change", syncMethod));
  form.addEventListener("submit", event => { event.preventDefault(); submitPay(m, items); });
  syncItem(); syncMethod();
}

function submitPay(m, items) {
  const key = val("pay-item"), item = items.find(i => i.key === key), amount = whole(val("pay-amount")), method = document.querySelector("input[name=pay-method]:checked").value;
  if (!item || !amount) return toast("Enter a whole-number amount above zero.", true);
  if (item.fixed && amount !== item.amount) return toast(`${LABEL[key]} is fixed at KES ${money(item.amount)}.`, true);
  if (!item.fixed && amount > item.max) return toast(`The most you can pay here is KES ${money(item.max)}.`, true);
  let ref;
  if (method === "Card") {
    const errors = cardErrors(val("card-name"), val("card-number"), val("card-expiry"), val("card-cvv"));
    ["card-name", "card-number", "card-expiry", "card-cvv"].forEach(id => { document.getElementById(id).value = ""; });   // never keep card data
    if (errors.length) return toast(errors[0], true);
    ref = "CARD" + Math.random().toString(16).slice(2, 10).toUpperCase();
  } else {
    const pin = val("mpesa-pin"); $("#mpesa-pin").value = "";   // simulated phone prompt: any 4 digits approve it
    if (!/^\d{4}$/.test(pin)) return toast("Enter your 4-digit M-Pesa PIN to approve.", true);
    ref = "MP" + Math.random().toString(16).slice(2, 10).toUpperCase();
  }
  showReceipt(applyPayment(m, key, amount, method, ref), m);
}

// One payment: ledger entry, member state, score, activity feed and an SMS to everyone.
function applyPayment(m, key, amount, method, ref) {
  if (key === "contribution") {
    const late = m.status === "overdue";
    if (late) m.lateDays = lateDays(m);
    m.status = "paid"; m.time = `Today, ${new Date().toLocaleTimeString("en-KE", { hour: "numeric", minute: "2-digit" })}`; m.method = method; m.cycleAmount = amount;
    if (late) { addScore(m, -15, "Late contribution"); m.streak = 0; }
    else { addScore(m, 10, "On-time contribution"); m.streak = (m.streak || 0) + 1; if (m.streak % 3 === 0) addScore(m, 20, `${m.streak}-payment streak`); }
  } else if (key === "penalty") m.penaltyPaid = (m.penaltyPaid || 0) + amount;
  else if (key === "installment") {
    const loan = loanOf(m.id);
    loan.repaid += amount; loan.paid += 1;
    if (loan.repaid >= loan.total) loan.status = "repaid";
    addScore(m, 25, "Loan installment on schedule");
  }
  const tx = addTx(m.id, amount, LABEL[key], method, method === "Cash" ? state.treasurer.name : "Auto-matched", ref);
  state.activity.unshift({ icon: "✓", title: `${m.name} paid ${LABEL[key].toLowerCase()}`, detail: `KES ${money(amount)} · ${method} · Just now` });
  save(); render();
  sendSms("PAYMENT", everyone(), `${m.name} paid KES ${money(amount)}. Group total: KES ${money(currentTotal())} / goal KES ${money(groupGoal())}.`);
  return tx;
}

function showReceipt(tx, m) {
  $("#pay-content").innerHTML = `<div class="surface pad receipt"><div class="receipt-check">✓</div><h2>Payment received</h2><div class="receipt-amount">KES ${money(tx.amount)}</div><p class="modal-intro">${escapeHtml(m.fullName)} · ${escapeHtml(tx.kind)}</p>
    <div class="rule-row"><span>Receipt no.</span><strong>#${state.transactions.length - state.transactions.indexOf(tx)}</strong></div><div class="rule-row"><span>Date</span><strong>${escapeHtml(tx.time)} (EAT)</strong></div>
    <div class="rule-row"><span>Method</span><strong>${escapeHtml(tx.method)} · ${escapeHtml(tx.ref)}</strong></div><div class="rule-row"><span>Record fingerprint</span><strong class="hash">${escapeHtml((tx.hash || "").slice(0, 20))}…</strong></div>
    <p class="modal-note">Everyone in the chama was notified by SMS and the ledger is updated.</p>
    <div class="modal-actions no-print"><button class="button button-outline" id="receipt-ledger">View ledger</button><button class="button button-green" id="receipt-again">Make another payment</button></div></div>`;
  $("#receipt-ledger").addEventListener("click", () => showView("ledger"));
  $("#receipt-again").addEventListener("click", () => renderPay({ memberId: m.id }));
}

// ---------- loans ----------
const voteMath = r => { const eligible = state.members.length - 1, votes = Object.values(r.votes), yes = votes.filter(Boolean).length; return { eligible, needed: Math.ceil(state.chama.approval * eligible / 100), yes, no: votes.length - yes }; };
const loanTerms = (principal, count) => { const total = Math.round(principal * (100 + Number(state.chama.interest)) / 100); return { total, per: Math.ceil(total / count) }; };

function renderLoans() {
  const open = state.loanRequests.filter(r => r.status === "pending" || r.status === "approved"), loans = state.loans.filter(l => l.status !== "defaulted");
  $("#loan-rules").innerHTML = `<div class="rule-row"><span>Maximum loan</span><strong>KES ${money(state.chama.maxLoan)}</strong></div><div class="rule-row"><span>Group approval</span><strong>${state.chama.approval}% of members</strong></div><div class="rule-row"><span>Interest</span><strong>${state.chama.interest}% flat</strong></div>`;
  $("#loan-column").innerHTML = open.map(requestCard).join("") + loans.map(loanCard).join("") || `<div class="surface pad"><p class="modal-intro">No loans yet. When a member requests one, the whole group gets a say.</p></div>`;
  document.querySelectorAll("[data-vote]").forEach(b => b.addEventListener("click", () => vote(...b.dataset.vote.split(":"))));
  document.querySelectorAll("[data-payout]").forEach(f => f.addEventListener("submit", event => { event.preventDefault(); payout(f.dataset.payout, f.querySelector("input")); }));
  document.querySelectorAll("[data-pay-loan]").forEach(b => b.addEventListener("click", () => showView("pay", { memberId: b.dataset.payLoan, item: "installment" })));
}

function requestCard(r) {
  const v = voteMath(r), waiting = state.members.filter(x => x.id !== r.memberId && !(x.id in r.votes));
  const action = r.status === "approved"
    ? `<form class="pot-form" data-payout="${r.id}" autocomplete="off"><input type="password" inputmode="numeric" maxlength="4" placeholder="Treasurer PIN" required /><button class="button button-green">Pay out (mock M-Pesa)</button></form>`
    : `<div class="inline-actions"><select data-voter="${r.id}">${memberOptions(waiting[0]?.id, x => waiting.includes(x))}</select><button class="button button-green" data-vote="${r.id}:yes">Approve</button><button class="button button-outline" data-vote="${r.id}:no">Reject</button></div>`;
  return `<div class="surface pad loan-card"><div class="loan-title-row"><div><h2>${escapeHtml(r.reason)}</h2><p>${escapeHtml(nameOf(r.memberId))} · KES ${money(r.amount)} over ${r.count} month${r.count === 1 ? "" : "s"}</p></div><span class="${r.status === "approved" ? "approved-pill" : "pending-pill"}">${r.status === "approved" ? "APPROVED" : "VOTING"}</span></div>
    <p class="modal-note">Repay KES ${money(r.terms.total)} in ${r.count} × KES ${money(r.terms.per)}. Votes: ${v.yes} approve · ${v.no} reject · need ${v.needed} of ${v.eligible}.</p>${action}</div>`;
}

function loanCard(l) {
  const rows = Array.from({ length: l.count }, (_, i) => `<div><span class="${i < l.paid ? "installment-check" : "installment-next"}">${i < l.paid ? "✓" : i + 1}</span><span>Installment ${i + 1}</span><strong>KES ${money(l.per)} · ${i < l.paid ? "Paid" : "Upcoming"}</strong></div>`).join("");
  return `<div class="surface pad loan-card"><div class="loan-title-row"><div><h2>${escapeHtml(l.reason)}</h2><p>${escapeHtml(nameOf(l.memberId))} · KES ${money(l.principal)} · repaid KES ${money(l.repaid)} of ${money(l.total)}</p></div><span class="approved-pill">${l.status === "repaid" ? "REPAID" : "ACTIVE"}</span></div>
    <div class="progress-track"><span style="width:${Math.round(l.repaid / l.total * 100)}%"></span></div><div class="installments">${rows}</div>
    ${l.status === "active" ? `<button class="button button-outline" data-pay-loan="${l.memberId}">Pay installment</button>` : ""}</div>`;
}

function vote(id, answer) {
  const r = state.loanRequests.find(x => x.id === id), voter = document.querySelector(`[data-voter="${id}"]`).value;
  if (!voter || voter in r.votes) return toast("That member has already voted.", true);
  r.votes[voter] = answer === "yes";
  const v = voteMath(r);
  if (v.yes >= v.needed) { r.status = "approved"; sendSms("LOAN", everyone(), `${nameOf(r.memberId)}’s loan of KES ${money(r.amount)} was approved.`); }
  else if (v.no > v.eligible - v.needed) { r.status = "rejected"; sendSms("LOAN", everyone(), `${nameOf(r.memberId)}’s loan request was not approved.`); }
  save(); render(); renderLoans();
}

function payout(id, input) {
  const r = state.loanRequests.find(x => x.id === id), pin = input.value; input.value = "";
  if (!pinOk(pin)) return;
  const pool = poolBalance();
  if (r.amount > pool) return toast("The pool can’t cover this payout right now.", true);
  addTx(r.memberId, -r.amount, "Loan payout", "M-Pesa", state.treasurer.name, "MP" + Math.random().toString(16).slice(2, 10).toUpperCase());
  state.loans.push({ id: `L${Date.now()}`, memberId: r.memberId, principal: r.amount, total: r.terms.total, per: r.terms.per, count: r.count, paid: 0, repaid: 0, status: "active", reason: r.reason });
  r.status = "paid-out";
  state.activity.unshift({ icon: "↗", title: `Loan paid out to ${nameOf(r.memberId)}`, detail: `KES ${money(r.amount)} · M-Pesa · Just now` });
  save(); render();
  sendSms("LOAN", everyone(), `KES ${money(r.amount)} was paid out to ${nameOf(r.memberId)}. Group total: KES ${money(currentTotal())} / goal KES ${money(groupGoal())}.`);
  // Fraud rule: a large payout right after contribution day sends a quiet SMS to the signatories.
  const day = new Date().getDate(), due = Number(state.chama.date) || 1;
  if (pool > 0 && r.amount >= 0.3 * pool && day >= due && day - due <= 2) sendSms("ANOMALY ALERT", "Signatories · Achieng & Grace", `ChamaVault notice: a payout of KES ${money(r.amount)} was made ${day - due} day(s) after contribution day. Please review the ledger.`);
  toast("Payout recorded in the ledger."); renderLoans();
}

function openLoanRequest() {
  const c = state.chama;
  openModal(`<h2>Request a chama loan</h2><p class="modal-intro">Other members vote; ${c.approval}% must approve. Maximum KES ${money(c.maxLoan)}, ${c.interest}% flat interest.</p>
    <form id="loan-form" autocomplete="off"><div class="form-field"><label for="loan-as">REQUESTING AS (DEMO)</label><select id="loan-as">${memberOptions(state.members[0].id)}</select></div>
    <div class="form-row"><div class="form-field"><label for="loan-amount">AMOUNT (KES)</label><input id="loan-amount" inputmode="numeric" value="${Math.min(5000, c.maxLoan)}" required /></div><div class="form-field"><label for="loan-months">MONTHS</label><select id="loan-months">${[1, 2, 3, 4, 5, 6].map(n => `<option ${n === 3 ? "selected" : ""}>${n}</option>`).join("")}</select></div></div>
    <div class="form-field"><label for="loan-reason">WHAT DO YOU NEED IT FOR?</label><textarea id="loan-reason" maxlength="120" required></textarea></div>
    <div class="modal-actions"><button class="button button-green">Share with the group</button></div></form>`);
  $("#loan-form").addEventListener("submit", event => {
    event.preventDefault();
    const memberId = val("loan-as"), amount = whole(val("loan-amount")), count = Number(val("loan-months")), reason = val("loan-reason").trim();
    if (state.loans.some(l => l.memberId === memberId && l.status === "active") || state.loanRequests.some(r => r.memberId === memberId && ["pending", "approved"].includes(r.status))) return toast("That member already has an open loan or request.", true);
    if (!amount || amount < 500) return toast("The minimum loan is KES 500.", true);
    if (amount > c.maxLoan) return toast(`Loan requests are capped at KES ${money(c.maxLoan)}.`, true);
    if (amount > poolBalance()) return toast("The group pool can’t cover that amount right now.", true);
    if (reason.length < 3) return toast("Please say what the loan is for.", true);
    state.loanRequests.push({ id: `r${Date.now()}`, memberId, amount, count, reason, votes: {}, status: "pending", terms: loanTerms(amount, count) });
    save(); closeModal(); render();
    sendSms("LOAN VOTE", everyone(), `${nameOf(memberId)} requested KES ${money(amount)}. Open ChamaVault to vote; ${c.approval}% approval is required.`);
    toast("Loan request shared with the group."); renderLoans();
  });
}

// ---------- statement: score explanation, printable, with a verification code ----------
const SCORE_RULES = [["+15", "Pay your contribution early"], ["+10", "Pay on the due date"], ["+25", "Pay a loan installment on schedule"], ["+20", "Every 3 on-time contributions in a row"], ["-15", "Pay late"], ["-40", "Miss a month entirely"], ["-100", "Default on a loan"]];
const statementCode = m => { const mine = state.transactions.filter(tx => tx.memberId === m.id), raw = sha256(`${m.id}|${mine.length}|${mine.map(tx => tx.hash).join("")}`).slice(0, 12).toUpperCase(); return `CV-${raw.slice(0, 4)}-${raw.slice(4, 8)}-${raw.slice(8)}`; };

function openStatement(memberId) {
  const m = memberById(memberId || state.members[0].id), mine = state.transactions.filter(tx => tx.memberId === m.id), events = state.scoreLog.filter(e => e.memberId === m.id).slice(0, 5);
  openModal(`<div class="statement"><h2>Member statement</h2><div class="no-print form-field"><select id="statement-member">${memberOptions(m.id)}</select></div>
    <p class="modal-intro"><strong>${escapeHtml(m.fullName)}</strong> · ${escapeHtml(m.phone)}<br>${escapeHtml(chamaName())} · credit score <strong>${m.score}</strong> (${scoreLabel(m.score)})</p>
    <table class="statement-table"><thead><tr><th>DATE</th><th>TYPE</th><th>METHOD</th><th>KES</th></tr></thead><tbody>${mine.map(tx => `<tr><td>${escapeHtml(tx.time)}</td><td>${escapeHtml(tx.kind || (tx.correction ? "Correction" : "Monthly contribution"))}</td><td>${escapeHtml(tx.method)}</td><td>${money(tx.amount)}</td></tr>`).join("") || `<tr><td colspan="4">No records yet</td></tr>`}</tbody></table>
    <h3 class="sub-h">How your score works</h3>${SCORE_RULES.map(([pts, text]) => `<div class="rule-row"><span>${text}</span><strong>${pts}</strong></div>`).join("")}
    ${events.length ? `<h3 class="sub-h">Recent changes</h3>${events.map(e => `<div class="rule-row"><span>${escapeHtml(e.reason)}</span><strong>${e.delta > 0 ? "+" : ""}${e.delta}</strong></div>`).join("")}` : ""}
    <div class="verify-box"><small>VERIFICATION CODE</small><strong>${statementCode(m)}</strong><span>Ledger check: ${verifyChain(state.transactions).ok ? "intact ✓" : "BROKEN ⚠"}</span></div>
    <div class="modal-actions no-print"><button class="button button-green" id="statement-print">Print / save as PDF</button></div></div>`);
  $("#statement-member").addEventListener("change", event => openStatement(event.target.value));
  $("#statement-print").addEventListener("click", () => window.print());
}

// ---------- wiring ----------
const baseRender = render, baseShowView = showView;
render = function () {
  ensureExtras();
  baseRender();
  if (sealChain(state.transactions)) save();
  const chain = verifyChain(state.transactions), badge = $(".verified");
  badge.innerHTML = chain.ok ? `<span>◈</span> VERIFIED · ${chain.count} RECORDS · CLICK TO RE-CHECK` : `<span>⚠</span> BROKEN AT RECORD #${chain.number}`;
  badge.classList.toggle("broken", !chain.ok);
};
showView = function (name, preset) {
  baseShowView(name);
  const title = { pay: "Make a payment", loans: "Loans & votes" }[name];
  if (title) $("#page-title").textContent = title;
  if (name === "pay") renderPay(preset);
  if (name === "loans") renderLoans();
};
$(".verified").addEventListener("click", () => { const c = verifyChain(state.transactions); toast(c.ok ? `Ledger verified: all ${c.count} records match their hashes.` : `Record #${c.number} is broken: ${c.reason}.`, !c.ok); });
const payButton = $("[data-open-pay]"); payButton.replaceWith(payButton.cloneNode(true));   // replace the cash popup with the payment page
$("[data-open-pay]").addEventListener("click", () => showView("pay"));
$("#loan-request").addEventListener("click", openLoanRequest);
$("#statement-open").addEventListener("click", () => openStatement());
render();
