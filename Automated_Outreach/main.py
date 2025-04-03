#auto-connect main
from functions.session_manager import SessionManager
from functions.shallow_scraper import ShallowScraper
import json
import time
import os

if __name__ == "__main__":
    # Step 1: Load config
    config_path = os.path.join(os.path.dirname(__file__), "config.json")

    with open(config_path) as f:
        config = json.load(f)


    target_label = config.get("target_label", "University of Exeter")
    max_profiles = config.get("max_profiles", 100)
    db_path = config.get("db_path", "functions_and_data/linkedin_profiles.db")

    # Step 2: Start session
    session = SessionManager()
    driver = session.login()

    # Step 3: Use shallow scraper
    scraper = ShallowScraper(driver)

    success = scraper.wait_and_open_target_tab(target_label)

    if success:
        df = scraper.scroll_and_extract_profiles(max_profiles=max_profiles)
        scraper.save_to_database(df, db_path=db_path)
    else:
        print("Could not open target tab. No scraping done.")

    # Optional: Pause so browser stays open if needed
    input("Done. Press ENTER to close the browser and exit...")
    driver.quit()
