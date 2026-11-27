var VER='1.3.3';
var CACHE='pca-'+VER;
var SHELL=['./','index.html','manifest.json','icon-192.png','icon-180.png','icon-512.png','logo.png'];
self.addEventListener('install',function(e){
  e.waitUntil(caches.open(CACHE).then(function(c){return c.addAll(SHELL);}).then(function(){return self.skipWaiting();}));
});
self.addEventListener('activate',function(e){
  e.waitUntil(caches.keys().then(function(ks){
    return Promise.all(ks.filter(function(k){return k!==CACHE;}).map(function(k){return caches.delete(k);}));
  }).then(function(){return self.clients.claim();}));
});
self.addEventListener('fetch',function(e){
  var r=e.request;
  if(r.method!=='GET')return;
  var u=new URL(r.url);
  if(u.origin!==location.origin)return;
  e.respondWith(
    fetch(r,{cache:'no-cache'}).then(function(res){
      if(res&&res.ok&&u.pathname.indexOf('version.json')<0){var cp=res.clone();caches.open(CACHE).then(function(c){c.put(r,cp);});}
      return res;
    }).catch(function(){return caches.match(r).then(function(m){return m||caches.match('index.html');});})
  );
});
