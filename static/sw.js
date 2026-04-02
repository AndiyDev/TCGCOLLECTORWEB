self.addEventListener('install', (e) => {
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(clients.claim());
});

self.addEventListener('fetch', (e) => {
  // Detta krävs av webbläsare för att de ska tillåta att appen installeras
  e.respondWith(fetch(e.request).catch(() => new Response("Du är offline.")));
});