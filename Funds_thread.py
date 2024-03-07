from PyQt5.QtCore import QThread, pyqtSignal
from selenium.webdriver.common.by import By
import time

def get_current_funds(browser, funds_xpath):
    """
    從網頁中抓取當前資金數據。
    """
    try:
        funds_element = browser.find_element(By.XPATH, funds_xpath)
        funds_text = funds_element.text.strip()
        # # 只提取數字部分
        # funds_amount = funds_text.split(' ')[0]
        # 如果文本中包含“可用”，則去除它
        funds_amount = funds_text.replace("可用", "").strip()
        # 返回完整的文本（包括 'VST'）
        return funds_amount
    except Exception as e:
        print(f"Error in getting funds: {e}")
        return None

class FundsThread(QThread):
    funds_signal = pyqtSignal(dict)  # 用於發送資金信息的信號

    def __init__(self, browser, input_event, funds_event, initial_funds):
        super().__init__()
        self.browser = browser
        self.input_event = input_event
        self.funds_event = funds_event  # 接收事件對象
        self.initial_funds = initial_funds  # 儲存初始資金
        self.last_funds = None

    def run(self):
        funds_xpath = '//*[@id="__layout"]/div/div/div[3]/div/div/div[4]/div/div[2]/li[1]/span/span[2]'
        alternate_xpath = '//*[@id="__layout"]/div/div/div[3]/div/div/div[4]/div/div[2]/li[1]/span'

        while True:
            if not self.input_event.is_set():
                current_funds = get_current_funds(self.browser, funds_xpath)
                if current_funds and current_funds != self.last_funds:
                    self.data_ready = True
                    # self.funds_signal.emit({"funds": current_funds})
                    self.funds_signal.emit({"funds": current_funds, "initial_funds": self.initial_funds})
                    self.funds_event.set()  # 數據抓取完成，設置事件
                    self.last_funds = current_funds
                else:
                    self.data_ready = False

            time.sleep(1)  # 每秒檢查一次
        
