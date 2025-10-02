# 🎮 Интеграция платежной системы с Unity

## 📋 Обзор

Эта инструкция поможет интегрировать систему монет в вашу Unity игру через JavaScript API.

## 🔧 Настройка в Unity

### 1. Создание C# скрипта для взаимодействия с JavaScript

Создайте скрипт `TelegramPaymentManager.cs`:

```csharp
using System;
using System.Runtime.InteropServices;
using UnityEngine;

public class TelegramPaymentManager : MonoBehaviour
{
    [DllImport("__Internal")]
    private static extern void GetUserBalance(string callbackObjectName, string callbackMethodName);
    
    [DllImport("__Internal")]
    private static extern void SpendCoins(int amount, string callbackObjectName, string callbackMethodName);
    
    [DllImport("__Internal")]
    private static extern void ShowBuyCoinsButton();
    
    [DllImport("__Internal")]
    private static extern void HideBuyCoinsButton();
    
    public static TelegramPaymentManager Instance { get; private set; }
    
    [Header("UI Elements")]
    public TMPro.TextMeshProUGUI coinsText;
    public UnityEngine.UI.Button[] purchaseButtons; // 6 кнопок покупки
    
    [Header("Events")]
    public UnityEngine.Events.UnityEvent<int> OnCoinsUpdated;
    public UnityEngine.Events.UnityEvent<bool> OnPurchaseResult;
    
    private int currentCoins = 0;
    
    void Awake()
    {
        if (Instance == null)
        {
            Instance = this;
            DontDestroyOnLoad(gameObject);
        }
        else
        {
            Destroy(gameObject);
        }
    }
    
    void Start()
    {
        // Получаем текущий баланс при запуске
        RefreshBalance();
        
        // Настраиваем кнопки покупки (если они есть в игре)
        SetupPurchaseButtons();
    }
    
    void SetupPurchaseButtons()
    {
        if (purchaseButtons != null)
        {
            for (int i = 0; i < purchaseButtons.Length; i++)
            {
                int buttonIndex = i; // Захватываем индекс для замыкания
                purchaseButtons[i].onClick.AddListener(() => OnPurchaseButtonClicked(buttonIndex));
            }
        }
    }
    
    void OnPurchaseButtonClicked(int buttonIndex)
    {
        // Показываем кнопку покупки в Telegram
        ShowBuyCoinsButton();
        
        // Можно добавить логику для разных пакетов
        Debug.Log($"Purchase button {buttonIndex} clicked");
    }
    
    public void RefreshBalance()
    {
        #if UNITY_WEBGL && !UNITY_EDITOR
            GetUserBalance(gameObject.name, "OnBalanceReceived");
        #else
            // Для тестирования в редакторе
            OnBalanceReceived("{\"success\":true,\"data\":{\"coins\":100}}");
        #endif
    }
    
    public void TrySpendCoins(int amount)
    {
        if (amount <= 0)
        {
            Debug.LogError("Invalid coin amount");
            return;
        }
        
        #if UNITY_WEBGL && !UNITY_EDITOR
            SpendCoins(amount, gameObject.name, "OnSpendResult");
        #else
            // Для тестирования в редакторе
            if (currentCoins >= amount)
            {
                currentCoins -= amount;
                OnSpendResult("{\"success\":true,\"data\":{\"coins\":" + currentCoins + "}}");
            }
            else
            {
                OnSpendResult("{\"success\":false,\"message\":\"Insufficient coins\"}");
            }
        #endif
    }
    
    // Callback методы, вызываемые из JavaScript
    public void OnBalanceReceived(string jsonResponse)
    {
        try
        {
            var response = JsonUtility.FromJson<ApiResponse>(jsonResponse);
            if (response.success && response.data != null)
            {
                currentCoins = response.data.coins;
                UpdateCoinsUI();
                OnCoinsUpdated?.Invoke(currentCoins);
                Debug.Log($"Balance updated: {currentCoins} coins");
            }
            else
            {
                Debug.LogError($"Failed to get balance: {response.message}");
            }
        }
        catch (Exception e)
        {
            Debug.LogError($"Error parsing balance response: {e.Message}");
        }
    }
    
    public void OnSpendResult(string jsonResponse)
    {
        try
        {
            var response = JsonUtility.FromJson<ApiResponse>(jsonResponse);
            if (response.success && response.data != null)
            {
                currentCoins = response.data.coins;
                UpdateCoinsUI();
                OnCoinsUpdated?.Invoke(currentCoins);
                OnPurchaseResult?.Invoke(true);
                Debug.Log($"Coins spent successfully. New balance: {currentCoins}");
            }
            else
            {
                OnPurchaseResult?.Invoke(false);
                Debug.LogError($"Failed to spend coins: {response.message}");
            }
        }
        catch (Exception e)
        {
            Debug.LogError($"Error parsing spend response: {e.Message}");
        }
    }
    
    void UpdateCoinsUI()
    {
        if (coinsText != null)
        {
            coinsText.text = $"💎 {currentCoins}";
        }
    }
    
    public int GetCurrentCoins()
    {
        return currentCoins;
    }
    
    public bool CanAfford(int amount)
    {
        return currentCoins >= amount;
    }
}

// Классы для десериализации JSON ответов
[System.Serializable]
public class ApiResponse
{
    public bool success;
    public string message;
    public UserData data;
}

[System.Serializable]
public class UserData
{
    public int user_id;
    public int coins;
    public int total_purchases;
}
```

### 2. Создание JavaScript плагина

Создайте файл `TelegramAPI.jslib` в папке `Assets/Plugins/WebGL/`:

```javascript
var TelegramAPI = {
    GetUserBalance: function(callbackObjectName, callbackMethodName) {
        var objectName = UTF8ToString(callbackObjectName);
        var methodName = UTF8ToString(callbackMethodName);
        
        if (window.GameAPI && window.GameAPI.getUserBalance) {
            window.GameAPI.getUserBalance(function(response) {
                SendMessage(objectName, methodName, JSON.stringify(response));
            });
        } else {
            SendMessage(objectName, methodName, JSON.stringify({
                success: false, 
                message: "GameAPI not available"
            }));
        }
    },
    
    SpendCoins: function(amount, callbackObjectName, callbackMethodName) {
        var objectName = UTF8ToString(callbackObjectName);
        var methodName = UTF8ToString(callbackMethodName);
        
        if (window.GameAPI && window.GameAPI.spendCoins) {
            window.GameAPI.spendCoins(amount, function(response) {
                SendMessage(objectName, methodName, JSON.stringify(response));
            });
        } else {
            SendMessage(objectName, methodName, JSON.stringify({
                success: false, 
                message: "GameAPI not available"
            }));
        }
    },
    
    ShowBuyCoinsButton: function() {
        if (window.GameAPI && window.GameAPI.showBuyCoinsButton) {
            window.GameAPI.showBuyCoinsButton();
        }
    },
    
    HideBuyCoinsButton: function() {
        if (window.GameAPI && window.GameAPI.hideBuyCoinsButton) {
            window.GameAPI.hideBuyCoinsButton();
        }
    }
};

mergeInto(LibraryManager.library, TelegramAPI);
```

### 3. Пример использования в игре

```csharp
public class ShopManager : MonoBehaviour
{
    [Header("Shop Items")]
    public ShopItem[] shopItems;
    
    void Start()
    {
        // Подписываемся на события обновления монет
        if (TelegramPaymentManager.Instance != null)
        {
            TelegramPaymentManager.Instance.OnCoinsUpdated.AddListener(OnCoinsUpdated);
            TelegramPaymentManager.Instance.OnPurchaseResult.AddListener(OnPurchaseComplete);
        }
    }
    
    public void BuyItem(int itemIndex)
    {
        if (itemIndex < 0 || itemIndex >= shopItems.Length) return;
        
        var item = shopItems[itemIndex];
        
        if (TelegramPaymentManager.Instance.CanAfford(item.price))
        {
            TelegramPaymentManager.Instance.TrySpendCoins(item.price);
        }
        else
        {
            // Показываем кнопку покупки монет
            TelegramPaymentManager.Instance.ShowBuyCoinsButton();
            Debug.Log("Not enough coins! Show purchase options.");
        }
    }
    
    void OnCoinsUpdated(int newAmount)
    {
        Debug.Log($"Coins updated: {newAmount}");
        // Обновляем UI магазина
        UpdateShopUI();
    }
    
    void OnPurchaseComplete(bool success)
    {
        if (success)
        {
            Debug.Log("Purchase completed successfully!");
            // Выдаем купленный предмет игроку
        }
        else
        {
            Debug.Log("Purchase failed!");
        }
    }
    
    void UpdateShopUI()
    {
        // Обновляем доступность кнопок покупки
        for (int i = 0; i < shopItems.Length; i++)
        {
            bool canAfford = TelegramPaymentManager.Instance.CanAfford(shopItems[i].price);
            // Обновляем UI кнопки
        }
    }
}

[System.Serializable]
public class ShopItem
{
    public string name;
    public int price;
    public Sprite icon;
}
```

## 🎯 Интеграция с вкладкой "Купить денег"

### В Unity создайте UI с 6 кнопками:

```csharp
public class PurchaseUI : MonoBehaviour
{
    [Header("Purchase Buttons")]
    public Button[] purchaseButtons = new Button[6];
    
    // Цены соответствуют пакетам в bot.py
    private int[] coinAmounts = {100, 250, 650, 1400, 3000, 6500};
    private int[] prices = {50, 100, 250, 500, 1000, 2000};
    
    void Start()
    {
        for (int i = 0; i < purchaseButtons.Length; i++)
        {
            int index = i; // Захват для замыкания
            purchaseButtons[i].onClick.AddListener(() => OnPurchaseClicked(index));
            
            // Обновляем текст кнопки
            var buttonText = purchaseButtons[i].GetComponentInChildren<TMPro.TextMeshProUGUI>();
            if (buttonText != null)
            {
                buttonText.text = $"💎 {coinAmounts[i]}\n{prices[i]}₽";
            }
        }
    }
    
    void OnPurchaseClicked(int packageIndex)
    {
        // Показываем кнопку покупки в Telegram
        if (TelegramPaymentManager.Instance != null)
        {
            TelegramPaymentManager.Instance.ShowBuyCoinsButton();
        }
        
        Debug.Log($"Purchase package {packageIndex}: {coinAmounts[packageIndex]} coins for {prices[packageIndex]}₽");
    }
}
```

## 🚀 Запуск и тестирование

1. **Соберите WebGL билд** с настроенными скриптами
2. **Запустите бота** с платежной системой
3. **Запустите API сервер**: `python backend/web_api.py`
4. **Протестируйте** покупку монет через Telegram
5. **Проверьте** обновление баланса в игре

## 🔧 Отладка

- Используйте `Debug.Log` для отслеживания вызовов API
- Проверьте консоль браузера на ошибки JavaScript
- Убедитесь, что API сервер запущен и доступен
- Проверьте CORS настройки для локальной разработки
