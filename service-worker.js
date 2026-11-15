const CACHE = 'dietplans-catalogue-v6';
const CORE = ['./', './index.html', './app.js', './styles.css', './data/menus.json', './data/image-prompts.json', './reports/extraction.md', './manifest.webmanifest', './assets/catalogue-icon.svg', './assets/catalogue-icon-180.png', './assets/catalogue-icon-192.png', './assets/catalogue-icon-512.png'];
self.addEventListener('install', event => event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(CORE.map(path => new Request(path, {cache: 'reload'})))).then(() => self.skipWaiting())));
self.addEventListener('activate', event => event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => (key.startsWith('diet-companion-') || key.startsWith('dietplans-catalogue-')) && key !== CACHE).map(key => caches.delete(key)))).then(() => self.clients.claim()).then(async () => {
  const base = new URL('./', self.location.href);
  for (const client of await self.clients.matchAll({type:'window'})) {
    const url = new URL(client.url);
    if (['', 'index.html', 'diet-companion.html'].includes(url.pathname.slice(base.pathname.length))) await client.navigate(url.pathname.endsWith('/diet-companion.html') ? base.href : client.url);
  }
})));
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;
  const base = new URL('./', self.location.href);
  const relative = url.pathname.slice(base.pathname.length);
  // Do not cache the private source chat or unrelated files on this origin.
  const isImage = /^assets\/meals\/menu-\d+\.(png|jpg)$/.test(relative);
  const isCore = CORE.some(path => new URL(path, base).pathname === url.pathname);
  if (!isImage && !isCore) return;
  if (isImage) {
    event.respondWith(caches.open(CACHE).then(async cache => {
      const cached = await cache.match(event.request); if (cached) return cached;
      const response = await fetch(event.request); if (response.ok) await cache.put(event.request, response.clone()); return response;
    }));
    return;
  }
  // Network first prevents the old seven-day app from surviving a successful update.
  event.respondWith(caches.open(CACHE).then(async cache => {
    try { const response = await fetch(event.request); if (response.ok) await cache.put(event.request, response.clone()); return response; }
    catch { return await cache.match(event.request) || (event.request.mode === 'navigate' ? await cache.match('./index.html') : Response.error()); }
  }));
});
