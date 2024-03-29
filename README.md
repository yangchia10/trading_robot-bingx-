# 自動化交易系統

這是一個使用 Python 和 Selenium 構建的自動化交易系統，專門針對 BingX 平台。它會自動抓取平台上的數據，根據預定的交易策略進行運算，並自動執行交易掛單。

## 功能

- 自動抓取 BingX 平台上的交易數據
- 根據預定的交易策略進行運算
- 自動執行交易掛單

## 安裝

本系統需要 Python 3.9 和以下依賴包：
selenium==4.15.2
PyQt5==5.15.10

您可以使用 pip 安裝這些依賴：

```bash
pip install -r requirements.txt
```

## 使用方法

啟動系統：

```bash
python app.py

啟動之後再新開啟的網頁登入bingx，並開到標準合約。
先設定布林帶(BB) 在設定移動平均線(MA)
```

根據提示輸入相關參數，系統將開始自動運行。

## 缺少商業機密文件處理

由於 trade_utils.py 文件包含商業機密，因此未包含在此存儲庫中。在運行系統之前，您需要：

獲取 trade_utils.py 文件的副本。
將該文件放置在與 app.py 相同的目錄中。
如果您沒有 trade_utils.py 文件的訪問權限，請聯繫系統管理員或開發者獲取幫助。

## 注意事項

確保您的環境中已安裝了 Chrome 瀏覽器並且已設置環境變量。
本系統目前僅支持 BingX 平台。

## 流程圖

```mermaid
graph TD
    app["app.py (主要應用程序)"]
    run_commands["run_commands.py (運行命令)"]
    price_thread["price_thread.py (價格監控)"]
    Funds_thread["Funds_thread.py (資金監控)"]
    HOLD_thread["HOLD_thread.py (持倉監控)"]
    entrust_thread["entrust_thread.py (委託監控)"]
    Trading_straregy["Trading_straregy.py (抓取價格)"]
    trade_utils["trade_utils.py (交易策略)"]
    priceVariable["priceVariable.py (價格變量處理)"]

    app --> run_commands
    app --> price_thread
    app --> Funds_thread
    app --> HOLD_thread
    app --> entrust_thread
    app --> Trading_straregy
    app --> priceVariable

    price_thread --> trade_utils
    Trading_straregy --> trade_utils
    priceVariable --> trade_utils
```

