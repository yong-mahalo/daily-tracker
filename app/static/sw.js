// Minimal service worker — required for PWA install prompt on some platforms.
// We don't cache anything (always network-first) to keep data fresh.
self.addEventListener('fetch', (event) => {
  // Pass-through: always fetch from network
  event.respondWith(fetch(event.request));
});
