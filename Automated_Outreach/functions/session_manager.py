# session_manager.py

import os
import time
import random
import pickle
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from functions.human_mimic import human_sleep, human_scroll, random_hover

class SessionManager:
    def __init__(self, cookie_path="your_cookies.pkl", use_user_profile=False, user_profile_path=None):
        self.cookie_path = cookie_path
        self.use_user_profile = use_user_profile
        self.user_profile_path = user_profile_path
        self.driver = self._init_driver()

    def _init_driver(self):
        chromedriver_autoinstaller.install()
        options = Options()
        options.add_argument("--user-agent=Mozilla/5.0")

        if self.use_user_profile:
            if self.user_profile_path:
                options.add_argument(f"--user-data-dir={self.user_profile_path}")
                print(f"[i] Using custom user profile: {self.user_profile_path}")
            else:
                print("[i] User profile flag is on but no path specified.")

        return webdriver.Chrome(options=options)

    def _human_mimic(self):
        human_scroll(self.driver, total_scrolls=5)
        random_hover(self.driver)
        human_sleep(2, 0.5)

    def _save_cookies(self):
        with open(self.cookie_path, "wb") as f:
            pickle.dump(self.driver.get_cookies(), f)
        print(f"[SUCCESS] Cookies saved to {self.cookie_path}")

    def _load_cookies(self):
        with open(self.cookie_path, "rb") as f:
            cookies = pickle.load(f)
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception:
                    pass

    def login(self):
        self.driver.get("https://www.linkedin.com")
        time.sleep(3)

        if os.path.exists(self.cookie_path):
            self._load_cookies()
            self.driver.get("https://www.linkedin.com/feed/")
            time.sleep(3)

            if "feed" in self.driver.current_url:
                print("[SUCCESS] Logged in using saved cookies.")
                self._human_mimic()
                return self.driver
            else:
                print("[ERROR] Saved cookies invalid or expired.")
        
        print("Manual login required.")
        print("Please login in the Chrome window. Waiting...")

        self.driver.get("https://www.linkedin.com/login")
        input("Press [ENTER] after you've logged in...")

        if "feed" in self.driver.current_url:
            self._save_cookies()
            self._human_mimic()
        else:
            print("[ERROR] Login failed. Please try again.")

        return self.driver
