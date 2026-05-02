from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

# 1. 이미 열려 있는 디버깅 브라우저에 연결 설정
chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

# 2. 드라이버 실행 (새 창이 뜨지 않고 기존 창을 제어함)
driver = webdriver.Chrome(options=chrome_options)

try:
    # 3. 계좌 페이지로 이동
    driver.get("https://www.tossinvest.com/account")
    time.sleep(3) # 페이지 로딩 대기

    # 4. 데이터 가져오기 (예: 전체 페이지 텍스트 출력)
    # 토스증권은 보안상 요소 찾기가 까다로울 수 있어 우선 전체 내용을 가져와 봅니다.
    account_info = driver.find_element(By.TAG_NAME, "body").text
    print("--- 수집된 계좌 정보 요약 ---")
    print(account_info)
    
    # 특정 요소를 찾고 싶다면 개발자 도구(F12)로 Selector를 확인해야 합니다.

except Exception as e:
    print(f"에러 발생: {e}")

# driver.quit()을 하지 않으면 브라우저가 닫히지 않고 유지됩니다.