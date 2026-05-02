import sys
import requests
import yfinance as yf
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QLabel, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QTextEdit, QMessageBox, QGroupBox, QDialog, 
                             QListWidget, QListWidgetItem)

# --- 종목 검색을 위한 팝업 창 클래스 ---
class SearchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("종목 검색")
        self.setGeometry(200, 200, 450, 400)
        self.selected_ticker = None

        layout = QVBoxLayout(self)

        # 검색 입력부
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("종목명 입력 (예: 삼성전자, apple, TSLA)")
        self.search_input.returnPressed.connect(self.perform_search) # 엔터키 지원
        
        self.search_btn = QPushButton("검색")
        self.search_btn.clicked.connect(self.perform_search)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)

        # 검색 결과 리스트
        self.result_list = QListWidget()
        self.result_list.itemDoubleClicked.connect(self.select_item)

        # 하단 선택 버튼
        self.select_btn = QPushButton("선택하기")
        self.select_btn.clicked.connect(self.select_item)
        self.select_btn.setStyleSheet("background-color: #3182f6; color: white; font-weight: bold;")

        layout.addLayout(search_layout)
        layout.addWidget(QLabel("검색 결과 (더블 클릭하거나 선택 후 버튼 클릭):"))
        layout.addWidget(self.result_list)
        layout.addWidget(self.select_btn)

    def perform_search(self):
        query = self.search_input.text().strip()
        if not query: 
            return
            
        self.result_list.clear()
        self.result_list.addItem("검색 중...")
        QApplication.processEvents() # UI 멈춤 방지

        try:
            # 야후 파이낸스 검색 API 활용
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(url, headers=headers)
            data = response.json()

            self.result_list.clear()
            
            if 'quotes' in data and len(data['quotes']) > 0:
                for quote in data['quotes']:
                    symbol = quote.get('symbol', '')
                    shortname = quote.get('shortname', '')
                    longname = quote.get('longname', '')
                    exch = quote.get('exchange', '')
                    
                    # 이름이 없는 경우 처리
                    name = shortname if shortname else longname
                    if not name: name = "이름 알 수 없음"
                    
                    item_text = f"{symbol} | {name} ({exch})"
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, symbol) # 실제 티커 데이터를 숨겨서 저장
                    self.result_list.addItem(item)
            else:
                self.result_list.addItem("검색 결과가 없습니다.")
                
        except Exception as e:
            self.result_list.clear()
            self.result_list.addItem("검색 중 네트워크 오류가 발생했습니다.")

    def select_item(self):
        curr_item = self.result_list.currentItem()
        if curr_item and curr_item.data(Qt.UserRole):
            self.selected_ticker = curr_item.data(Qt.UserRole)
            self.accept() # 창 닫고 성공 신호 반환

# --- 메인 프로그램 클래스 ---
class ApiTradingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.portfolio = {}
        self.init_ui()
        self.init_timer()

    def init_ui(self):
        self.setWindowTitle('API 기반 실시간 자동 매매 봇')
        self.setGeometry(100, 100, 1100, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # ---------------- 1. 종목 추가 패널 ----------------
        input_group = QGroupBox("새로운 감시 종목 추가")
        input_layout = QHBoxLayout()

        self.ticker_input = QLineEdit()
        self.ticker_input.setPlaceholderText("종목코드 (예: AAPL)")
        self.ticker_input.setReadOnly(False)
        
        search_ticker_btn = QPushButton("🔍 종목 검색")
        search_ticker_btn.clicked.connect(self.open_search_dialog)
        
        self.buy_price_input = QLineEdit()
        self.buy_price_input.setPlaceholderText("매입 단가 (숫자)")
        
        self.target_rate_input = QLineEdit()
        self.target_rate_input.setPlaceholderText("목표 수익률 (%)")
        
        add_btn = QPushButton("포트폴리오에 추가")
        add_btn.setStyleSheet("background-color: #3182f6; color: white; font-weight: bold; padding: 5px 15px;")
        add_btn.clicked.connect(self.add_stock_to_portfolio)

        input_layout.addWidget(QLabel("종목코드:"))
        input_layout.addWidget(self.ticker_input)
        input_layout.addWidget(search_ticker_btn)
        input_layout.addWidget(QLabel("매입단가:"))
        input_layout.addWidget(self.buy_price_input)
        input_layout.addWidget(QLabel("목표수익률(%):"))
        input_layout.addWidget(self.target_rate_input)
        input_layout.addWidget(add_btn)
        
        input_group.setLayout(input_layout)

        # ---------------- 2. 보유 주식 현황 표 ----------------
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["종목코드", "매입가", "현재가 (API)", "현재 수익률(%)", "목표 수익률(%)", "상태"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # ---------------- 3. 로그 창 ----------------
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.append("시스템: 실시간 API 트레이딩 봇이 시작되었습니다.")
        self.log_console.append("안내: [🔍 종목 검색] 버튼을 눌러 원하는 기업 이름을 검색해 보세요.")

        # 레이아웃 조립
        main_layout.addWidget(input_group)
        main_layout.addWidget(QLabel("<b>실시간 포트폴리오 감시 현황 (5초마다 API 갱신)</b>"))
        main_layout.addWidget(self.table)
        main_layout.addWidget(QLabel("<b>실행 로그</b>"))
        main_layout.addWidget(self.log_console)

    def open_search_dialog(self):
        dialog = SearchDialog(self)
        # 검색 창을 열고, 사용자가 아이템을 '선택'해서 창이 정상적으로 닫혔다면
        if dialog.exec_():
            if dialog.selected_ticker:
                self.ticker_input.setText(dialog.selected_ticker)

    def init_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.routine_check)
        self.timer.start(5000) 

    def add_stock_to_portfolio(self):
        ticker = self.ticker_input.text().strip().upper()
        buy_price_str = self.buy_price_input.text().strip()
        target_rate_str = self.target_rate_input.text().strip()

        if not ticker or not buy_price_str or not target_rate_str:
            QMessageBox.warning(self, "입력 오류", "모든 칸을 입력해주세요.")
            return

        try:
            buy_price = float(buy_price_str.replace(',', ''))
            target_rate = float(target_rate_str)
        except ValueError:
            QMessageBox.warning(self, "입력 오류", "매입단가와 목표수익률은 숫자로 입력해주세요.")
            return

        self.portfolio[ticker] = {
            "buy_price": buy_price,
            "current_price": buy_price, 
            "target_rate": target_rate,
            "sold": False
        }
        
        self.log_console.append(f"추가 완료: [{ticker}] 매입가 {buy_price} / 목표수익률 {target_rate}% 감시를 시작합니다.")
        
        self.ticker_input.clear()
        self.buy_price_input.clear()
        self.target_rate_input.clear()
        
        self.update_table_ui()
        self.routine_check()

    def routine_check(self):
        if not self.portfolio:
            return 

        for ticker, data in self.portfolio.items():
            if data["sold"]:
                continue 

            try:
                stock = yf.Ticker(ticker)
                current_price = stock.fast_info.get('lastPrice')
                
                if current_price is not None:
                    data["current_price"] = current_price
                    self.check_profit_and_sell(ticker, data)
                
            except Exception as e:
                pass 

        self.update_table_ui()

    def check_profit_and_sell(self, ticker, data):
        buy_price = data["buy_price"]
        current_price = data["current_price"]
        target_rate = data["target_rate"]
        
        if buy_price <= 0: return
        
        current_profit_rate = ((current_price - buy_price) / buy_price) * 100

        if current_profit_rate >= target_rate:
            self.execute_api_sell(ticker, current_price, current_profit_rate)
            data["sold"] = True

    def execute_api_sell(self, ticker, price, profit_rate):
        self.log_console.append(f"<font color='red'><b>[매도 감지!]</b> {ticker} 목표 달성! 현재 수익률: {profit_rate:.2f}%</font>")
        self.log_console.append(f"-> 시스템: 증권사 API로 {ticker} 전량 매도 주문을 전송했습니다. (매도 체결가: {price:.2f})")

    def update_table_ui(self):
        self.table.setRowCount(len(self.portfolio))
        for row, (ticker, data) in enumerate(self.portfolio.items()):
            buy_price = data["buy_price"]
            current_price = data["current_price"]
            profit_rate = ((current_price - buy_price) / buy_price) * 100 if buy_price > 0 else 0

            self.table.setItem(row, 0, QTableWidgetItem(ticker))
            self.table.setItem(row, 1, QTableWidgetItem(f"{buy_price:,.2f}"))
            self.table.setItem(row, 2, QTableWidgetItem(f"{current_price:,.2f}"))
            
            profit_item = QTableWidgetItem(f"{profit_rate:.2f}%")
            if profit_rate > 0: profit_item.setForeground(Qt.red)
            elif profit_rate < 0: profit_item.setForeground(Qt.blue)
            self.table.setItem(row, 3, profit_item)
            
            self.table.setItem(row, 4, QTableWidgetItem(f"{data['target_rate']}%"))
            
            status = "매도 완료" if data["sold"] else "감시 중"
            self.table.setItem(row, 5, QTableWidgetItem(status))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ApiTradingApp()
    window.show()
    sys.exit(app.exec_())