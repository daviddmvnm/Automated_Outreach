import os
import sys
import sqlite3
import pandas as pd
import joblib
from datetime import datetime
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report


class ModelTrainer:
    def __init__(self, db_path="data/linkedin_profiles.db", model_dir="models", model_type="logistic"):
        # Handle .exe or script environment paths
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        self.db_path = os.path.abspath(os.path.join(base_path, "..", db_path))
        self.model_dir = os.path.abspath(os.path.join(base_path, "..", model_dir))
        os.makedirs(self.model_dir, exist_ok=True)

        self.model_type = model_type

    def load_training_data(self):
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("""
            SELECT * FROM processed_data
            WHERE connection_sent = 1
        """, conn)
        conn.close()

        df = df[df["connection_accepted"].isin([0, 1])]  # Keep only labeled rows
        return df

    def train_model(self, df):
        features = [
            "tag_h1_coordination_game", "tag_h2_status_seekers",
            "tag_h3_shared_interests", "tag_h4_profile_effort",
            "tag_h5_likely_female"
        ]
        X = df[features]
        y = df["connection_accepted"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42
        )

        if self.model_type == "logistic":
            model = LogisticRegression(max_iter=1000)
        elif self.model_type == "random_forest":
            model = RandomForestClassifier(n_estimators=100, random_state=42)
        else:
            raise ValueError("Unsupported model type. Use 'logistic' or 'random_forest'.")

        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        print("\n[REPORT] Classification Report:\n")
        print(classification_report(y_test, y_pred))

        return model

    def save_model(self, model, filename=None):
        if filename is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"{self.model_type}_model_{timestamp}.pkl"

        model_path = os.path.join(self.model_dir, filename)
        joblib.dump(model, model_path)
        print(f"\n[SUCCESS] Model saved to {model_path}")

    def run(self):
        df = self.load_training_data()
        if df.empty:
            print("[INFO] Not enough labeled data to train a model.")
            return

        model = self.train_model(df)
        self.save_model(model)
