from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# When the room creation form is filled, a room should be created, and the user redirected to the game lobby
def test_create_room_flow(driver, live_server):
    wait = WebDriverWait(driver, 15)

    driver.get(f"{live_server}/login")
    wait.until(EC.presence_of_element_located((By.ID, "login-username"))).send_keys("tester")
    driver.find_element(By.ID, "login-password").send_keys("Password123")
    driver.find_element(By.ID, "login-button").click()

    wait.until(EC.presence_of_element_located((By.ID, "landing-page-main")))

    driver.get(f"{live_server}/createRoom")

    # Wait for the Create Room page to actually load
    q_count_select = wait.until(EC.presence_of_element_located((By.ID, "question-count")))
    q_count_select.send_keys("10")

    difficulty_select = driver.find_element(By.ID, "difficulty")
    difficulty_select.send_keys("medium")

    timer_30 = driver.find_element(By.ID, "t30")
    driver.execute_script("arguments[0].click();", timer_30)

    submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    submit_btn.click()

    wait = WebDriverWait(driver, 20) 
    wait.until(EC.presence_of_element_located((By.ID, "lobby-screen")))

    # Verify room code is displayed
    room_code_display = driver.find_element(By.ID, "display-code")
    room_code = room_code_display.text
    
    assert len(room_code) == 4
    assert room_code.isdigit()

# If a user tries to create a room without an account, they should see an alert or be redirected to login
def test_create_room_requires_login(driver, live_server):
    # Clear cookies to ensure logged out
    driver.delete_all_cookies()
    driver.get(f"{live_server}/createRoom")
    
    # Check if we were redirected to login
    assert "/login" in driver.current_url
