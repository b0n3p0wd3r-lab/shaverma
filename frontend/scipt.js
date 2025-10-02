(function() {
  // Video Loading Screen Logic
  function initVideoLoadingScreen() {
    const videoLoadingScreen = document.getElementById('videoLoadingScreen');
    const loadingVideo = document.getElementById('loadingVideo');
    const gameFrame = document.getElementById('gameFrame');
    const loadingIndicator = document.getElementById('unityLoadingIndicator');
    
    if (videoLoadingScreen && loadingVideo) {
      let isUnityReady = false;
      let checkAttempts = 0;
      const maxCheckAttempts = 300; // 30 секунд максимум (проверка каждые 100мс)
      
      // Функция обновления индикатора загрузки
      function updateLoadingIndicator(status) {
        if (loadingIndicator) {
          switch (status) {
            case 'waiting':
              loadingIndicator.innerHTML = 'Ожидание игры<span class="progress-dots"></span>';
              break;
            case 'loading':
              loadingIndicator.innerHTML = 'Загрузка Unity<span class="progress-dots"></span>';
              break;
            case 'initializing':
              loadingIndicator.innerHTML = 'Инициализация<span class="progress-dots"></span>';
              break;
            case 'ready':
              loadingIndicator.innerHTML = 'Готово!';
              break;
            default:
              loadingIndicator.innerHTML = 'Загрузка игры<span class="progress-dots"></span>';
          }
        }
      }
      
      // Функция проверки готовности Unity
      function checkUnityReady() {
        checkAttempts++;
        
        // Обновляем индикатор в зависимости от прогресса
        if (checkAttempts < 50) {
          updateLoadingIndicator('waiting');
        } else if (checkAttempts < 150) {
          updateLoadingIndicator('loading');
        } else {
          updateLoadingIndicator('initializing');
        }
        
        try {
          // Проверяем доступность iframe и его содержимого
          if (gameFrame && gameFrame.contentWindow) {
            const iframeDoc = gameFrame.contentWindow.document;
            const iframeWindow = gameFrame.contentWindow;
            
            // Ищем признаки загруженной Unity игры (расширенный поиск)
            const unityCanvas = iframeDoc.querySelector('#unity-canvas') || 
                              iframeDoc.querySelector('canvas') ||
                              iframeDoc.querySelector('#gameContainer canvas') ||
                              iframeDoc.querySelector('.unity-desktop canvas') ||
                              iframeDoc.querySelector('.unity-mobile canvas');
            
            // Проверяем наличие Unity объектов в окне iframe
            const hasUnityInstance = iframeWindow.unityInstance || 
                                   iframeWindow.gameInstance ||
                                   iframeWindow.Module ||
                                   iframeWindow.Unity ||
                                   iframeWindow.UnityLoader;
            
            // Проверяем, что Unity загрузился (canvas видимый и имеет контент)
            const isCanvasReady = unityCanvas && 
                                unityCanvas.width > 0 && 
                                unityCanvas.height > 0 &&
                                unityCanvas.style.display !== 'none' &&
                                !unityCanvas.style.visibility === 'hidden';
            
            // Дополнительная проверка - ищем элементы Unity UI
            const hasUnityUI = iframeDoc.querySelector('.unity-mobile') ||
                              iframeDoc.querySelector('#unity-container') ||
                              iframeDoc.querySelector('[data-unity]') ||
                              iframeDoc.querySelector('.unity-desktop') ||
                              iframeDoc.querySelector('#unityContainer');
            
            // Специальная проверка для кликер игры - ищем игровые элементы
            const hasGameElements = iframeDoc.querySelector('[class*="clicker"]') ||
                                  iframeDoc.querySelector('[class*="game"]') ||
                                  iframeDoc.querySelector('[class*="score"]') ||
                                  iframeDoc.querySelector('[class*="coin"]') ||
                                  iframeDoc.querySelector('button') ||
                                  iframeDoc.querySelector('.ui-button') ||
                                  iframeDoc.querySelector('[onclick]');
            
            // Unity считается готовым если есть canvas И (Unity instance ИЛИ Unity UI ИЛИ игровые элементы)
            if (isCanvasReady && (hasUnityInstance || hasUnityUI || hasGameElements)) {
              console.log('Unity игра успешно загружена!');
              updateLoadingIndicator('ready');
              setTimeout(() => hideVideoLoadingScreen(), 500); // Показываем "Готово!" на полсекунды
              return;
            }
            
            // Альтернативная проверка - если iframe полностью загружен и нет элементов загрузки
            const loadingElements = iframeDoc.querySelectorAll(
              '.unity-progress, .unity-loading, [class*="loading"], [class*="Loading"], ' +
              '[id*="loading"], [id*="Loading"], .progress, .spinner, .loader'
            );
            const isIframeFullyLoaded = iframeDoc.readyState === 'complete';
            
            // Проверяем, что нет видимых элементов загрузки
            const hasVisibleLoaders = Array.from(loadingElements).some(el => 
              el.style.display !== 'none' && 
              el.style.visibility !== 'hidden' && 
              el.offsetParent !== null
            );
            
            if (isIframeFullyLoaded && !hasVisibleLoaders && unityCanvas) {
              console.log('Unity игра загружена (альтернативная проверка)');
              updateLoadingIndicator('ready');
              setTimeout(() => hideVideoLoadingScreen(), 500);
              return;
            }
            
            // Дополнительное логирование для отладки
            if (checkAttempts % 50 === 0) { // Логируем каждые 5 секунд
              console.log('Unity проверка:', {
                attempt: checkAttempts,
                hasCanvas: !!unityCanvas,
                canvasSize: unityCanvas ? `${unityCanvas.width}x${unityCanvas.height}` : 'N/A',
                canvasReady: isCanvasReady,
                hasUnityInstance: hasUnityInstance,
                hasUnityUI: hasUnityUI,
                hasGameElements: hasGameElements,
                iframeLoaded: isIframeFullyLoaded,
                loadingElementsCount: loadingElements.length,
                hasVisibleLoaders: hasVisibleLoaders
              });
            }
            
          }
        } catch (e) {
          // Игнорируем ошибки доступа к iframe (CORS и т.д.)
          console.log('Проверка Unity (попытка ' + checkAttempts + '): iframe недоступен');
        }
        
        // Продолжаем проверку, если не достигли лимита
        if (checkAttempts < maxCheckAttempts && !isUnityReady) {
          setTimeout(checkUnityReady, 100); // Проверяем каждые 100мс
        } else if (!isUnityReady) {
          // Резервное скрытие через максимальное время
          console.log('Unity проверка завершена по таймауту, скрываем загрузочный экран');
          hideVideoLoadingScreen();
        }
      }
      
      // Функция скрытия видео загрузки
      function hideVideoLoadingScreen() {
        if (!isUnityReady) {
          isUnityReady = true;
          videoLoadingScreen.classList.add('fade-out');
          
          // Также скрываем обычный loading overlay
          const overlay = document.getElementById('loadingOverlay');
          if (overlay) {
            overlay.style.display = 'none';
          }
          
          // Полностью скрываем элемент после анимации
          setTimeout(function() {
            videoLoadingScreen.style.display = 'none';
          }, 500); // 500ms - время анимации fade-out
        }
      }
      
      // Инициализируем индикатор
      updateLoadingIndicator('waiting');
      
      // Начинаем проверку после загрузки iframe
      gameFrame.addEventListener('load', function() {
        console.log('Iframe загружен, начинаем проверку Unity...');
        updateLoadingIndicator('loading');
        // Даем немного времени Unity на инициализацию
        setTimeout(checkUnityReady, 500);
      });
      
      // Также начинаем проверку сразу, если iframe уже загружен
      if (gameFrame.complete || gameFrame.readyState === 'complete') {
        setTimeout(checkUnityReady, 500);
      }
      
      // Обработка ошибок загрузки видео
      loadingVideo.addEventListener('error', function() {
        console.warn('Не удалось загрузить видео загрузки');
        hideVideoLoadingScreen();
      });
      
      // Резервный таймер на случай, если что-то пойдет не так
      setTimeout(function() {
        if (!isUnityReady) {
          console.log('Резервный таймер: принудительно скрываем загрузочный экран');
          hideVideoLoadingScreen();
        }
      }, 30000); // 30 секунд максимум
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
      // Не скрываем overlay сразу, ждем полной загрузки Unity
      console.log('Iframe загружен, ожидаем полной загрузки Unity...');
      try { frame.contentWindow.focus(); } catch (e) {}
    });
  }

  

  
})();




