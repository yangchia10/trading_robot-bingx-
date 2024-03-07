from PyQt5.QtCore import QThread, pyqtSignal
from selenium.webdriver.common.by import By
import time

def get_current_HOLD(browser, HOLD_xpath):
    """
    從網頁中抓取當前資金數據。
    """
    try:
        HOLD_element = browser.find_element(By.XPATH, HOLD_xpath)
        HOLD_text = HOLD_element.text.strip()
        # 只提取數字部分
        HOLD_amount = HOLD_text.split(' ')[0]
        return HOLD_amount
    except Exception as e:
        print(f"Error in getting HOLD: {e}")
        return None

class HOLDThread(QThread):
    """
    一個 QThread 子類，用於定期檢查資金數據的變化。
    """
    HOLD_signal = pyqtSignal(str)  # 用於發送資金信息的信號

    def __init__(self, browser, input_event, hold_event):
        super().__init__()
        self.browser = browser
        self.input_event = input_event
        self.hold_event = hold_event  # 新增屬性來接收事件對象
        self.last_HOLD = None

    def run(self):
        HOLD_xpath = '//*[@id="__layout"]/div/div/div[3]/div/div/div[5]/div/div[1]/div[2]/ul/li[1]/div[1]'
        
        while True:
            if not self.input_event.is_set():
                current_HOLD = get_current_HOLD(self.browser, HOLD_xpath)
                if current_HOLD != self.last_HOLD:
                    
                    self.HOLD_signal.emit(str(current_HOLD))
                    self.hold_event.set()  # 數據抓取完成，設置事件
                    self.last_HOLD = current_HOLD
            time.sleep(1)  # 每秒檢查一次
