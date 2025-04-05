#html_extraction.py
import os
import random
import time
import sqlite3
import sys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from functions.human_mimic import human_sleep, human_scroll, random_hover

class HTMLExtraction:
    def __init__(self, driver, db_path="data/linkedin_profiles.db", cache_dir="data/html_cache"):
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        self.driver = driver
        self.db_path = os.path.abspath(os.path.join(base_path, "..", db_path))
        self.cache_dir = os.path.abspath(os.path.join(base_path, "..", cache_dir))
        os.makedirs(self.cache_dir, exist_ok=True)

        self.pause_after_n = random.randint(10, 20)
        self.processed_count = 0

        print(f"[DEBUG] DB path: {self.db_path}")
        print(f"[DEBUG] Cache folder: {self.cache_dir}")

    def take_linkedin_detour(self):
        destinations = [
            ("https://www.linkedin.com/feed/", "Feed"),
            ("https://www.linkedin.com/mynetwork/", "My Network"),
            ("https://www.linkedin.com/jobs/", "Jobs"),
            ("https://www.linkedin.com/notifications/", "Notifications"),
        ]
        url, label = random.choice(destinations)

        print(f"\n[Detour] Visiting {label} page...")
        self.driver.get(url)
        human_sleep(3.5, 1.5)

        human_scroll(self.driver, total_scrolls=random.randint(2, 4))
        random_hover(self.driver, "a")
        human_sleep(1.5, 0.7)

    def load_profiles(self):
        conn = sqlite3.connect(self.db_path)
        df = None
        try:
            df = conn.execute("SELECT profile_id, profile_url FROM profiles ORDER BY profile_id ASC").fetchall()
        finally:
            conn.close()
        return df

    def save_profile_html(self, profile_id, url):
        filename = f"profile_{profile_id}.html"
        filepath = os.path.join(self.cache_dir, filename)

        if os.path.exists(filepath):
            print(f"[{profile_id}] Skipped — already saved.")
            return False

        print(f"[{profile_id}] Visiting: {url}")
        try:
            self.driver.get(url)

            human_sleep(3, 1.5)
            human_scroll(self.driver, total_scrolls=random.randint(2, 4))
            random_hover(self.driver, "section")

            html = self.driver.page_source
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"[{profile_id}] Saved.")
            return True

        except Exception as e:
            print(f"[{profile_id}] Error: {e}")
            return False

        finally:
            self.processed_count += 1

            if random.random() < 0.25:
                self.take_linkedin_detour()

            if self.processed_count >= self.pause_after_n:
                long_break = random.uniform(10, 30)
                print(f"\n--- Long break: {long_break:.1f} seconds ---\n")
                time.sleep(long_break)
                self.processed_count = 0
                self.pause_after_n = random.randint(10, 20)

    def run(self, max_profiles=None):
        profiles = self.load_profiles()
        print(f"\nLoaded {len(profiles)} profiles from database.\n")

        saved = 0
        for profile_id, url in profiles:
            was_saved = self.save_profile_html(profile_id, url)
            if was_saved:
                saved += 1
                if max_profiles is not None and saved >= max_profiles:
                    print(f"\n[INFO] Reached max of {max_profiles} new profiles. Stopping.\n")
                    break

        print(f"\n[SUCCESS] HTML extraction complete. {saved} new profiles saved.\n")
        print(f"[INFO] Processed {self.processed_count} profiles in total.\n")
        print(f"[INFO] All HTML files saved in: {self.cache_dir}\n")