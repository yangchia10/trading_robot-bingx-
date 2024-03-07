from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
from PyQt5.QtCore import QMetaObject, Qt, Q_ARG
from datetime import datetime

from trade_utils import order_trade

prev_current_price = 0  # 初始值設為0或合適的初始值

def set_values_in_webpage(browser, url, initial_funds, leverage_xpath, takeProfit_xpath, takeProfit_input_xpath, stoploss_Xpath, trigger_stoploss_Xpath, confirm_button_xpath):
    try:
        if browser.current_url != url:
            browser.get(url)
            time.sleep(3)  # 避免頻繁刷新，只在必要時加載頁面

        time.sleep(1)# 在填寫前暫停一秒
        # 假設這裡有一個輸入框來設置交易金額，這裡需要替換成實際的Xpath
        amount_input_xpath = '//*[@id="__layout"]/div/div/div[3]/div/div/div[4]/div/div[2]/div[1]/div/div/div[2]/input'
        WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.XPATH, amount_input_xpath)))
        amount_input = browser.find_element(By.XPATH, amount_input_xpath)
        amount_input.clear()
        amount_input.send_keys(str(initial_funds))
        print("設置交易金額:".format(initial_funds))
        time.sleep(1)# 在填寫後暫停一秒

        # 下面是對槓桿、止盈、止損等選項的操作，根據實際情況進行調整
        # 設置槓桿
        WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, leverage_xpath))).click()
        print("設置槓桿成功")

        # 設置止盈
        WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, takeProfit_xpath))).click()
        # 等待止盈的 input 元素變為可見，並獲取它
        takeProfit_input = WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.XPATH, takeProfit_input_xpath)))
        # 使用JavaScript清空輸入框並輸入新的值
        takeProfit_input.click()  # 點擊以確保輸入框被激活
        time.sleep(1)
        browser.execute_script("arguments[0].value = '';", takeProfit_input)  # 清空輸入框
        time.sleep(1)
        takeProfit_input.send_keys("6")  # 輸入新的值
        time.sleep(1)
        print("設置止盈成功")

        # 設置止損
        WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, stoploss_Xpath))).click()
        WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, trigger_stoploss_Xpath))).click()
        print("設置止損成功")

        # 假設這裡有一個確認交易的按鈕，我們也需要點擊它
        WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, confirm_button_xpath))).click()
        print("交易執行")

        # 在完成操作後滾動回頁面頂部
        browser.execute_script("window.scrollTo(0, 0);")
        print("滾動回頁面頂部")

    except Exception as e:
        print(f"An error occurred: {e}")

def main_priceVariable(browser, selected_url, data, app, initial_funds_str):
    global prev_current_price  # 使用全局變量保存前一秒的價格
    try:

        # 打印接收到的數據，確認函數被正確調用
        print("收到 main_priceVariable 中的數據:", data)
        # 從傳入的數據字典中解析所需參數
        BB_upside = data["BB_upside"]
        BB_middle = data["BB_middle"]
        BB_under = data["BB_under"]
        MA = data["MA"]
        initial_funds = data["initial_funds"]  # 假設這個值也是通過某種方式獲取的
        current_price = float(data["current_price"])
        first_price_history = float(data["first_price_history"])
        funds = data["funds"]
        strategy_type = data["strategy_type"]

        strategy_type = app.strategy_type  # Assuming you've stored the strategy type in the app object

        # 將 initial_funds_str 轉換為浮點數
        if isinstance(initial_funds_str, str):
            initial_funds = float(initial_funds_str.replace("VST", "").replace("USDT", "").replace(",", "").strip())
        else:
            initial_funds = initial_funds_str

        # 解析數據
        current_funds = float(funds.replace("VST", "").replace("USDT", "").replace(",", "").strip()) if isinstance(funds, str) else funds
        # 檢查當前資金是否小於初始資金的指定百分比
        if current_funds < initial_funds * 0.05:
            message = "目前資金少於初始資金的指定百分比。跳過策略。"
            QMetaObject.invokeMethod(app, "operationMessageUpdated", Qt.QueuedConnection, Q_ARG(str, message))
            print(message)
            return  # 直接返回，不執行後續操作
        # 使用 Order_amount 函數計算需要交易的金額
        if strategy_type == "long":
            amount_to_trade, trade_type, message = order_trade(browser, float(BB_upside), float(BB_middle), float(BB_under), float(MA), float(initial_funds), float(current_price), float(first_price_history), 'long')
        elif strategy_type == "short":
            amount_to_trade, trade_type, message = order_trade(browser, float(BB_upside), float(BB_middle), float(BB_under), float(MA), float(initial_funds), float(current_price), float(first_price_history), 'short')
        elif strategy_type == "all":
            amount_to_trade, trade_type, message = order_trade(browser, float(BB_upside), float(BB_middle), float(BB_under), float(MA), float(initial_funds), float(current_price), float(first_price_history), 'all')
        else:
            print("策略類型無效")

        # 解析數據
        BB_upside, BB_middle, BB_under, MA, initial_funds, current_price,first_price_history,funds,strategy_type = data.values()

        # 確認解析後的參數
        print(f"BB_upside: {BB_upside}, BB_middle: {BB_middle}, BB_under: {BB_under}, MA: {MA}, 期初資金: {initial_funds}, 現價: {current_price}, 前三秒價格: {first_price_history}, 當前可用資金: {current_funds}, 當前選擇策略: {strategy_type}")

  
        print(amount_to_trade)
        if amount_to_trade in app.funds_ratio_list:
            # 調用set_values_in_webpage函數設置交易參數並執行交易
            amount_input_xpath = '//*[@id="__layout"]/div/div/div[3]/div/div/div[4]/div/div[2]/div[1]/div/div/div[2]/input'
            leverage_xpath = '//*[@id="__layout"]/div/div/div[3]/div/div/div[4]/div/div[2]/ul[3]/li[1]'
            takeProfit_xpath = '//*[@id="__layout"]/div/div/div[3]/div/div/div[4]/div/div[2]/li[2]/ul/div/span'
            takeProfit_input_xpath = '//*[@id="__layout"]/div/div/div[3]/div/div/div[4]/div/div[2]/li[2]/div[2]/div/div[2]/input'
            #trigger_takeprofit_xpath = '//*[@id="__layout"]/div/div/div[3]/div/div/div[4]/div/div[2]/li[2]/ul[2]/li[2]'
            stoploss_Xpath = '//*[@id="__layout"]/div/div/div[3]/div/div/div[4]/div/div[2]/li[3]/ul/div/span'
            trigger_stoploss_Xpath = '//*[@id="__layout"]/div/div/div[3]/div/div/div[4]/div/div[2]/li[3]/ul[2]/li[2]'
            confirm_button_xpath = '//*[@id="__layout"]/div/div/div[3]/div/div/div[4]/div/div[3]/div[2]/button'
            
            set_values_in_webpage(browser, selected_url, amount_to_trade, 
                                  leverage_xpath, takeProfit_xpath, takeProfit_input_xpath,
                                  stoploss_Xpath, trigger_stoploss_Xpath,confirm_button_xpath)
        
        else:
            print("計算出的交易金額不符合預設比例，跳過此次交易")

        # 使用 Qt 的信號發送操作消息
        QMetaObject.invokeMethod(app, "operationMessageUpdated", Qt.QueuedConnection, Q_ARG(str, message))
        
    except Exception as e:
        print(f"Error in main_priceVariable: {e}")