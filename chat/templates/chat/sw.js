const CACHE_VERSION = 'v4';
const STATIC_CACHE  = `logersn-static-${CACHE_VERSION}`;
const HTML_CACHE    = `logersn-html-${CACHE_VERSION}`;

const STATIC_ASSETS = ['/chat/dashboard/', '/static/manifest.json', '/static/logo.png'];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then(cache => cache.addAll(STATIC_ASSETS).catch(() => {}))
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(names => Promise.all(
      names.map(n => (n !== STATIC_CACHE && n !== HTML_CACHE) ? caches.delete(n) : null)
    ))
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  if (request.method !== 'GET') return;
  if (url.pathname.startsWith('/api/')) return;
  if (request.url.startsWith('ws://') || request.url.startsWith('wss://')) return;
  if (url.pathname.startsWith('/static/') || url.hostname.includes('fonts.g') || url.hostname.includes('tailwind')) {
    event.respondWith(cacheFirst(request, STATIC_CACHE));
    return;
  }
  event.respondWith(networkFirst(request, HTML_CACHE));
});

async function networkFirst(request, cacheName) {
  try {
    const res = await fetch(request);
    if (res && res.status === 200 && res.type !== 'opaque') {
      const cache = await caches.open(cacheName);
      cache.put(request, res.clone());
    }
    return res;
  } catch {
    const cached = await caches.match(request);
    if (cached) return cached;
    if (request.mode === 'navigate') {
      return new Response(
        `<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>Hors ligne</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:system-ui,sans-serif;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100svh;background:#0f4f2c;color:#fff;padding:2rem;text-align:center}.icon{font-size:4rem;margin-bottom:1.5rem}h1{font-size:1.5rem;font-weight:800;margin-bottom:.75rem}p{color:rgba(255,255,255,.7);max-width:280px;line-height:1.6;margin-bottom:2rem}button{padding:.875rem 2.5rem;background:#fff;color:#0f4f2c;border:none;border-radius:999px;font-size:1rem;font-weight:700;cursor:pointer}</style></head><body><div class="icon">📶</div><h1>Hors Connexion</h1><p>Loger Sénégal CRM nécessite une connexion internet. Réessayez.</p><button onclick="location.reload()">Réessayer</button></body></html>`,
        { headers: { 'Content-Type': 'text/html;charset=utf-8' } }
      );
    }
    return new Response('', { status: 408 });
  }
}

async function cacheFirst(request, cacheName) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const res = await fetch(request);
    if (res && res.status === 200) {
      const cache = await caches.open(cacheName);
      cache.put(request, res.clone());
    }
    return res;
  } catch {
    return new Response('', { status: 408 });
  }
}
