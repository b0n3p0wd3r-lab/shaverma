(function() {
  try {
    if (window.Telegram && window.Telegram.WebApp) {
      var tg = window.Telegram.WebApp;
      tg.expand();
      tg.ready();
      // Set a light/dark theme class on body if needed
      var theme = tg.colorScheme || 'light';
      document.documentElement.setAttribute('data-theme', theme);
    }
  } catch (e) {}
  function setViewportUnit() {
    var vh = window.innerHeight * 0.01;
    document.documentElement.style.setProperty('--vh', vh + 'px');
  }

  setViewportUnit();
  window.addEventListener('resize', setViewportUnit);
  window.addEventListener('orientationchange', function() {
    setTimeout(setViewportUnit, 300);
  });

  var frame = document.getElementById('gameFrame');
  var overlay = document.getElementById('loadingOverlay');
  var btnReload = null;
  var btnFullscreen = null;
  if (frame) {
    try {
      var isLocalhost = /^(localhost|127\.0\.0\.1)$/i.test(window.location.hostname);
      var src = frame.getAttribute('src') || '';
      var isAbsolute = /^https?:\/\//i.test(src);
      if (isLocalhost && !isAbsolute) {
        frame.src = 'http://localhost:3000/public/webgl_game/index.html';
      }
    } catch (e) {}
    frame.addEventListener('load', function() {
      if (overlay) overlay.style.display = 'none';
      try { frame.contentWindow.focus(); } catch (e) {}
    });
  }

  

  
})();




