from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import random
import sqlite3
import os
from functions.human_mimic import human_sleep, random_hover

class ShallowScraper:
    def __init__(self, driver):
        self.driver = driver
        self.people = []
        self.seen_urls = set()
        self.original_window_size = self.driver.get_window_size()  # Save original size

    # Temporarily resize the window for scraping
    def temporarily_resize_window(self, width=1280, height=900):
        self.driver.set_window_size(width, height)
        human_sleep(1, 0.5)  # Optional: give the page a moment to adjust

    # Reset to the original window size
    def reset_window_size(self):
        self.driver.set_window_size(self.original_window_size['width'], self.original_window_size['height'])
        human_sleep(1, 0.5)  # Optional: adjust with a short sleep to ensure smooth transition

    def wait_and_open_target_tab(self, target_label, max_retries=10, scroll_loops=8):
        print(f"Trying to open 'People you may know from {target_label}' tab")

        for attempt in range(max_retries):
            print(f"[{attempt + 1}/{max_retries}] Searching...")

            self.driver.get("https://www.linkedin.com/mynetwork/")
            human_sleep(5, 2)
            random_hover(self.driver, "a")

            # Temporarily resize window for scraping
            self.temporarily_resize_window()

            # Trigger modal to load
            self.driver.execute_script("window.scrollBy(0, 500);")
            human_sleep(1.5, 0.5)
            self.driver.execute_script("""
                const evt = new WheelEvent('wheel', {
                    deltaY: 100,
                    bubbles: true,
                    cancelable: true
                });
                document.dispatchEvent(evt);
            """)
            human_sleep(1.5, 0.5)

            for scroll in range(scroll_loops):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                print(f"    Full-page scroll {scroll + 1}/{scroll_loops}")
                human_sleep(2, 1.5)

                if scroll in {2, 5} and random.random() < 0.4:
                    print("   ...pausing to simulate reading")
                    human_sleep(3, 1)

            try:
                show_all_btn = self.driver.find_element(
                    By.XPATH,
                    f"//button[@aria-label='Show all suggestions for People you may know from {target_label}']"
                )
                self.driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth' });", show_all_btn)
                human_sleep(2, 1)

                ActionChains(self.driver).move_to_element(show_all_btn).perform()
                human_sleep(1.5, 0.5)

                self.driver.execute_script("arguments[0].click();", show_all_btn)
                print(f"Opened suggestions for: {target_label}")
                
                # Reset the window size after actions
                self.reset_window_size()

                return True

            except Exception:
                print("Did not find the tab this time.")
                if random.random() < 0.4:
                    self.driver.get("https://www.linkedin.com/feed/")
                    print("Went back to feed to reset.")
                else:
                    print("Retrying directly from My Network...")
                human_sleep(5, 2)

        print("Gave up after too many attempts, are you sure you entered in the section name EXACTLY AS IT'S WRITTEN?.")
        return False

    def scroll_and_extract_profiles(self, pause_range=(2.5, 4.0), streak_limit=5, scrolls_per_loop=10, scroll_factor=1.8, max_profiles=100):
        streak = 0
        loop = 0

        def get_scroll_container(timeout=10):
            try:
                return WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#root > dialog > div > div:nth-child(2)"))
                )
            except Exception:
                return None

        def extract_new_people():
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            cards = soup.find_all("a", href=True)
            new_count = 0

            for card in cards:
                href = card['href']
                if not href.startswith("https://www.linkedin.com/in/"):
                    continue
                if href in self.seen_urls:
                    continue

                try:
                    paragraphs = card.find_all("p")
                    if len(paragraphs) < 2:
                        continue

                    name = paragraphs[0].get_text(strip=True)
                    headline = paragraphs[1].get_text(strip=True)

                    self.people.append({
                        "name": name,
                        "headline": headline,
                        "profile_url": href
                    })
                    self.seen_urls.add(href)
                    new_count += 1

                    if max_profiles is not None and len(self.seen_urls) >= max_profiles:
                        break

                except Exception as e:
                    print("   Error parsing card:", e)
                    continue

            return new_count

        print("\nStarting deep scroll & extract...\n")

        while True:
            loop += 1
            print(f"Loop {loop}")

            new_profiles = extract_new_people()
            print(f"   New: {new_profiles} | Total collected: {len(self.seen_urls)}")

            if max_profiles is not None and len(self.seen_urls) >= max_profiles:
                print(f"Reached max scrape limit ({max_profiles}). Stopping.")
                break

            if new_profiles == 0:
                streak += 1
                print(f"   No new profiles ({streak}/{streak_limit})")
                if streak >= streak_limit:
                    print("Too many empty scrolls. Ending loop.")
                    break
            else:
                streak = 0

            scroll_container = get_scroll_container()
            if scroll_container and scroll_container.size['height'] > 0:
                print("Using modal container for scrolling.")
                try:
                    for s in range(scrolls_per_loop):
                        scroll_step = scroll_factor + random.uniform(-0.3, 0.3)
                        self.driver.execute_script("""
                            let container = arguments[0];
                            container.scrollTop += container.clientHeight * arguments[1];
                            container.style.border = '2px solid red';
                        """, scroll_container, scroll_step)
                        print(f"      Modal scroll {s+1}/{scrolls_per_loop} [factor: {scroll_step:.2f}]")
                        human_sleep(random.uniform(1.5, 2.5))

                except Exception as e:
                    print("   Failed modal scroll:", e)
                    print("   Falling back to full-page scroll.")
                    for s in range(scrolls_per_loop):
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        print(f"      Fallback scroll {s+1}/{scrolls_per_loop}")
                        human_sleep(random.uniform(1.5, 2.5))
            else:
                print("Modal container missing. Using full-page scroll.")
                for s in range(scrolls_per_loop):
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    print(f"      Full-page scroll {s+1}/{scrolls_per_loop}")
                    human_sleep(random.uniform(1.5, 2.5))

            # Re-add see more button click logic
            try:
                see_more_button = self.driver.find_element(
                    By.CSS_SELECTOR,
                    "#root > dialog > div > div > div > div > section > div > div > div > div._1xoe5hdi.cnuthtrs > button"
                )
                if see_more_button:
                    print("   Found 'See more' button — clicking.")
                    self.driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth' });", see_more_button)
                    human_sleep(2, 1)
                    ActionChains(self.driver).move_to_element(see_more_button).perform()
                    human_sleep(1.5, 0.5)
                    self.driver.execute_script("arguments[0].click();", see_more_button)
                    human_sleep(2, 1)
            except Exception:
                print("   No 'See more' button found this round.")

            if loop % 3 == 0 and random.random() < 0.5:
                pause = random.uniform(5, 9)
                print(f"   Taking a longer pause: {pause:.1f}s")
                human_sleep(pause / 2, pause / 2)

            human_sleep(*pause_range)

        df = pd.DataFrame(self.people)
        print(f"\nDone. Collected {len(df)} unique profiles.\n")
        return df

    def save_to_database(self, df, db_path="data/linkedin_profiles.db"):
        base_path = os.path.dirname(os.path.abspath(__file__))
        full_db_path = os.path.join(base_path, "..", db_path)
        os.makedirs(os.path.dirname(full_db_path), exist_ok=True)

        conn = sqlite3.connect(full_db_path)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_url TEXT UNIQUE,
            name TEXT,
            headline TEXT,
            location TEXT,
            connections TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()

        new_rows = 0
        if not df.empty:
            for _, row in df.iterrows():
                try:
                    cursor.execute("""
                        INSERT INTO profiles (profile_url, name, headline, location, connections)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        row.get("profile_url"),
                        row.get("name"),
                        row.get("headline"),
                        row.get("location", None),
                        row.get("connections", None)
                    ))
                    new_rows += 1
                except sqlite3.IntegrityError:
                    continue

            conn.commit()
            print(f"Inserted {new_rows} new profiles into the database.")
        else:
            print("No profiles scraped to insert.")

        conn.close()
