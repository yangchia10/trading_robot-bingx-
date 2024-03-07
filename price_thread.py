from PyQt5.QtCore import QThread, pyqtSignal
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
import time

class PriceThread(QThread):
    price_signal = pyqtSignal(dict)  # 用於發送價格信息的信號

    def __init__(self, browser, input_event, url, price_event):
        super().__init__()
        self.browser = browser
        self.input_event = input_event
        self.url_to_open = url
        self.initialize_browser()
        self.stop_requested = False
        self.price_event = price_event
        self.price_history = []  # 保存最近三個價格

    def request_stop(self):
        self.stop_requested = True

    def initialize_browser(self):
        # 初始化瀏覽器設置
        close_button_selector = 'i.ic-close'
        fifteen_minutes_xpath = '//*[@id="__layout"]/div/div/div[3]/div/div/div[2]/div/div/div[1]/div[1]/div[3]'
        
        
        try:
            self.browser.get(self.url_to_open)
            WebDriverWait(self.browser, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, close_button_selector))).click()
            print("Popup closed.")
            WebDriverWait(self.browser, 10).until(
                EC.element_to_be_clickable((By.XPATH, fifteen_minutes_xpath))).click()
            print("15分鐘間隔選擇成功。")
        except TimeoutException:
            print("未找到彈出窗口或無法單擊。")

    def run(self):
        price_selector = '.price .btn span'
        while not self.stop_requested:
            if not self.input_event.is_set():
                try:
                    price_element = self.browser.find_element(By.CSS_SELECTOR, price_selector)
                    current_price = price_element.text.strip()
                    # 更新價格歷史列表，保持長度為3
                    if len(self.price_history) >= 3:
                        self.price_history.pop(0)
                    self.price_history.append(current_price)
                    
                    # 僅當有3個價格數據時，才發送信號
                    if len(self.price_history) == 3:
                        data = {
                            "current_price": current_price,
                            "price_history": self.price_history.copy()  # 使用 copy() 確保傳遞的是當前狀態的副本
                            # [self.price_history[1]]  # 只傳遞第一個和最後一個價格數據
                        }
                        self.price_signal.emit(data)
                        self.price_event.set()
                except Exception as e:
                    print(f"\nAn error occurred: {e}")
            time.sleep(1)

            if self.stop_requested:
                print("PriceThread is stopping.")
                break

