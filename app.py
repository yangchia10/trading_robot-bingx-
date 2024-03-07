# 從其他腳本中導入必要的函數
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from priceVariable import main_priceVariable  # 這將是接受事件的更新後的 main_priceVariable

import threading
import time
import os
import sys
import subprocess
from PyQt5 import QtWidgets
from UI.bingx_Auto import Ui_BACKGROUND
from price_thread import PriceThread
from Funds_thread import FundsThread
from entrust_thread import entrustThread
from HOLD_thread import HOLDThread
from Trading_straregy import TradingStrategyThread

from run_commands import run_commands_from_file

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# 此事件在模塊之間共享，用於信號輸入正在進行中。
input_event = threading.Event()

class MainApp(QtWidgets.QMainWindow, Ui_BACKGROUND):
    priceUpdated = pyqtSignal(str)  # 確保這行在 __init__ 方法之前
    operationMessageUpdated = pyqtSignal(str)  # 新增一個信號用於操作消息的更新
    
    def __init__(self, browser):

        super().__init__()
        self.setupUi(self)

        # 連接信號到槽，用於更新價格
        self.priceUpdated.connect(self.NOW_PRICE.setText)
        # 創建為每個線程的事件
        self.price_event = threading.Event()
        self.funds_event = threading.Event()
        self.hold_event = threading.Event()
        self.trading_strategy_event = threading.Event()

        self.connect()      # 調用connect方法來設置連接
        self.browser = browser  # 保存傳遞的 browser 對象為類屬性
        self.funds_event = threading.Event()
        self.price_event = threading.Event()
        # 將VST的URL設為預設值
        self.selected_url = "https://bingx.com/zh-tw/futures/forward/BTCUSDT/?margin=VST&grants=0"
        #self.selected_url = None  # 初始化 selected_url 屬性
        self.funds_initialized = False  # 新增屬性，用於跟蹤是否已更新O_Asset
        self.price_thread = None  # 先定義self.price_thread
        self.initial_funds = None  # 新增屬性保存初始資金值

        self.price_history = []  # 用於存儲價格歷史數據

        # 數據就緒的同步對象
        self.data_ready_condition = threading.Condition()   

        # 初始化參數
        self.BB_upside = None
        self.BB_middle = None
        self.BB_under = None
        self.MA = None
        self.funds = None
        self.current_price = None

        # self.skip_fake_message = False  # 新增初始化skip_fake_message標志
        self.start_price_variable_timer()  # 原有的啟動真實消息定時器
        # self.start_fake_message_timer()  # 新增的啟動假消息定時器
        
        # 啟動定時器執行main_priceVariable
        self.start_price_variable_timer()
        self.operationMessageUpdated.connect(self.appendOperationMessage)  # 連接新信號到更新UI的槽

        self.funds_ratio_list = []  # 新增列表保存初始資金和比例計算值
        
        self.initial_funds_input_event = threading.Event()  #必須先輸入金額
        self.strategy_type_input_event = threading.Event()  #在輸入策略

        # Start a separate thread for getting initial funds
        threading.Thread(target=self.get_initial_funds).start()
        threading.Thread(target=self.get_strategy_type).start()

    def get_initial_funds(self):
        while True:
            try:
                initial_funds = float(input("請輸入期初資金: "))
                if initial_funds > 0:
                    break
                else:
                    print("請輸入一個大於0的數字")
            except ValueError:
                print("請輸入一個有效的數字")
        self.initial_funds = initial_funds
        self.funds_ratio_list = [self.initial_funds, self.initial_funds * 0.05, self.initial_funds * 0.03]
        self.initial_funds_input_event.set()  # 輸入後設定事件

    def get_strategy_type(self):
        while True:
            strategy_type = input("輸入策略類型 (long, short, all): ").lower()
            if strategy_type in ['long', 'short', 'all']:
                self.strategy_type = strategy_type
                break
            else:
                print("策略類型無效。 請輸入 long, short, all.")
        self.strategy_type_input_event.set()  # 輸入後設定事件


    def on_price_update(self, data):
        self.current_price = data["current_price"]
        self.price_history = data["price_history"]  # 確保這裏正確地更新了 price_history
        self.priceUpdated.emit(str(self.current_price))

    def appendOperationMessage(self, message):
        # 獲取當前文本並追加新消息
        current_text = self.SHOW.toPlainText()  # 假設 SHOW 是一個 QTextEdit，如果是 QLabel 使用 text()
        #current_text = self.SHOW.text()  # 對於 QLabel 使用 text() 方法獲取當前文本
        new_text = current_text + "\n" + message
        self.SHOW.setText(new_text)  # 更新文本內容

    def start_price_variable_timer(self):
        # 每三分鐘執行一次
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.execute_price_variable)
        # self.timer.start(120000)  # 120000毫秒 = 2分鐘
        self.timer.start(60000)  # 60000毫秒 = 1分鐘

    def check_data_ready(self):
        return (self.price_thread.data_ready and
                self.funds_thread.data_ready and
                self.trading_strategy_thread.data_ready)

    # 確保在關閉窗口時停止線程
    def closeEvent(self, event):
        if self.price_thread and self.price_thread.isRunning():
            self.price_thread.request_stop()
            self.price_thread.wait()

        if self.funds_thread and self.funds_thread.isRunning():
            self.funds_thread.request_stop()
            self.funds_thread.wait()

        if self.HOLD_thread and self.HOLD_thread.isRunning():
            self.HOLD_thread.request_stop()
            self.HOLD_thread.wait()

        if self.trading_strategy_thread and self.trading_strategy_thread.isRunning():
            self.trading_strategy_thread.stop()
            self.trading_strategy_thread.wait()

        super(MainApp, self).closeEvent(event)
    
        
    def start_crawler_threads(self):
        self.initial_funds_input_event.wait()  # 等待初始資金投入
        self.strategy_type_input_event.wait()  # 等待策略輸入
        
        if not self.price_thread or not self.price_thread.isRunning():
            self.price_thread = PriceThread(self.browser, input_event, self.selected_url, self.price_event)
            self.price_thread.price_signal.connect(self.updatePrice)
            self.price_thread.price_signal.connect(self.on_price_update)
            self.price_thread.start()
        else:
            self.price_thread.url_to_open = self.selected_url  # 動態更新URL
            self.price_thread.request_stop()
            self.price_thread.wait()  # 等待線程安全退出後重新啟動
            self.price_thread.start()

        # 初始化並啟動 FundsThread
        self.funds_thread = FundsThread(self.browser, input_event, self.funds_event, self.initial_funds)
        self.funds_thread.funds_signal.connect(self.updateFunds)
        self.funds_thread.start()

        # 初始化並啟動 entrustThread
        self.HOLD_thread = HOLDThread(self.browser, input_event, self.hold_event)
        self.HOLD_thread.HOLD_signal.connect(self.updateHOLD)
        self.HOLD_thread.start()

        # 這段代碼示例假設您已經有一個UI元件showWidget和一個tradingStrategyThread的實例
        # 確保 TradingStrategyThread 專註於 <iframe> 的數據抓取
        self.trading_strategy_thread = TradingStrategyThread(self.browser, self.trading_strategy_event)
        self.trading_strategy_thread.data_signal.connect(self.handle_bb_ma_data)  # 連接信號
        self.trading_strategy_thread.start()  # 啟動線程

    def updatePrice(self, data):
        # 從data中提取出來的當前價格
        current_price = data.get("current_price")
        price_history = data.get("price_history", [])
        self.price_history = price_history

        # 更新UI，確保這一步驟在主線程中執行
        # 註意：此處假設 self.NOW_PRICE 是在 UI 線程創建的 Qt Widget
        # 在工作線程中處理數據，然後發射信號更新 UI
        # history_text = "價格歷史: " + ", ".join(price_history)
        # self.appendOperationMessage(history_text)  # 假設這是將文本添加到UI組件的方法
        self.priceUpdated.emit(str(current_price))

        with self.data_ready_condition:
            self.current_price = current_price
            self.BB_upside = data.get("BB_upside")
            self.BB_middle = data.get("BB_middle")
            self.BB_under = data.get("BB_under")
            self.MA = data.get("MA")
            
            # 通知等待數據的線程
            self.data_ready_condition.notifyAll()

    def updateFunds(self, data):
        funds = data.get("funds", "N/A")
        print(f"當前可用資金: {funds}")  # Debugging
        self.funds = funds  # 更新 funds 屬性
        # 只在第一次接收到資金數據時更新O_Asset的文本
        if not self.funds_initialized:
            self.O_Asset.setText(f"{self.initial_funds} VST")  # Use the manually inputted initial funds
            self.funds_initialized = True  # Prevents reinitialization
            # self.initial_funds = funds  # 保存初始資金值
            # # 從字符串中提取數字並轉換為浮點數
            # self.initial_funds = float(funds.replace("VST", "").replace("USDT", "").replace(",", "").strip())
            # # 更新列表，包括初始資金、初始資金的0.05和0.03
            # self.funds_ratio_list = [self.initial_funds, self.initial_funds * 0.05, self.initial_funds * 0.03]
            # self.O_Asset.setText(funds)  # 更新資金顯示，只在第一次執行
            # # self.O_Asset.setText(f"{self.initial_funds} VST")
            # self.funds_initialized = True  # 更新標志，防止再次更新O_Asset
        self.ASSET.setText(funds)  # 更新資金顯示s


    def updateHOLD(self, HOLD):
        self.HOLD.setText(HOLD)  # 更新持有顯示

    def handle_bb_ma_data(self, data):
        # 嘗試解析並更新UI，如果數據無效則設置重試
        self.BB_upside = data.get("BB_upside")
        self.BB_middle = data.get("BB_middle")
        self.BB_under = data.get("BB_under")
        self.MA = data.get("MA")
         # 檢查是否可以執行交易邏輯
        self.execute_price_variable()
        self.trading_strategy_event.wait()
        self.trading_strategy_event.clear()  # 清除事件，為下一次抓取做準備

    def try_update_bb_ma_data(self, data, retry_count=0, max_retries=5):
        # 定義一個方法來嘗試解析數據並更新UI
        BB_middle = data.get("BB_middle", "N/A")
        BB_upside = data.get("BB_upside", "N/A")
        BB_under = data.get("BB_under", "N/A")
        MA = data.get("MA", "N/A")
        # 初始化display_text變量，以確保無論條件如何它都被定義
        display_text = "數據未就緒"

        # 檢查是否所有數據都是有效數字
        if all(x.replace('.', '', 1).isdigit() for x in [BB_middle, BB_upside, BB_under, MA] if x != "N/A"):
            display_text = f"BB Middle: {BB_middle}\nBB Upside: {BB_upside}\nBB Under: {BB_under}\nMA: {MA}"
            self.SHOW.setText(display_text)
        elif retry_count < max_retries:
            # 如果數據無效且重試次數未達上限，則使用QTimer稍後重試
            QTimer.singleShot(3000, lambda: self.try_update_bb_ma_data(data, retry_count+1, max_retries))  # 3秒後重試
        else:
            print("嘗試獲取有效數據失敗，已達最大重試次數。")

        # 更新UI中的顯示
        self.SHOW.setText(display_text)

    def execute_price_variable(self):
        # self.skip_fake_message = True  # 開始執行真實邏輯時跳過假消息

        with self.data_ready_condition:

        # 使用條件變量等待，直到所有數據都已更新，並設置超時避免無限等待
            data_ready = self.data_ready_condition.wait_for(lambda: all([
                self.BB_upside is not None, 
                self.BB_middle is not None, 
                self.BB_under is not None, 
                self.MA is not None, 
                self.funds is not None, 
                self.initial_funds is not None,
                self.current_price is not None, 
                self.price_history is not None, # 確保price_history非空
                self.strategy_type is not None
            ]), timeout=10)  # 設置10秒超時
            if not data_ready:
                print("等待更多價格歷史數據")
                return  # 如果數據未準備就緒，則直接返回不執行後續操作
        print(f"BB_upside: {self.BB_upside}, BB_middle: {self.BB_middle}, BB_under: {self.BB_under}, MA: {self.MA}, 當前可用資金: {self.funds}, 現價: {self.current_price}, price_history: {self.price_history}, 期初資金: {self.initial_funds}, 當前選擇策略: {self.strategy_type}")

            # 打印本次策略主要金額
        print(f"本次策略主要金額: {self.funds_ratio_list}")

        # 確保price_history至少有一個元素
        if self.price_history:
            first_price_history = self.price_history[0]  # 獲取列表中的第一個元素
        else:
            first_price_history = None  # 如果列表為空，則設置為None

        # first_price_history = self.price_history[0] if self.price_history else None  # 取第一個歷史價格
        # # 在所有數據都就緒後執行的邏輯
        data = {
            "BB_upside": self.BB_upside,
            "BB_middle": self.BB_middle,
            "BB_under": self.BB_under,
            "MA": self.MA,
            "initial_funds": self.initial_funds,  # 使用初始資金值
            "current_price": self.current_price,
            "first_price_history": first_price_history,  # 使用第一個歷史價格
            "funds":self.funds,
            "strategy_type":self.strategy_type
        }
        threading.Thread(target=main_priceVariable, args=(self.browser, self.selected_url, data, self, self.initial_funds)).start()

        # QTimer.singleShot(120000, self.reset_skip_fake_message)  # 2分鐘後重置標志

    def timetime(self):   #實時顯示時間
        while True:
            current_time = time.localtime()
            T = time.strftime("%Y-%m-%d %H:%M:%S", current_time)
            self.label_6.setText(T)
            time.sleep(1)  # 暫停 1 秒

    def showUseInfo(self):   #點擊出現使用說明
        dialog = QDialog()
        dialog.setWindowTitle("使用說明")
        dialog.setFixedSize(300, 600)
        label = QLabel("1 . 請先選擇幣別 "+"\n"+"2 . 點擊RUN開始執行")
        layout = QVBoxLayout()
        layout.addWidget(label)
        dialog.setLayout(layout)
        dialog.exec_()

    def comboaction(self):  # 點擊貨幣選擇
        print("Current index:", self.Choose_coin.currentIndex())
        self.update_url_based_on_selection()  # 更新URL基於選擇
        #self.confirm_selection_and_run()  # 確認選擇並根據新URL重新啟動爬蟲線程


    def update_url_based_on_selection(self):
        selected_index = self.Choose_coin.currentIndex()
        if selected_index == 0:
            self.selected_url = "https://bingx.com/zh-tw/futures/forward/BTCUSDT/?margin=USDT&grants=0"
            #self.SHOW.setText("USDT")
        elif selected_index == 1:
            self.selected_url = "https://bingx.com/zh-tw/futures/forward/BTCUSDT/?margin=VST&grants=0"
            #self.SHOW.setText("VST")
        else:
            print("未選擇有效的貨幣")
            self.selected_url = None

    def confirm_selection_and_run(self):  # 用戶確認選擇後執行
        if self.selected_url:
            # 重置funds_initialized標志，以便在新的URL初始化後可以更新資金數據
            self.funds_initialized = False
            
            # 更新PriceThread的URL
            if self.price_thread and self.price_thread.isRunning():
                self.price_thread.request_stop()
                self.price_thread.wait()  # 等待線程安全退出
                
            # 只有在這裏重新啟動爬蟲線程
            self.start_crawler_threads()
        
        # 控制 TradingStrategyThread 的啟動
            if hasattr(self, 'trading_strategy_thread') and self.trading_strategy_thread.isRunning():
                # 如果線程已經在運行，先停止它
                self.trading_strategy_thread.stop()
                self.trading_strategy_thread.wait()  # 等待線程安全退出

            # 創建新的 TradingStrategyThread 實例
            self.trading_strategy_thread = TradingStrategyThread(self.browser, self.trading_strategy_event)
            # 連接信號與槽，以便在數據更新時能夠更新UI
            self.trading_strategy_thread.data_signal.connect(self.handle_bb_ma_data)
            # 啟動線程
            self.trading_strategy_thread.start()

        else:
            print("請先選擇一個有效的貨幣")

    def connect(self):    #串接功能
        self.Choose_coin.addItems(["USDT","VST"])
        self.Choose_coin.currentIndexChanged.connect(self.comboaction)  # 連接選擇框的變化到 comboaction 方法
        self.RUN.clicked.connect(self.confirm_selection_and_run)# 確保RUN按鈕點擊時調用正確的方法
        QTimer.singleShot(0, self.start_crawler_threads)  # 延遲啟動線程以確保UI完全加載
        now_time = threading.Thread(target=self.timetime)
        now_time.start()
        self.USE_INFO.clicked.connect(self.showUseInfo)


    def run_scripts(self):
        # 在單獨的線程中啟動價格變量邏輯，傳遞事件
        print("等待10秒網頁loading")
        time.sleep(10)
        priceVariable_thread = threading.Thread(target=main_priceVariable, args=(self.browser,self.selected_url, input_event))
        priceVariable_thread.start()

        # 在啟動價格更新邏輯之前等待價格變量邏輯完成
        priceVariable_thread.join()
        
def main():

    # # 在創建UI之前運行 run_commands.py
    # subprocess.run(['python', 'run_commands.py'], check=True)
    # os.chdir(os.path.dirname(os.path.abspath(__file__)))
    # commands_file_path = 'commands.txt'
    if getattr(sys, 'frozen', False):
        # sys._MEIPASS 是 PyInstaller 為臨時文件創建的路徑
        application_path = sys._MEIPASS
    else:
        # 如果程序不是以單文件形式運行，使用當前腳本的路徑
        application_path = os.path.dirname(os.path.abspath(__file__))

    commands_file_path = os.path.join(application_path, 'commands.txt')

    # 檢查commands.txt是否存在於.exe文件所在的目錄
    if not os.path.exists(commands_file_path):
        print("找不到 commands.txt 文件。請確保它位於程序的同一目錄中。")
        return  # 或者您可以提供一個默認的 commands.txt 路徑或者創建一個新的文件

    run_commands_from_file(commands_file_path)

    # 設定webdriver選項
    options = Options()
    options.headless = True

    # 如果您沒有連接到現有的 Chrome 會話，應該刪除 debuggerAddress 選項。
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9527")

    # 創建webdriver實例
    browser = webdriver.Chrome(options=options)

    app = QtWidgets.QApplication(sys.argv)  # 創建應用程序實例
    main_window = MainApp(browser)  # 創建主窗口實例
    ui = Ui_BACKGROUND()
    main_window.show()  # 顯示窗口
    sys.exit(app.exec_()) 

if __name__ == "__main__":
    main()
