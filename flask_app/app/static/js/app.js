// ChamaVault client script: viewer switch, payment form behaviour, Vaulti chat, print button.
(function () {
  const csrf = () => document.querySelector('meta[name="csrf-token"]').content;

  // "Viewing as" dropdown submits on change.
  document.querySelectorAll('[data-autosubmit]').forEach((el) =>
    el.addEventListener('change', () => el.form.submit()));

  // Print / save as PDF.
  document.querySelectorAll('[data-print]').forEach((el) =>
    el.addEventListener('click', () => window.print()));

  // Payment screen: auto-fill amount, lock fixed items, toggle M-Pesa/Card sections.
  const payForm = document.getElementById('pay-form');
  if (payForm) {
    const item = payForm.elements.item, amount = payForm.elements.amount;
    const sync = () => {
      const opt = item.selectedOptions[0];
      amount.value = opt.dataset.amount;
      amount.readOnly = opt.dataset.editable !== '1';
      amount.max = opt.dataset.max || '';
      document.getElementById('amount-hint').textContent =
        amount.readOnly ? 'Fixed amount' : 'You can change this amount (max KES ' + Number(opt.dataset.max).toLocaleString() + ')';
    };
    const method = () => {
      const m = payForm.elements.method.value;
      document.getElementById('mpesa-box').classList.toggle('hidden', m !== 'mpesa');
      document.getElementById('card-box').classList.toggle('hidden', m !== 'card');
      document.getElementById('mpesa-box').querySelectorAll('input').forEach((i) => (i.disabled = m !== 'mpesa'));
      document.getElementById('card-box').querySelectorAll('input').forEach((i) => (i.disabled = m !== 'card'));
    };
    item.addEventListener('change', sync);
    payForm.querySelectorAll('input[name=method]').forEach((r) => r.addEventListener('change', method));
    // Never keep card details around after the form is sent or the page is restored from cache.
    payForm.addEventListener('submit', () => setTimeout(() =>
      payForm.querySelectorAll('#card-box input').forEach((i) => (i.value = '')), 0));
    const keepAmount = amount.dataset.keep;
    sync(); if (keepAmount) amount.value = keepAmount; method();
  }

  // Cash form: member picks which items are payable.
  const cash = document.getElementById('cash-form');
  if (cash) {
    const options = JSON.parse(document.getElementById('cash-options').textContent);
    const member = cash.elements.member_id, item = cash.elements.item, amount = cash.elements.amount;
    const fill = () => {
      item.innerHTML = '';
      options[member.value].forEach((o) => {
        const opt = new Option(o.label, o.key); opt.dataset.amount = o.amount; item.add(opt);
      });
      amount.value = item.selectedOptions[0].dataset.amount;
    };
    member.addEventListener('change', fill);
    item.addEventListener('change', () => (amount.value = item.selectedOptions[0].dataset.amount));
    fill();
  }

  // Vaulti chat: ask without reloading; falls back to a normal form post if fetch fails.
  const chat = document.getElementById('vaulti-form');
  if (chat) {
    const log = document.getElementById('chat-log');
    const add = (cls, text) => { const d = document.createElement('div'); d.className = 'bubble ' + cls; d.textContent = text; log.appendChild(d); d.scrollIntoView({ block: 'nearest' }); };
    const ask = async (q) => {
      add('me', q);
      try {
        const res = await fetch(chat.action, { method: 'POST', headers: { 'Accept': 'application/json', 'X-CSRFToken': csrf() },
          body: new URLSearchParams({ question: q, lang: chat.elements.lang.value }) });
        add('bot', (await res.json()).answer);
      } catch (e) { add('bot', 'Sorry, I could not reach the coach. Please try again.'); }
    };
    chat.addEventListener('submit', (e) => {
      e.preventDefault();
      const q = chat.elements.question.value.trim();
      if (q) { chat.elements.question.value = ''; ask(q); }
    });
    document.querySelectorAll('[data-ask]').forEach((b) => b.addEventListener('click', () => ask(b.dataset.ask)));
  }
})();
