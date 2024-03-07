from PyQt5.QtCore import QThread, pyqtSignal
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class TradingStrategyThread(QThread):
    data_signal = pyqtSignal(dict)  # 修改為發送字典

    def __init__(self, browser, trading_strategy_event):
        super().__init__()
        self.browser = browser
        self.trading_strategy_event = trading_strategy_event  # 新增事件屬性
        self.is_running = True
        self.data_ready = False  # 新增數據就緒屬性

    def run(self):
        while self.is_running:
            try:
                self.fetch_data()
                self.data_ready = True  # 數據獲取成功
                self.trading_strategy_event.set()  # 數據抓取完成，設置事件
                time.sleep(60)  # 等待180秒或3分鐘後再次嘗試獲取數據
            except Exception as e:
                print(f"TradingStrategyThread 運行錯誤: {e}")
                self.data_ready = False  # 數據獲取失敗
                time.sleep(3)  # 等待一段時間後重試
                

    def fetch_data(self):
        iframe_title_xpath = "//iframe[@title='Financial Chart']"
        iframe = WebDriverWait(self.browser, 15).until(
            EC.presence_of_element_located((By.XPATH, iframe_title_xpath))
        )
        print("切換到iframe")
        self.browser.switch_to.frame(iframe)

        # 定義元素的XPath路徑
        elements_xpaths = {
                    "BB_middle": "/html/body/div[2]/div[3]/div[2]/div[1]/div[2]/table/tr[1]/td[2]/div/div[2]/div[2]/div[2]/div[2]/div[2]/div/div[1]/div",
                    "BB_upside": "/html/body/div[2]/div[3]/div[2]/div[1]/div[2]/table/tr[1]/td[2]/div/div[2]/div[2]/div[2]/div[2]/div[2]/div/div[2]/div",
                    "BB_under": "/html/body/div[2]/div[3]/div[2]/div[1]/div[2]/table/tr[1]/td[2]/div/div[2]/div[2]/div[2]/div[2]/div[2]/div/div[3]/div",
                    "MA": "/html/body/div[2]/div[3]/div[2]/div[1]/div[2]/table/tr[1]/td[2]/div/div[2]/div[2]/div[2]/div[3]/div[2]/div/div[1]/div"
                }

        data = {}
        for name, xpath in elements_xpaths.items():
            element = WebDriverWait(self.browser, 15).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            data[name] = element.text.strip()

        print(f"抓取到的{name}數據為：{data[name]}")
        self.browser.switch_to.default_content()
        print("切換回主內容")
        self.data_signal.emit(data)
        #self.trading_strategy_event.set()  # 數據抓取完成，設置事件


    def stop(self):
        self.is_running = False
