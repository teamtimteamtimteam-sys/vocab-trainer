/* 背单词 · Service Worker
   策略：stale-while-revalidate —— 打开即用缓存（离线可用），
   同时后台拉新版本写回缓存，下次打开生效。 */
const CACHE = "vocab-shell-v2";
const ASSETS = ["./", "./index.html", "./manifest.webmanifest", "./icon-180.png", "./icon-512.png"];

self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => Promise.allSettled(ASSETS.map(a => c.add(a))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  const r = e.request;
  if (r.method !== "GET") return;
  if (new URL(r.url).origin !== location.origin) return;

  const netP = fetch(r).then(resp => {
    if (resp && resp.ok) {
      const copy = resp.clone();
      caches.open(CACHE).then(c => c.put(r, copy));
    }
    return resp;
  }).catch(() => null);

  e.waitUntil(netP);
  e.respondWith((async () => {
    const cached = await caches.match(r, { ignoreSearch: true });
    if (cached) return cached;
    const fresh = await netP;
    if (fresh) return fresh;
    if (r.mode === "navigate") {
      const shell = await caches.match("./index.html");
      if (shell) return shell;
    }
    return Response.error();
  })());
});
