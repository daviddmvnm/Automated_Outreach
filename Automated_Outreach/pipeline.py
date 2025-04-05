import os
import sys
import json
import pandas as pd
from functions.session_manager import SessionManager
from functions.shallow_scraper import ShallowScraper
from functions.html_extraction import HTMLExtraction
from functions.profile_parser import ProfileParser
from functions.preprocessing import DataPreprocessing
from functions.ml_layer import ModelPredictor

def run_pipeline(driver=None):
    # Step 1: Load config (compatible with .exe builds)
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(__file__)

    config_path = os.path.join(base_path, "config.json")
    with open(config_path) as f:
        config = json.load(f)

    # Load configurable values
    target_label = config.get("target_label", "University of Exeter")
    max_profiles = config.get("max_profiles", 100)
    db_path = config.get("db_path", "data/linkedin_profiles.db")
    run_html_extraction = config.get("run_html_extraction", True)
    run_parsing = config.get("run_parsing", True)
    run_prediction = config.get("run_prediction", True)
    model_path = config.get("model_path", "models/default_model.pkl")
    prediction_threshold = config.get("prediction_threshold", 0.0)

    # Step 2: Start session if not provided
    close_driver = False
    if driver is None:
        session = SessionManager()
        driver = session.login()
        close_driver = True

    try:
        # Step 3: Shallow scrape
        scraper = ShallowScraper(driver)
        success = scraper.wait_and_open_target_tab(target_label)

        if success:
            df = scraper.scroll_and_extract_profiles(max_profiles=max_profiles)
            scraper.save_to_database(df, db_path=db_path)
        else:
            print("Could not open target tab. No scraping done.")

        # Step 4: HTML Extraction
        if run_html_extraction:
            print("\n[INFO] Starting HTML profile caching...\n")
            extractor = HTMLExtraction(driver, db_path=db_path, cache_dir="data/html_cache")
            extractor.run(max_profiles=max_profiles)

        # Step 5: Parse Profiles
        parsed_profiles = []
        if run_parsing:
            print("\n[INFO] Parsing cached HTML profiles...\n")
            cache_folder = os.path.join(base_path, "data", "html_cache")
            profile_ids = [
                int(f.split("_")[1].split(".")[0])
                for f in os.listdir(cache_folder)
                if f.startswith("profile_") and f.endswith(".html")
            ]

            parser = ProfileParser()
            for pid in sorted(profile_ids):
                parsed = parser.parse_profile(pid)
                if parsed:
                    parsed_profiles.append(parsed)
                    print(f"[Parsed] Profile {pid}: {parsed.get('connection_count')} connections, "
                          f"{len(parsed.get('experiences', []))} experience entries.")

        # Step 6: Clean, tag, and save to DB
        if parsed_profiles:
            df_raw = pd.DataFrame(parsed_profiles)
            processor = DataPreprocessing(df_raw)
            processor.run_cleaning()
            processor.run_tagging()
            processor.save_to_database()

        # Step 7: Predict and return sorted outreach-ready leads
        if run_prediction:
            predictor = ModelPredictor(model_path=model_path, db_path=db_path)
            sorted_df = predictor.run(min_score=prediction_threshold)

            if not sorted_df.empty:
                print(f"\n[INFO] Top profiles to consider for outreach:")
                print(sorted_df[["profile_id", "predicted_acceptance"]].head(10))
            else:
                print("[INFO] No profiles passed the prediction threshold.")

    except Exception as e:
        print(f"[ERROR] An issue occurred during scraping/extraction/processing: {e}")

    finally:
        if close_driver:
            input("\nDone. Press ENTER to close the browser and exit...")
            driver.quit()
