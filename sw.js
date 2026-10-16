const CACHE='zondi-v1';
const ASSETS=[
  '/',
  '/index.html',
  '/login.html',
  '/clients.html',
  '/patrol.html',
  '/register.html',
  '/logo.jpg',
  '/about.jpg',
  '/manifest.json'
];

// Install - save all for FREE MODE
self.addEventListener('install', e=>{
  self.skipWaiting();
  e.waitUntil(
    caches.open(CACHE).then(c=>c.addAll(ASSETS)).catch(()=>{})
  );
});

// Activate - take control
self.addEventListener('activate', e=>{
  e.waitUntil(
    caches.keys().then(keys=>Promise.all(
      keys.filter(k=>k!==CACHE).map(k=>caches.delete(k))
    )).then(()=>self.clients.claim())
  );
});

// Fetch - serve from cache when NO DATA
self.addEventListener('fetch', e=>{
  e.respondWith(
    caches.match(e.request).then(cached=>{
      return cached || fetch(e.request).then(res=>{
        // Save new files
        if(res.ok && e.request.method==='GET' && e.request.url.startsWith(self.location.origin)){
          let clone=res.clone();
          caches.open(CACHE).then(c=>c.put(e.request, clone));
        }
        return res;
      }).catch(()=>{
        // No data? Show cached index
        if(e.request.mode==='navigate'){
          return caches.match('/index.html');
        }
      });
    })
  );
});
