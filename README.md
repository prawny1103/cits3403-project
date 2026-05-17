# CITS3403 Group Project

### Description
A web application that allows users to create quizzes and play them with each other. Created by Adam Young (23817456, adsyoung), Darrell Ek (24849609, DarrellEk), Pranav Menon (24069351, prawny1103), and Rundong Wu (24441894, Russ0418)

### Usage:
Use the command `python run.py` in the project directory to launch the website. The command `flask run` will not work, as the project requires WebSockets. 

### Tests
All tests are managed by `pytest`.
*   **Run all tests:** `python -m pytest`
*   **Run only Unit Tests:** `python -m pytest tests/unit`
*   **Run only Selenium Tests:** `python -m pytest tests/selenium` 
    *(Note: These require a live server instance and the appropriate WebDriver installed)*.
*   **Run specific test:** `python -m pytest tests/unit/<filename>`
