from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Testing the flow of events. When a user signs up with valid credentials, they should be redirected to the homepage. 
def test_registration_to_home_flow(driver, live_server):
    # Navigate to the signup page
    driver.get(f"{live_server}/register")
    
    # Find the form elements using IDs from signup.html
    username_input = driver.find_element(By.ID, "signup-username")
    password_input = driver.find_element(By.ID, "signup-password")
    confirm_input = driver.find_element(By.ID, "signup-password-confirm")
    submit_button = driver.find_element(By.ID, "signup-button")
    
    # Fill out the form
    test_username = "AgileUser1"
    username_input.send_keys(test_username)
    password_input.send_keys("Password123")
    confirm_input.send_keys("Password123")
    
    # Submit the form
    submit_button.click()
    
    # Wait for redirection and verify the username appears in the header
    wait = WebDriverWait(driver, 10)
    
    # Verify we are on the home page
    wait.until(EC.presence_of_element_located((By.ID, "landing-page-main")))
    
    # Check if the username is displayed in the nav bar as per index.html
    username_display = driver.find_element(By.CLASS_NAME, "login-nav-authenticated-username")
    assert test_username in username_display.text
    
    # Verify the "Log Out" link is now visible
    logout_link = driver.find_element(By.CLASS_NAME, "login-nav-authenticated-logout")
    assert logout_link.is_displayed()

# Test registration with invalid credentials. User should receive an error. 
def test_registration_failure_password_mismatch(driver, live_server):
    driver.get(f"{live_server}/register")
    
    driver.find_element(By.ID, "signup-username").send_keys("FailUser")
    driver.find_element(By.ID, "signup-password").send_keys("Password123")
    driver.find_element(By.ID, "signup-password-confirm").send_keys("WrongPassword")
    driver.find_element(By.ID, "signup-button").click()
    
    # Wait for the flash message area
    wait = WebDriverWait(driver, 5)
    flash_message = wait.until(EC.presence_of_element_located((By.ID, "signup-flash")))
    
    assert "Passwords do not match" in flash_message.text

# Ensure logged out users aren't allowed to view protected pages
def test_unauthorized_redirect(driver, live_server):
    driver.delete_all_cookies()
    driver.get(f"{live_server}/createRoom")
    
    assert "/login" in driver.current_url
    assert "Please enter your details" in driver.page_source
