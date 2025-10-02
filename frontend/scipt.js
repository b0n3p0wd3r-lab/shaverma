(function() {
  // Video Loading Screen Logic
  function initVideoLoadingScreen() {
    const videoLoadingScreen = document.getElementById('videoLoadingScreen');
    const loadingVideo = document.getElementById('loadingVideo');
    
    if (videoLoadingScreen && loadingVideo) {
      // Показываем экран загрузки на 5 секунд
      setTimeout(function() {
        videoLoadingScreen.classList.add('fade-out');
        
        // Полностью скрываем элемент после анимации
        setTimeout(function() {
          videoLoadingScreen.style.display = 'none';
        }, 500); // 500ms - время анимации fade-out
      }, 5000); // 5 секунд показа видео
      
      // Обработка ошибок загрузки видео
      loadingVideo.addEventListener('error', function() {
        console.warn('Не удалось загрузить видео загрузки');
        videoLoadingScreen.style.display = 'none';
      });
    }
  }
  
  // Запускаем экран загрузки сразу
  initVideoLoadingScreen();

  try {
    if (window.Telegram && window.Telegram.WebApp) {
      var tg = window.Telegram.WebApp;
      tg.expand();
      tg.ready();
      // Set a light/dark theme class on body if needed
      var theme = tg.colorScheme || 'light';
      document.documentElement.setAttribute('data-theme', theme);
      
      // Делаем Telegram WebApp доступным глобально для Unity
      window.TelegramWebApp = tg;
      
      // Функции для работы с API
      window.GameAPI = {
        // Получить баланс пользователя
        getUserBalance: function(callback) {
          if (!tg.initDataUnsafe.user) {
            callback({success: false, error: "No user data"});
            return;
          }
          
          var userId = tg.initDataUnsafe.user.id;
          var apiUrl = window.location.origin + '/api/user/balance?user_id=' + userId + '&auth_date=' + Date.now();
          
          fetch(apiUrl)
            .then(response => response.json())
            .then(data => callback(data))
            .catch(error => callback({success: false, error: error.message}));
        },
        
        // Потратить монеты
        spendCoins: function(amount, callback) {
          if (!tg.initDataUnsafe.user) {
            callback({success: false, error: "No user data"});
            return;
          }
          
          var userId = tg.initDataUnsafe.user.id;
          var apiUrl = window.location.origin + '/api/user/spend?user_id=' + userId + '&amount=' + amount + '&auth_date=' + Date.now();
          
          fetch(apiUrl)
            .then(response => response.json())
            .then(data => callback(data))
            .catch(error => callback({success: false, error: error.message}));
        },
        
        // Показать кнопку покупки монет
        showBuyCoinsButton: function() {
          if (tg.MainButton) {
            tg.MainButton.setText("💰 Купить монеты");
            tg.MainButton.show();
            tg.MainButton.onClick(function() {
              tg.close();
            });
          }
        },
        
        // Скрыть кнопку покупки монет
        hideBuyCoinsButton: function() {
          if (tg.MainButton) {
            tg.MainButton.hide();
          }
        }
      };
    }
  } catch (e) {
    console.error('Telegram WebApp initialization error:', e);
  }
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




