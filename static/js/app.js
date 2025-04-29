
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/js/service-worker.js')
      .then(registration => {
        console.log('ServiceWorker registered');
      })
      .catch(err => {
        console.log('ServiceWorker registration failed: ', err);
      });
  });
}
