import os
import sys
import sqlite3
import pandas as pd
import joblib  # Assumes models are saved using joblib

class ModelPredictor:
    def __init__(self, model_path="models/logistic_model.pkl", db_path="data/linkedin_profiles.db", min_score=0.0):
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        self.model_path = os.path.abspath(os.path.join(base_path, "..", model_path))
        self.db_path = os.path.abspath(os.path.join(base_path, "..", db_path))
        self.min_score = min_score
        self.model = self.load_model()

    def load_model(self):
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found at {self.model_path}")
        return joblib.load(self.model_path)

    def fetch_data(self):
        conn = sqlite3.connect(self.db_path)
        query = """
        SELECT profile_id, tag_h1_coordination_game, tag_h2_status_seekers,
               tag_h3_shared_interests, tag_h4_profile_effort, tag_h5_likely_female
        FROM processed_data
        WHERE connection_sent = 0
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def predict(self, df):
        features = [
            "tag_h1_coordination_game", "tag_h2_status_seekers",
            "tag_h3_shared_interests", "tag_h4_profile_effort",
            "tag_h5_likely_female"
        ]
        X = df[features]
        predictions = self.model.predict_proba(X)[:, 1]  # Probability of class 1
        df["predicted_acceptance"] = predictions
        return df

    def update_predictions_in_db(self, df):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for _, row in df.iterrows():
            cursor.execute("""
                UPDATE processed_data
                SET predicted_acceptance = ?
                WHERE profile_id = ?
            """, (row["predicted_acceptance"], row["profile_id"]))
        conn.commit()
        conn.close()
        print(f"[SUCCESS] Updated {len(df)} predictions in the database.")

    def run(self):
        df = self.fetch_data()
        if df.empty:
            print("[INFO] No profiles to predict on.")
            return pd.DataFrame()

        df_pred = self.predict(df)
        self.update_predictions_in_db(df_pred)

        # Filter + sort by predicted_acceptance descending
        df_filtered = df_pred[df_pred["predicted_acceptance"] >= self.min_score].copy()
        df_sorted = df_filtered.sort_values(by="predicted_acceptance", ascending=False).reset_index(drop=True)

        print(f"[INFO] {len(df_sorted)} profiles ready for outreach (score >= {self.min_score})")
        return df_sorted
