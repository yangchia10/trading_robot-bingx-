from PyQt5.QtCore import QThread, pyqtSignal
from selenium.webdriver.common.by import By
import time


class BBMAThread(QThread):
    bb_ma_signal = pyqtSignal(dict)  # 發送BB和MA信息的信號

    def __init__(self, browser):
        super().__init__()
        self.browser = browser
def get_current_entrust(browser, entrust_xpath):
    """
    從網頁中抓取當前資金數據。
    """
    try:
        entrust_element = browser.find_element(By.XPATH, entrust_xpath)
        entrust_text = entrust_element.text.strip()
        # 只提取數字部分
        entrust_amount = entrust_text.split(' ')[0]
        return entrust_amount
    except Exception as e:
        print(f"Error in getting entrust: {e}")
        return None

class entrustThread(QThread):
    """
    一個 QThread 子類，用於定期檢查資金數據的變化。
    """
    entrust_signal = pyqtSignal(str)  # 用於發送資金信息的信號

    def __init__(self, browser, input_event):
        super().__init__()
        self.browser = browser
        self.input_event = input_event
        self.last_entrust = None

    def run(self):
        entrust_xpath = '//*[@id="__layout"]/div/div/div[3]/div/div/div[5]/div/div[1]/div[2]/ul/li[2]/div[1]'
        
        while True:
            if not self.input_event.is_set():
                current_entrust = get_current_entrust(self.browser, entrust_xpath)
                if current_entrust != self.last_entrust:
                    print("Current entrust received:", current_entrust)
                    self.entrust_signal.emit(str(current_entrust))
                    self.last_entrust = current_entrust
            time.sleep(1)  # 每秒檢查一次
