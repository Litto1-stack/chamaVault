// Calculators: loan (flat / reducing), savings growth, share-out. Pure maths in the browser.
(function () {
  const $ = (id) => document.getElementById(id);
  const num = (id) => Math.max(0, parseFloat(String($(id).value).replace(/,/g, '')) || 0);
  const kes = (n) => 'KES ' + Math.round(n).toLocaleString('en-KE');

  function loan() {
    const p = num('l-amount'), n = Math.max(1, Math.min(60, Math.round(num('l-months')))), rate = num('l-rate');
    const type = $('l-type').value;
    let pay, total;
    if (type === 'reducing' && rate > 0) {
      const r = rate / 100; pay = Math.ceil(p * r / (1 - Math.pow(1 + r, -n))); total = pay * n;
    } else { total = Math.round(p * (100 + rate) / 100); pay = Math.ceil(total / n); }
    $('l-pay').textContent = kes(pay); $('l-total').textContent = kes(total); $('l-int').textContent = kes(total - p);
    let bal = p, rows = '<tr><th>Month</th><th>Pay</th><th>Interest</th><th>Balance</th></tr>';
    for (let m = 1; m <= Math.min(n, 12); m++) {
      const interest = type === 'reducing' ? bal * rate / 100 : (total - p) / n;
      const principal = pay - interest; bal = Math.max(0, bal - principal);
      rows += `<tr><td>${m}</td><td>${kes(pay)}</td><td>${kes(interest)}</td><td>${kes(bal)}</td></tr>`;
    }
    $('l-table').innerHTML = rows;
  }

  function save() {
    const m = num('s-monthly'), years = Math.min(50, num('s-years')), r = num('s-rate') / 100 / 12;
    let bal = 0, pts = [0];
    for (let i = 1; i <= years * 12; i++) { bal = (bal + m) * (1 + r); if (i % 3 === 0) pts.push(bal); }
    const put = m * years * 12;
    $('s-final').textContent = kes(bal); $('s-in').textContent = kes(put); $('s-growth').textContent = kes(bal - put);
    const max = Math.max(...pts, 1), w = 320, h = 110;
    const line = pts.map((v, i) => `${(i * w / Math.max(1, pts.length - 1)).toFixed(1)},${(h - 6 - v / max * (h - 14)).toFixed(1)}`).join(' ');
    $('s-chart').innerHTML = `<polygon points="0,${h} ${line} ${w},${h}" style="fill:var(--green);opacity:.15"/>` +
      `<polyline points="${line}" style="fill:none;stroke:var(--green);stroke-width:2.5"/>`;
  }

  function share() {
    const g = num('h-group');
    $('h-share').textContent = g ? kes(num('h-profit') * Math.min(num('h-mine'), g) / g) : '–';
  }

  [['calc-loan', loan], ['calc-save', save], ['calc-share', share]].forEach(([id, fn]) => {
    $(id).querySelectorAll('input,select').forEach((el) => el.addEventListener('input', fn));
    fn();
  });
})();
