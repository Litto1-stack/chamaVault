const STORAGE_KEY = "chamavault-umoja-demo-v3";
const memberSeed = [
  { id: "w", name: "Wanjiku M.", fullName: "Wanjiku Mwangi", phone: "0712 345 678", initials: "WM", color: "rose", score: 640, status: "paid", time: "Today, 9:14 AM", method: "M-Pesa", streak: 2 },
  { id: "a", name: "Achieng O.", fullName: "Achieng Otieno", phone: "0722 130 450", initials: "AO", color: "sage", score: 720, status: "paid", time: "Today, 8:42 AM", method: "M-Pesa", streak: 4 },
  { id: "g", name: "Grace N.", fullName: "Grace Njeri", phone: "0703 550 211", initials: "GN", color: "gold", score: 580, status: "paid", time: "Yesterday, 6:18 PM", method: "Cash", streak: 1 },
  { id: "f", name: "Faith W.", fullName: "Faith Wambui", phone: "0718 204 980", initials: "FW", color: "blue", score: 690, status: "paid", time: "Oct 1, 10:06 AM", method: "M-Pesa", streak: 3 },
  { id: "m", name: "Mercy K.", fullName: "Mercy Kamene", phone: "0790 442 167", initials: "MK", color: "peach", score: 510, status: "pending", time: "", method: "", streak: 0 },
  { id: "n", name: "Naliaka S.", fullName: "Naliaka Simiyu", phone: "0708 901 235", initials: "NS", color: "lilac", score: 465, status: "overdue", time: "", method: "", streak: 0 }
];
const transactionSeed = (() => {
  const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const stamp = (month, day, hour, minute) => `${MONTHS[month]} ${day}, ${hour % 12 || 12}:${String(minute).padStart(2, "0")} ${hour < 12 ? "AM" : "PM"}`;
  const ids = ["w", "a", "g", "f", "m", "n"], lateDays = { w: 0, a: 0, g: 1, f: 0, m: 5, n: 8 };   // days after the 1st that each member usually pays
  const october = [
    { id: "t1", memberId: "w", amount: 1000, time: "Oct 5, 9:14 AM", method: "M-Pesa", by: "Auto-matched", balance: 0, status: "normal", cycle: true },
    { id: "t2", memberId: "a", amount: 1000, time: "Oct 5, 8:42 AM", method: "M-Pesa", by: "Auto-matched", balance: 0, status: "normal", cycle: true },
    { id: "t3", memberId: "g", amount: 1000, time: "Oct 4, 6:18 PM", method: "Cash", by: "Kamau N.", balance: 0, status: "normal", cycle: true },
    { id: "t7", memberId: "w", amount: 3000, time: "Oct 3, 2:10 PM", method: "M-Pesa", by: "Auto-matched", balance: 0, status: "normal", kind: "Loan installment" },
    { id: "t4", memberId: "f", amount: 1000, time: "Oct 1, 10:06 AM", method: "M-Pesa", by: "Auto-matched", balance: 0, status: "normal", cycle: true }
  ];
  const history = [];
  [5, 6, 7, 8].forEach(month => ids.forEach((memberId, i) => {
    const day = 1 + lateDays[memberId], minute = 10 + i * 7, cash = (month + i) % 3 === 0;
    history.push({ ts: new Date(2026, month, day, 9, minute), id: `h${month}${memberId}`, memberId, amount: 1000, time: stamp(month, day, 9, minute), method: cash ? "Cash" : "M-Pesa", by: cash ? "Kamau N." : "Auto-matched", balance: 0, status: "normal" });
  }));
  history.push({ ts: new Date(2026, 7, 20, 11, 0), id: "h-loan", memberId: "w", amount: -8000, time: stamp(7, 20, 11, 0), method: "M-Pesa", by: "Kamau N.", balance: 0, status: "normal", kind: "Loan payout" });
  history.sort((a, b) => b.ts - a.ts);
  return [...october, ...history.map(({ ts, ...tx }) => tx)];
})();
const initialState = {
  chama: { name: "Umoja Sisters", contribution: 1000, frequency: "monthly", date: "1", goal: 8000, latePenalty: 100, inviteCode: "482916" },
  treasurer: { name: "Kamau N.", phone: "0712 000 111", pin: "1234", score: 640, streak: 2 },
  members: memberSeed,
  transactions: transactionSeed,
  messages: [
    { type: "WELCOME", to: "Wanjiku M.", text: "Welcome to Umoja Sisters! Contributions: KES 1,000 due every 1st. Text HELP anytime for Vaulti, your financial coach.", time: "Today, 8:00 AM" },
    { type: "PAYMENT", to: "All 6 members", text: "Achieng paid KES 1,000. Group total: KES 4,000 / goal KES 8,000.", time: "Today, 8:43 AM" },
    { type: "REMINDER", to: "Naliaka S.", text: "A gentle reminder from Umoja Sisters: your KES 1,000 contribution is still outstanding. Please reach out if you need a hand.", time: "Yesterday, 6:00 PM" }
  ],
  activity: [
    { icon: "✓", title: "Wanjiku and Achieng contributed", detail: "KES 2,000 · M-Pesa · Today" },
    { icon: "↗", title: "Wanjiku’s loan installment received", detail: "KES 3,000 · Oct 3" },
    { icon: "◈", title: "Monthly contribution cycle started", detail: "October 1 · 6 members" }
  ]
};
let state;
try {
  state = JSON.parse(localStorage.getItem(STORAGE_KEY)) || structuredClone(initialState);
} catch {
  console.warn("Saved demo data could not be read; starting with the seeded demo.");
  state = structuredClone(initialState);
}
state.chama ||= structuredClone(initialState.chama);
state.treasurer ||= structuredClone(initialState.treasurer);
state.treasurer.score ??= 640;
state.treasurer.streak ??= 2;
let PIN = state.treasurer.pin || "1234";
const money = amount => new Intl.NumberFormat("en-KE").format(amount);
const chamaName = () => state.chama?.name || "Umoja Sisters";
const contribution = () => Number(state.chama?.contribution || 1000);
const groupGoal = () => Number(state.chama?.goal || 8000);
const memberById = id => state.members.find(member => member.id === id);
const currentMember = () => state.members.find(member => member.id === state.treasurer.memberId);
const userScore = () => currentMember()?.score ?? state.treasurer.score;
const userStreak = () => currentMember()?.streak ?? state.treasurer.streak;
const escapeHtml = value => String(value).replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
const scoreLabel = score => score >= 700 ? "Very good" : score >= 600 ? "Good" : score >= 500 ? "Fair" : "Building";
const currentTotal = () => state.members.filter(member => member.status === "paid").reduce((sum, member) => sum + (member.cycleAmount || contribution()), 0);
const save = () => {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); }
  catch (error) { console.error("Could not save the demo ledger.", error); toast("Could not save changes on this device.", true); }
};

function toast(message, error = false) {
  const item = document.createElement("div");
  item.className = `toast${error ? " error" : ""}`;
  item.textContent = message;
  document.querySelector("#toast-region").append(item);
  setTimeout(() => item.remove(), 3600);
}

function showView(name) {
  document.querySelectorAll(".view-panel").forEach(view => view.classList.toggle("active-view", view.id === `view-${name}`));
  document.querySelectorAll(".nav-item").forEach(button => button.classList.toggle("active", button.dataset.view === name));
  const label = { dashboard: "Overview", ledger: "Full ledger", members: "Members", vaulti: "Ask Vaulti" }[name];
  document.querySelector("#page-title").textContent = label || "Overview";
  document.querySelector("#sidebar").classList.remove("mobile-open");
  window.scrollTo({ top: 0, behavior: "smooth" });
}
document.querySelectorAll(".nav-item").forEach(button => button.addEventListener("click", () => showView(button.dataset.view)));
document.querySelectorAll("[data-goto]").forEach(button => button.addEventListener("click", () => showView(button.dataset.goto)));
document.querySelector("#mobile-menu").addEventListener("click", () => document.querySelector("#sidebar").classList.toggle("mobile-open"));

function render() {
  const total = currentTotal();
  const paid = state.members.filter(member => member.status === "paid").length;
  const pending = state.members.filter(member => member.status === "pending").length;
  const overdue = state.members.filter(member => member.status === "overdue").length;
  document.querySelector("#group-total").textContent = money(total);
  document.querySelector("#ledger-balance").textContent = `KES ${money(total)}`;
  document.querySelector(".group-label strong").textContent = chamaName();
  document.querySelector(".welcome-sub strong").textContent = chamaName();
  document.querySelector("#profile-name").textContent = state.treasurer.name;
  document.querySelector("#welcome-name").textContent = state.treasurer.name.split(/\s+/)[0];
  document.querySelector("#group-avatar").textContent = chamaName().split(/\s+/).slice(0, 2).map(part => part[0].toUpperCase()).join("");
  document.querySelector(".group-label small").textContent = `${state.members.length} members · Active`;
  document.querySelector("#contribution-denom").textContent = state.members.length;
  document.querySelector("#directory-cycle").textContent = `${state.chama.frequency.toUpperCase()} CONTRIBUTION · KES ${money(contribution())}`;
  document.querySelector("#outstanding-caption").textContent = `KES ${money((pending + overdue) * contribution())} outstanding`;
  const score = userScore();
  document.querySelector("#credit-score").textContent = score;
  document.querySelector("#score-level").textContent = scoreLabel(score).toUpperCase();
  document.querySelector("#score-meter").style.width = `${Math.min(100, Math.round(score / 850 * 100))}%`;
  document.querySelector("#score-explanation").textContent = `Your score is ${score} (${scoreLabel(score)}). ${userStreak() ? `You’re on a ${userStreak()}-month on-time streak.` : "Pay on time to start building a positive history."}`;
  document.querySelector("#coach-welcome").textContent = `Habari ${state.treasurer.name.split(/\s+/)[0]}! I’m here for you. Your score is ${score} (${scoreLabel(score)})${userStreak() ? `, with a ${userStreak()}-month on-time streak` : ""}. What’s on your mind? Ask about saving, chama rules, loans, or anything money-related.`;
  document.querySelector("#vaulti-personal-data").textContent = `${state.members.length} members · KES ${money(contribution())} ${state.chama.frequency} · Your score: ${score} · ${userStreak() ? `You’re on a ${userStreak()}-month on-time streak.` : "Start your on-time streak with this cycle."}`;
  document.title = `ChamaVault — ${chamaName()}`;
  const progress = groupGoal() > 0 ? Math.min(100, Math.round(total / groupGoal() * 100)) : 0;
  document.querySelector("#goal-label").textContent = groupGoal() > 0 ? `KES ${money(total)} of KES ${money(groupGoal())} goal` : `KES ${money(total)} saved · no group goal set`;
  document.querySelector("#goal-percent").textContent = groupGoal() > 0 ? `${progress}%` : "—";
  document.querySelector("#goal-progress").style.width = `${progress}%`;
  document.querySelector("#paid-count").textContent = paid;
  document.querySelector("#member-count").textContent = state.members.length;
  document.querySelector("#pending-count").textContent = pending;
  document.querySelector("#overdue-count").textContent = overdue;
  document.querySelector("#on-time-count").textContent = state.members.filter(member => member.status === "paid" && member.method !== "Cash").length;
  document.querySelector("#sms-badge").textContent = state.messages.length;
  document.querySelector("#ledger-count").textContent = state.transactions.length;
  document.querySelector("#record-count").textContent = `${state.transactions.length} entries`;
  document.querySelector("#dashboard-members").innerHTML = state.members.map(member => {
    const status = member.status === "paid" ? `<span class="payment-status"><span class="status-mark">✓</span> Paid</span>` : member.status === "overdue" ? `<span class="payment-status overdue"><span class="status-mark">!</span> 4 days late</span>` : `<span class="payment-status pending"><span class="status-mark">◷</span> Pending</span>`;
    return `<div class="member-row"><div class="member-identity"><span class="avatar ${member.color}">${escapeHtml(member.initials)}</span><span class="member-name"><strong>${escapeHtml(member.name)}</strong><small>${escapeHtml(member.phone)}</small></span></div>${status}<div class="member-amount">${member.status === "paid" ? `KES ${money(member.cycleAmount || contribution())}<small>${escapeHtml(member.method)} · ${escapeHtml(member.time)}</small>` : `KES ${money(contribution())}<small>Due ${escapeHtml(state.chama.date)}${state.chama.frequency === "monthly" ? " of month" : ""}</small>`}</div></div>`;
  }).join("");
  document.querySelector("#recent-activity").innerHTML = state.activity.slice(0, 4).map(item => `<div class="activity-item"><span class="activity-icon ${item.icon === "!" ? "warn" : ""}">${escapeHtml(item.icon)}</span><span class="activity-copy"><strong>${escapeHtml(item.title)}</strong><small>${escapeHtml(item.detail)}</small></span></div>`).join("");
  document.querySelector("#ledger-rows").innerHTML = state.transactions.map(tx => {
    const member = memberById(tx.memberId);
    const correction = tx.correction;
    const amountText = correction?.referenceId ? `KES ${money(correction.oldAmount)} → ${money(correction.newAmount)}<span class="corrected-note">${escapeHtml(correction.reason)}</span>` : correction ? `<span style="text-decoration:line-through;color:#9aa098">KES ${money(tx.amount)}</span><span class="corrected-note">KES ${money(correction.newAmount)} · ${escapeHtml(correction.reason)}</span>` : `KES ${money(tx.amount)}`;
    return `<tr><td><div class="table-member"><span class="avatar ${member?.color || "sage"}">${escapeHtml(member?.initials || "??")}</span><div><strong>${escapeHtml(member?.name || "Member")}</strong><small>${correction ? "Correction record · Original retained" : escapeHtml(tx.kind || "Monthly contribution")}</small></div></div></td><td>${escapeHtml(tx.time)}</td><td><span class="method-pill">${escapeHtml(tx.method)}</span></td><td>${escapeHtml(tx.by)}</td><td class="amount-cell">${amountText}</td><td><span class="status-pill ${correction || tx.status === "corrected" ? "corrected" : ""}">${correction || tx.status === "corrected" ? "CORRECTED" : "RECORDED"}</span></td><td>${tx.status === "normal" && !correction ? `<button class="row-action correct-record" data-id="${escapeHtml(tx.id)}" aria-label="Correct record">···</button>` : ""}</td></tr>`;
  }).join("");
  document.querySelector("#member-directory").innerHTML = state.members.map(member => `<div class="directory-row"><div class="member-identity"><span class="avatar ${member.color}">${escapeHtml(member.initials)}</span><span class="member-name"><strong>${escapeHtml(member.fullName)}</strong><small>${escapeHtml(member.phone)} · Member</small></span></div><div class="directory-cell"><small>THIS CYCLE</small><strong>${member.status === "paid" ? `KES ${money(member.cycleAmount || contribution())} · Paid` : member.status === "overdue" ? "Overdue · 4 days" : `Pending · due ${escapeHtml(state.chama.date)}`}</strong></div><div class="directory-cell"><small>CREDIT SCORE</small><span class="credit-chip ${member.score < 500 ? "low" : ""}">✳ ${member.score} · ${scoreLabel(member.score)}</span></div><button class="text-button member-remind" data-id="${escapeHtml(member.id)}">${member.status !== "paid" ? "Send reminder →" : "View history →"}</button></div>`).join("");
  document.querySelector("#outbox-list").innerHTML = state.messages.slice().reverse().map(message => `<article class="sms-card"><div class="sms-card-top"><strong><span class="sms-type">${escapeHtml(message.type)}</span>${escapeHtml(message.to)}</strong><small>${escapeHtml(message.time)}</small></div><div class="sms-message">${escapeHtml(message.text)}</div><div class="sms-to">✓ Delivered · SMS simulator</div></article>`).join("");
  document.querySelectorAll(".correct-record").forEach(button => button.addEventListener("click", () => openCorrection(button.dataset.id)));
  document.querySelectorAll(".member-remind").forEach(button => button.addEventListener("click", () => {
    const member = memberById(button.dataset.id);
    if (member.status !== "paid") sendReminder(member);
    else toast(`${member.name} is up to date this cycle.`);
  }));
}

const outbox = document.querySelector("#outbox");
document.querySelector("#open-outbox").addEventListener("click", () => outbox.classList.add("open"));
document.querySelector("#close-outbox").addEventListener("click", () => outbox.classList.remove("open"));
function sendSms(type, to, text) {
  state.messages.push({ type, to, text, time: new Date().toLocaleTimeString("en-KE", { hour: "numeric", minute: "2-digit" }) });
  save();
  render();
}
document.querySelector("#trigger-reminder").addEventListener("click", () => {
  state.members.forEach(member => sendSms("DAY-BEFORE", member.name, `Reminder: Your KES ${money(contribution())} contribution to ${chamaName()} is due TOMORROW. Pay via M-Pesa Till 123456.`));
  toast(`Day-before reminder sent to all ${state.members.length} members.`);
  outbox.classList.add("open");
});
document.querySelector("#remind-overdue").addEventListener("click", () => {
  const overdue = state.members.filter(member => member.status === "overdue");
  if (!overdue.length) return toast("No overdue members to remind.");
  overdue.forEach(sendReminder);
});
function sendReminder(member) {
  sendSms("REMINDER", member.name, `A gentle reminder from ${chamaName()}: your KES ${money(contribution())} contribution is outstanding. Please reach out if you need a hand.`);
  toast(`A gentle reminder was sent to ${member.name}.`);
  outbox.classList.add("open");
}

function openModal(content) {
  document.querySelector("#modal-content").innerHTML = content;
  document.querySelector("#modal-backdrop").hidden = false;
  document.querySelector("#modal-close").focus();
}
function closeModal() { document.querySelector("#modal-backdrop").hidden = true; }
document.querySelector("#modal-close").addEventListener("click", closeModal);
document.querySelector("#modal-backdrop").addEventListener("click", event => { if (event.target.id === "modal-backdrop") closeModal(); });
document.addEventListener("keydown", event => { if (event.key === "Escape") { closeModal(); outbox.classList.remove("open"); } });

function openPayment() {
  const unpaid = state.members.filter(member => member.status !== "paid");
  if (!unpaid.length) return toast("Everyone has contributed this cycle.");
  openModal(`<h2>Record a cash payment</h2><p class="modal-intro">The member and the whole group will see this entry immediately. The record can’t be deleted.</p><form id="payment-form"><div class="form-field"><label for="payment-member">MEMBER</label><select id="payment-member" required>${unpaid.map(member => `<option value="${member.id}">${escapeHtml(member.fullName)} · ${member.status === "overdue" ? "4 days overdue" : "pending"}</option>`).join("")}</select></div><div class="form-row"><div class="form-field"><label for="payment-amount">AMOUNT (KES)</label><input id="payment-amount" type="number" min="1" value="${contribution()}" required /></div><div class="form-field"><label for="payment-pin">TREASURER PIN</label><input id="payment-pin" type="password" inputmode="numeric" maxlength="4" placeholder="4 digits" required /></div></div><div class="modal-note">Recorded by ${escapeHtml(state.treasurer.name)} · Treasurer · Entry is permanent</div><div class="modal-actions"><button type="button" class="button button-outline cancel-modal">Cancel</button><button class="button button-green" type="submit">Confirm payment</button></div></form>`);
  document.querySelector(".cancel-modal").addEventListener("click", closeModal);
  document.querySelector("#payment-form").addEventListener("submit", event => {
    event.preventDefault();
    const member = memberById(document.querySelector("#payment-member").value);
    const amount = Number(document.querySelector("#payment-amount").value);
    if (document.querySelector("#payment-pin").value !== state.treasurer.pin) return toast("That PIN isn’t right. Check the treasurer PIN and try again.", true);
    if (!Number.isFinite(amount) || amount <= 0) return toast("Enter a valid payment amount.", true);
    const wasOverdue = member.status === "overdue";
    member.status = "paid"; member.time = `Today, ${new Date().toLocaleTimeString("en-KE", { hour: "numeric", minute: "2-digit" })}`; member.method = "Cash"; member.cycleAmount = amount;
    member.score += wasOverdue ? -15 : 10;
    const now = new Date();
    const tx = { id: `t${Date.now()}`, memberId: member.id, amount, time: now.toLocaleString("en-KE", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }), method: "Cash", by: state.treasurer.name, balance: currentTotal(), status: "normal", cycle: true };
    state.transactions.unshift(tx);
    state.activity.unshift({ icon: "✓", title: `${member.name} contributed KES ${money(amount)}`, detail: `Cash · Recorded by ${state.treasurer.name} · Just now` });
    save(); closeModal(); render();
    sendSms("PAYMENT", `All ${state.members.length} members`, `${member.name} paid KES ${money(amount)}. Group total: KES ${money(currentTotal())} / goal KES ${money(groupGoal())}.`);
    toast("Payment recorded. All members have been notified.");
    outbox.classList.add("open");
  });
}
document.querySelector("#record-payment").addEventListener("click", openPayment);
document.querySelector("#ledger-record").addEventListener("click", openPayment);
document.querySelectorAll("[data-open-pay]").forEach(button => button.addEventListener("click", openPayment));

document.querySelector("#trigger-mpesa").addEventListener("click", () => {
  const unpaid = state.members.filter(member => member.status !== "paid");
  if (!unpaid.length) return toast("All members have paid for this cycle.");
  openModal(`<h2>Simulate M-Pesa payment</h2><p class="modal-intro">Mock Daraja webhook — no real money moves. We’ll match the payer’s phone number to a chama member.</p><form id="mpesa-form"><div class="form-field"><label for="mpesa-phone">PAYER PHONE NUMBER</label><input id="mpesa-phone" type="tel" value="${escapeHtml(unpaid[0].phone)}" required /></div><div class="form-row"><div class="form-field"><label for="mpesa-amount">AMOUNT (KES)</label><input id="mpesa-amount" type="number" min="1" value="${contribution()}" required /></div><div class="form-field"><label for="mpesa-ref">TRANSACTION REF</label><input id="mpesa-ref" value="QK${Math.floor(1000 + Math.random() * 9000)}" required /></div></div><div class="modal-actions"><button type="button" class="button button-outline cancel-modal">Cancel</button><button class="button button-green">Simulate payment</button></div></form>`);
  document.querySelector(".cancel-modal").addEventListener("click", closeModal);
  document.querySelector("#mpesa-form").addEventListener("submit", event => {
    event.preventDefault();
    const phone = document.querySelector("#mpesa-phone").value.replace(/\D/g, "").slice(-9);
    const member = state.members.find(entry => entry.phone.replace(/\D/g, "").slice(-9) === phone);
    const amount = Number(document.querySelector("#mpesa-amount").value);
    if (!member) return toast("No chama member matches that phone number.", true);
    if (member.status === "paid") return toast(`${member.name} has already contributed.`, true);
    if (!Number.isFinite(amount) || amount <= 0) return toast("Enter a valid payment amount.", true);
    member.status = "paid"; member.time = `Today, ${new Date().toLocaleTimeString("en-KE", { hour: "numeric", minute: "2-digit" })}`; member.method = "M-Pesa"; member.cycleAmount = amount;
    member.score = Math.max(300, member.score - 5);
    state.transactions.unshift({ id: `t${Date.now()}`, memberId: member.id, amount, time: new Date().toLocaleString("en-KE", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }), method: "M-Pesa", by: "Auto-matched", balance: currentTotal(), status: "normal", cycle: true });
    state.activity.unshift({ icon: "✓", title: `${member.name} paid via M-Pesa`, detail: `KES ${money(amount)} · Auto-matched · Just now` });
    save(); closeModal(); render();
    sendSms("PAYMENT", `All ${state.members.length} members`, `${member.name} paid KES ${money(amount)}. Group total: KES ${money(currentTotal())} / goal KES ${money(groupGoal())}.`);
    toast(`M-Pesa payment matched to ${member.name}.`);
    outbox.classList.add("open");
  });
});

function openCorrection(id) {
  const tx = state.transactions.find(entry => entry.id === id);
  const member = memberById(tx.memberId);
  openModal(`<h2>Correct a ledger record</h2><p class="modal-intro">The original will stay visible, marked corrected. Your reason and this change will be sent to every member and the signatories.</p><div class="form-field"><label>ORIGINAL RECORD</label><div class="modal-note">${escapeHtml(member.name)} · KES ${money(tx.amount)} · ${escapeHtml(tx.time)}</div></div><form id="correction-form"><div class="form-row"><div class="form-field"><label for="corrected-amount">CORRECT AMOUNT (KES)</label><input id="corrected-amount" type="number" min="1" value="${tx.amount}" required /></div><div class="form-field"><label for="correction-pin">TREASURER PIN</label><input id="correction-pin" type="password" maxlength="4" inputmode="numeric" placeholder="4 digits" required /></div></div><div class="form-field"><label for="correction-reason">WHY DOES THIS NEED CORRECTING?</label><textarea id="correction-reason" required placeholder="Please explain clearly — e.g. typing error"></textarea></div><div class="modal-actions"><button type="button" class="button button-outline cancel-modal">Cancel</button><button class="button button-green">Publish correction</button></div></form>`);
  document.querySelector(".cancel-modal").addEventListener("click", closeModal);
  document.querySelector("#correction-form").addEventListener("submit", event => {
    event.preventDefault();
    const newAmount = Number(document.querySelector("#corrected-amount").value);
    const reason = document.querySelector("#correction-reason").value.trim();
    if (document.querySelector("#correction-pin").value !== state.treasurer.pin) return toast("That PIN isn’t right. Check the treasurer PIN and try again.", true);
    if (!reason) return toast("A written reason is required.", true);
    if (newAmount <= 0 || !Number.isFinite(newAmount)) return toast("Enter a valid amount.", true);
    const oldAmount = tx.amount;
    tx.status = "corrected";
    tx.correction = { newAmount, reason, time: new Date().toLocaleString("en-KE") };
    if (tx.cycle) member.cycleAmount = newAmount;
    state.transactions.unshift({ id: `c${Date.now()}`, memberId: tx.memberId, amount: newAmount - oldAmount, time: new Date().toLocaleString("en-KE", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }), method: "Correction", by: state.treasurer.name, balance: currentTotal(), status: "normal", correction: { oldAmount, newAmount, reason, referenceId: tx.id } });
    state.activity.unshift({ icon: "!", title: `${member.name}’s record corrected`, detail: `KES ${money(oldAmount)} → KES ${money(newAmount)} · ${reason}` });
    save(); closeModal(); render();
    sendSms("CORRECTION", "All members", `Record corrected in ${chamaName()}: ${member.name}'s payment changed from KES ${money(oldAmount)} to KES ${money(newAmount)}. Reason: ${reason}. — Treasurer ${state.treasurer.name}`);
    sendSms("ANOMALY ALERT", "Signatories · Achieng & Grace", `ChamaVault alert: a ledger correction was published in ${chamaName()}. ${member.name}: KES ${money(oldAmount)} → KES ${money(newAmount)}. Reason: ${reason}.`);
    toast("Correction published transparently. Members and signatories notified.");
    outbox.classList.add("open");
  });
}

function showInvite() {
  const code = state.chama.inviteCode;
  openModal(`<h2>Invite your members</h2><p class="modal-intro">Share this code so members can join your chama. They’ll get a welcome SMS and start with a credit score of 500.</p><div class="invite-code">${escapeHtml(code.slice(0, 3))} ${escapeHtml(code.slice(3))}</div><button class="button button-green code-copy" id="copy-invite">Copy invite code</button><div class="modal-actions"><button class="button button-outline" id="join-demo">Join with invite code</button><button class="button button-outline" id="create-chama">Create a chama</button></div>`);
  document.querySelector("#copy-invite").addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(code); toast("Invite code copied."); }
    catch { toast(`Invite code: ${code}`); }
  });
  document.querySelector("#join-demo").addEventListener("click", showJoinForm);
  document.querySelector("#create-chama").addEventListener("click", showCreateForm);
}
function showCreateForm() {
  openModal(`<h2>Create a chama</h2><p class="modal-intro">Set up your group and contribution rules. We’ll send a demo verification code by SMS.</p><form id="create-chama-form"><div class="form-field"><label for="create-owner">TREASURER FULL NAME</label><input id="create-owner" required placeholder="e.g. Kamau Njoroge" /></div><div class="form-row"><div class="form-field"><label for="create-phone">PHONE NUMBER</label><input id="create-phone" type="tel" required placeholder="07xx xxx xxx" /></div><div class="form-field"><label for="create-pin">4-DIGIT PIN</label><input id="create-pin" type="password" inputmode="numeric" maxlength="4" required /></div></div><div class="form-field"><label for="create-name">CHAMA NAME</label><input id="create-name" required placeholder="e.g. Umoja Sisters" /></div><div class="form-row"><div class="form-field"><label for="create-contribution">CONTRIBUTION (KES)</label><input id="create-contribution" type="number" min="1" value="1000" required /></div><div class="form-field"><label for="create-frequency">FREQUENCY</label><select id="create-frequency"><option value="weekly">Weekly</option><option value="monthly" selected>Monthly</option></select></div></div><div class="form-row"><div class="form-field"><label for="create-date">DUE DATE (DAY OF MONTH)</label><input id="create-date" type="number" min="1" max="28" value="1" required /></div><div class="form-field"><label for="create-goal">GROUP GOAL (KES)</label><input id="create-goal" type="number" min="0" value="50000" /></div></div><div class="form-row"><div class="form-field"><label for="create-penalty">LATE PENALTY / DAY (KES)</label><input id="create-penalty" type="number" min="0" value="100" /></div><div class="form-field"><label for="create-max-loan">MAX LOAN (KES)</label><input id="create-max-loan" type="number" min="0" value="15000" /></div></div><div class="form-row"><div class="form-field"><label for="create-interest">LOAN INTEREST (%)</label><input id="create-interest" type="number" min="0" value="10" /></div><div class="form-field"><label for="create-approval">APPROVAL THRESHOLD (%)</label><input id="create-approval" type="number" min="1" max="100" value="60" /></div></div><div class="modal-actions"><button class="button button-green">Send verification code</button></div></form>`);
  document.querySelector("#create-chama-form").addEventListener("submit", event => {
    event.preventDefault();
    const pin = document.querySelector("#create-pin").value;
    const goal = Number(document.querySelector("#create-goal").value || 0);
    if (!/^\d{4}$/.test(pin)) return toast("Choose a 4-digit PIN.", true);
    const config = {
      name: document.querySelector("#create-name").value.trim(),
      contribution: Number(document.querySelector("#create-contribution").value),
      frequency: document.querySelector("#create-frequency").value,
      date: document.querySelector("#create-date").value,
      goal,
      latePenalty: Number(document.querySelector("#create-penalty").value || 0),
      maxLoan: Number(document.querySelector("#create-max-loan").value || 0),
      interest: Number(document.querySelector("#create-interest").value || 0),
      approval: Number(document.querySelector("#create-approval").value || 60),
      inviteCode: String(Math.floor(100000 + Math.random() * 900000))
    };
    if (!config.name || !Number.isFinite(config.contribution) || config.contribution <= 0 || goal < 0 || config.approval < 1 || config.approval > 100) return toast("Check the chama details and try again.", true);
    const fullName = document.querySelector("#create-owner").value.trim();
    const phone = document.querySelector("#create-phone").value.trim();
    state.pendingChama = { config, treasurer: { name: fullName, phone, pin } };
    sendSms("OTP", phone, "Your ChamaVault verification code is 2468. Demo only — do not use this code for a real account.");
    openModal(`<h2>Verify your phone</h2><p class="modal-intro">We sent a one-time code to ${escapeHtml(phone)}. Check the SMS outbox — this demo code is <strong>2468</strong>.</p><form id="otp-form"><div class="form-field"><label for="otp-code">4-DIGIT VERIFICATION CODE</label><input id="otp-code" inputmode="numeric" maxlength="4" required autofocus /></div><div class="modal-actions"><button type="button" class="button button-outline" id="otp-back">Back</button><button class="button button-green">Verify & create chama</button></div></form>`);
    document.querySelector("#otp-back").addEventListener("click", showCreateForm);
    document.querySelector("#otp-form").addEventListener("submit", e => {
      e.preventDefault();
      if (document.querySelector("#otp-code").value !== "2468") return toast("That code doesn’t match. Check the SMS outbox.", true);
      const pending = state.pendingChama;
      if (!pending) return toast("Your setup has expired. Please start again.", true);
      const name = pending.treasurer.name.trim();
      const parts = name.split(/\s+/);
      state.chama = pending.config;
      const memberId = `m${Date.now()}`;
      const member = { id: memberId, name: `${parts[0]} ${parts.at(-1)[0]}.`, fullName: name, phone: pending.treasurer.phone, initials: parts.slice(0, 2).map(part => part[0].toUpperCase()).join(""), color: "sage", score: 500, status: "pending", time: "", method: "", streak: 0, role: "Treasurer" };
      state.treasurer = { ...pending.treasurer, memberId, score: 500, streak: 0 };
      PIN = state.treasurer.pin;
      state.members = [member];
      state.transactions = [];
      state.loans = [];
      state.loanRequests = [];
      state.scoreLog = [];
      state.activity = [{ icon: "◈", title: `${name} created ${state.chama.name}`, detail: `Contribution KES ${money(state.chama.contribution)} · ${state.chama.frequency} · Just now` }];
      state.pendingChama = null;
      save(); closeModal(); render(); showView("dashboard");
      sendSms("WELCOME", member.name, `Welcome to ${chamaName()}! Contributions: KES ${money(contribution())} due every ${state.chama.date}. Text HELP anytime for Vaulti, your financial coach.`);
      toast(`${chamaName()} is ready. Your invite code is ${state.chama.inviteCode}.`);
      outbox.classList.add("open");
    });
  });
}
function showJoinForm() {
  openModal(`<h2>Join ${escapeHtml(chamaName())}</h2><p class="modal-intro">Enter your invite code and details. Your new member profile starts with a score of 500.</p><form id="join-form"><div class="form-field"><label for="join-code">6-DIGIT INVITE CODE</label><input id="join-code" inputmode="numeric" value="${escapeHtml(state.chama.inviteCode)}" required /></div><div class="form-field"><label for="join-name">YOUR NAME</label><input id="join-name" required placeholder="e.g. Esther Wanjala" /></div><div class="form-row"><div class="form-field"><label for="join-phone">PHONE NUMBER</label><input id="join-phone" type="tel" required placeholder="07xx xxx xxx" /></div><div class="form-field"><label for="join-pin">4-DIGIT PIN</label><input id="join-pin" type="password" maxlength="4" inputmode="numeric" required /></div></div><div class="modal-actions"><button class="button button-green">Join chama</button></div></form>`);
  document.querySelector("#join-form").addEventListener("submit", event => {
    event.preventDefault();
    if (document.querySelector("#join-code").value !== state.chama.inviteCode) return toast("That invite code doesn’t match this chama.", true);
    const fullName = document.querySelector("#join-name").value.trim();
    const phone = document.querySelector("#join-phone").value.trim();
    if (!/^\d{4}$/.test(document.querySelector("#join-pin").value)) return toast("Choose a 4-digit PIN.", true);
    if (state.members.some(member => member.phone.replace(/\D/g, "") === phone.replace(/\D/g, ""))) return toast("That phone number is already in the group.", true);
    const initials = fullName.split(/\s+/).slice(0, 2).map(part => part[0].toUpperCase()).join("");
    const member = { id: `m${Date.now()}`, name: `${fullName.split(" ")[0]} ${fullName.split(" ").at(-1)[0]}.`, fullName, phone, initials, color: "blue", score: 500, status: "pending", time: "", method: "", streak: 0 };
    state.members.push(member); save(); render(); closeModal();
    sendSms("WELCOME", member.name, `Welcome to ${chamaName()}! Contributions: KES ${money(contribution())} due every ${state.chama.date}. Text HELP anytime for Vaulti, your financial coach.`);
    toast(`${member.name} joined ${chamaName()}. Welcome SMS sent.`);
    outbox.classList.add("open");
  });
}
document.querySelector("#invite-button").addEventListener("click", showInvite);
document.querySelector("#members-invite").addEventListener("click", showInvite);

const faq = [
  { keys: ["budget", "budgeting", "spend", "expenses"], answer: "A simple budget starts with what comes in and where it goes. Try splitting income into needs, savings, and wants. Even KES 50 saved before spending adds up. What is one expense you could plan for this week?" },
  { keys: ["compound", "interest"], answer: "Compound interest means your interest also earns interest over time. It’s like planting a sukuma wiki seed and saving the seeds from every harvest. Start early, save regularly, and give it time. Ask a licensed provider about the exact rates and fees." },
  { keys: ["chama", "rules", "group"], answer: "Good chama rules are agreed together and written down: contribution dates, how loans get approved, what happens when someone is late, and how records are corrected. In Umoja Sisters, every ledger entry is visible, and corrections leave the original in place." },
  { keys: ["money market", "mmf", "fund"], answer: "A money market fund pools members’ savings and invests in short-term assets. Returns can change and aren’t guaranteed. Before choosing one, check that the provider is CMA-licensed, ask about fees, withdrawal timing, and risks, and never invest money your group needs immediately." },
  { keys: ["loan shark", "loan", "debt", "borrow"], answer: "Be cautious of lenders who hide fees, pressure you to decide fast, or ask for your M-Pesa PIN. Compare the total repayment, not just the advertised rate. Your group loan rules can help keep borrowing fair and accountable." },
  { keys: ["emergency", "rainy day"], answer: "An emergency fund is money set aside for things like a clinic visit or a slow business week. Begin with a small, reachable target — even KES 100 each week — and keep it separate from everyday spending." },
  { keys: ["score", "credit", "rating"], answer: `Your score is ${userScore()} (${scoreLabel(userScore())}). Paying contributions on time, keeping a steady streak, and repaying loans as agreed can improve your record. ${userStreak() ? `You have a ${userStreak()}-month on-time streak — keep it up to move toward Very Good.` : "Pay on time this cycle to start a positive streak."}` },
  { keys: ["late", "miss", "overdue"], answer: "Life happens — one late contribution doesn’t define you. Let your treasurer know early if you need support, and make a plan that works for you. The group can keep its records honest while still treating members with kindness." },
  { keys: ["save", "saving", "savings"], answer: "Try saving a small amount as soon as money comes in, before other spending. Make it regular and realistic — KES 100 every week is a real start. In a chama, agree together on how savings are tracked and accessed." },
  { keys: ["mpesa", "m-pesa", "pin"], answer: "Never share your M-Pesa PIN or one-time password — not even with someone claiming to be from your chama. Check the paybill or till number with a trusted group member before sending money." },
  { keys: ["goal", "target"], answer: "A good savings goal is specific and shared: what you’re saving for, how much it costs, and when you need it. Umoja Sisters has a KES 8,000 cycle goal; you’re making steady progress together." },
  { keys: ["business", "side hustle", "hustle"], answer: "For a small business, write down money in and out each day — even in a simple notebook. Keep business money separate from household spending where you can, and test a new idea small before borrowing heavily." },
  { keys: ["insurance", "cover"], answer: "Insurance can help protect against a big unexpected cost, but read the exclusions, waiting period, and total premium carefully. Use a licensed provider and make sure the cover fits your real needs." },
  { keys: ["scam", "fraud", "safe"], answer: "Pause if someone asks for a PIN, promises guaranteed high returns, or pressures you to act now. Verify requests using a number you already know. In this chama, cash records and corrections are visible to every member." },
  { keys: ["hello", "hi", "habari", "sasa"], answer: "Habari! 😊 I’m here with simple, practical money guidance. Ask me about budgeting, chama savings, credit scores, loans, or keeping your M-Pesa safe." },
  { keys: ["asante", "thank", "kwaheri"], answer: "Karibu sana! Keep asking questions and keep building that savings habit. You’re doing this together. 🌱" }
];
function coachAnswer(question) {
  const normalized = question.toLowerCase();
  if (/\b(swahili|kiswahili|kwa kiswahili)\b/.test(normalized)) return "Ndiyo, naweza kukusaidia kwa Kiswahili! Niulize kuhusu kuweka akiba, bajeti, mikopo ya chama au alama yako ya mkopo. Hatuwezi kuahidi faida — soma masharti kabla ya kuwekeza.";
  const topic = faq.find(entry => entry.keys.some(key => normalized.includes(key)));
  if (topic) return topic.answer;
  return "That’s a thoughtful question. I can help with budgeting, savings goals, chama rules, credit scores, M-Pesa safety, emergency funds, and borrowing wisely. For investment decisions, check a licensed provider and understand the risks first. What part would you like to explore?";
}
function addChatMessage(text, isUser) {
  const container = document.querySelector("#chat-messages");
  const row = document.createElement("div");
  row.className = `message-row${isUser ? " user" : ""}`;
  const avatar = isUser ? `<span class="chat-message-avatar">K</span>` : `<span class="vaulti-avatar small">✳</span>`;
  row.innerHTML = `${isUser ? "" : avatar}<div class="bubble-wrap"><div class="chat-bubble">${escapeHtml(text)}</div><small>${isUser ? "You · just now" : "Vaulti · just now"}</small></div>${isUser ? avatar : ""}`;
  container.append(row); container.scrollTop = container.scrollHeight;
}
document.querySelector("#chat-form").addEventListener("submit", event => {
  event.preventDefault();
  const input = document.querySelector("#chat-input");
  const text = input.value.trim();
  if (!text) return;
  addChatMessage(text, true); input.value = "";
  setTimeout(() => addChatMessage(coachAnswer(text), false), 320);
});
document.querySelectorAll(".suggested-questions button").forEach(button => button.addEventListener("click", () => {
  const input = document.querySelector("#chat-input"); input.value = button.textContent; document.querySelector("#chat-form").requestSubmit();
}));
document.querySelector("#sms-coach").addEventListener("click", () => {
  openModal(`<h2>Vaulti · SMS mode</h2><p class="modal-intro">Send a text the way a feature-phone user would. Vaulti’s local FAQ still works offline.</p><form id="sms-coach-form"><div class="form-field"><label for="sms-question">YOUR SMS TO VAULTI</label><input id="sms-question" placeholder="e.g. How do I save better?" required /></div><div class="modal-actions"><button class="button button-green">Send SMS</button></div></form><div id="sms-answer"></div>`);
  document.querySelector("#sms-coach-form").addEventListener("submit", event => {
    event.preventDefault();
    const question = document.querySelector("#sms-question").value.trim();
    const answer = coachAnswer(question);
    sendSms("VAULTI", "Kamau N. · SMS", `You: ${question} Vaulti: ${answer}`);
    document.querySelector("#sms-answer").innerHTML = `<p class="modal-note">${escapeHtml(answer)}</p>`;
    outbox.classList.add("open");
  });
});

document.querySelector("#help-button").addEventListener("click", () => {
  openModal(`<h2>Demo guide</h2><p class="modal-intro">A seeded chama is ready to explore. SMS and M-Pesa are simulated; no real money moves.</p><div class="integrity-note"><span>◈</span><div><strong>Treasurer PIN: ${escapeHtml(state.treasurer.pin)}</strong><small>Use it to record a cash payment or publish a correction.</small></div></div><div class="form-field"><strong style="font-size:10px">Try the core flow</strong><p class="modal-note">Send a reminder · record a contribution · correct a ledger entry with a reason · check the member scores · ask Vaulti a question.</p></div><div class="modal-actions"><button class="button button-outline" id="reset-demo">Reset demo data</button><button class="button button-green" id="guide-outbox">Open SMS outbox</button></div>`);
  const btn = document.querySelector("#guide-outbox");
  if (btn) btn.addEventListener("click", () => { closeModal(); outbox.classList.add("open"); });
  document.querySelector("#reset-demo").addEventListener("click", () => {
    if (!window.confirm("Reset this device’s data to the Umoja Sisters demo seed?")) return;
    localStorage.removeItem(STORAGE_KEY);
    window.location.reload();
  });
});
render();
