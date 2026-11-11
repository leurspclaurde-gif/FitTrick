// Offline cache for the app shell. Bump VERSION on every release so iPhones pick up the new files.
const VERSION = 'fittrick-v1';
const FILES = ['./', 'index.html', 'css/app.css', 'js/main.js', 'js/planner.js', 'js/weights.js', 'js/data.js',
  'manifest.webmanifest', 'img/splash.webp', 'img/icon-180.png', 'img/icon-192.png', 'img/icon-512.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== VERSION).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== location.origin) return; // API calls go straight to the network
  // network first (fresh code when online), cache as fallback (gym without signal)
  e.respondWith(fetch(e.request).then(res => {
    const copy = res.clone();
    caches.open(VERSION).then(c => c.put(e.request, copy));
    return res;
  }).catch(() => caches.match(e.request).then(r => r || caches.match('index.html'))));
});
