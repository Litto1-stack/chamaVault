// Service worker: keeps the app shell and the last-seen pages available offline.
// Only GET pages are cached; payments and other POSTs always need a connection.
const CACHE = 'chamavault-v1';
const SHELL = ['/', '/static/css/style.css', '/static/js/app.js', '/static/icon.svg'];

self.addEventListener('install', (e) => e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting())));
self.addEventListener('activate', (e) => e.waitUntil(
  caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim())));

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== location.origin) return;
  if (req.url.includes('/receipt/') || req.url.includes('/statement')) return;      // never cache personal documents
  e.respondWith(
    fetch(req).then((res) => {
      if (res.ok) { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(req, copy)); }
      return res;
    }).catch(() => caches.match(req).then((hit) => hit || new Response(
      '<h1 style="font-family:sans-serif">You are offline</h1><p style="font-family:sans-serif">Open a page you visited before, or reconnect to make payments.</p>',
      { headers: { 'Content-Type': 'text/html' }, status: 503 }))));
});
