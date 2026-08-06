/**
 * Service Worker — ATS Recluta PWA
 * Estrategia: Cache-first para estáticos, Network-first para páginas dinámicas
 */

const CACHE_NAME = 'ats-recluta-v2';
const STATIC_CACHE = 'ats-static-v2';

// Recursos estáticos a cachear en instalación
const STATIC_ASSETS = [
  '/static/css/ats.css',
  '/static/js/ats.js',
  '/manifest.json',
  '/static/img/icon-192.png',
  '/static/img/icon-512.png',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js',
];

// Página offline de fallback
const OFFLINE_PAGE = '/offline/';

// ─── Instalación: precachear estáticos ───────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then(cache => {
      return cache.addAll(STATIC_ASSETS).catch(err => {
        console.warn('[SW] Error precacheando algunos recursos:', err);
      });
    }).then(() => self.skipWaiting())
  );
});

// ─── Activación: limpiar caches anteriores ───────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(k => k !== CACHE_NAME && k !== STATIC_CACHE)
            .map(k => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

// ─── Fetch: estrategia por tipo de recurso ───────────────────
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Solo manejar peticiones del mismo origen o CDNs conocidos
  const isOwnOrigin = url.origin === self.location.origin;
  const isCDN = url.hostname.includes('cdn.jsdelivr.net') ||
                url.hostname.includes('code.jquery.com');

  if (!isOwnOrigin && !isCDN) return;

  // Ignorar peticiones no GET
  if (request.method !== 'GET') return;

  // Ignorar rutas de admin de Django y API
  const skipPaths = ['/admin/', '/login/', '/logout/', '/registro/'];
  if (skipPaths.some(p => url.pathname.startsWith(p))) return;

  // Estáticos: Cache-first
  if (url.pathname.startsWith('/static/') || isCDN) {
    event.respondWith(
      caches.match(request).then(cached => {
        if (cached) return cached;
        return fetch(request).then(response => {
          if (response && response.status === 200) {
            const clone = response.clone();
            caches.open(STATIC_CACHE).then(cache => cache.put(request, clone));
          }
          return response;
        }).catch(() => new Response('', { status: 503 }));
      })
    );
    return;
  }

  // Páginas dinámicas: Network-first con fallback a cache
  event.respondWith(
    fetch(request)
      .then(response => {
        if (response && response.status === 200) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(request, clone));
        }
        return response;
      })
      .catch(() =>
        caches.match(request).then(cached => {
          if (cached) return cached;
          // Fallback: página offline
          if (request.destination === 'document') {
            return caches.match(OFFLINE_PAGE);
          }
          return new Response('Sin conexión', { status: 503 });
        })
      )
  );
});
