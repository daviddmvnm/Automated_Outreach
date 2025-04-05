import tkinter as tk
from tkinter import messagebox, simpledialog
from tkinter import Button, Label, Entry, Toplevel

import json
import os
import sys

# Pipeline & functional logic
from pipeline import run_pipeline
from functions.session_manager import SessionManager
from functions.ml_train_new import ModelTrainer
#from functions.linkedin_outreach import linkedin_outreach  


class LinkedInApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto-Connect")
        self.root.geometry("400x350")

        tk.Button(root, text="Process More Profiles", command=self.process_profiles).pack(pady=20)
        tk.Button(root, text="Send Connection Invites", command=self.send_connections).pack(pady=20)
        tk.Button(root, text="Train New Model", command=self.train_model).pack(pady=20)
        tk.Button(root, text="Edit Config", command=self.edit_config).pack(pady=10)

    def process_profiles(self):
        try:
            run_pipeline()
            messagebox.showinfo("Success", "Profile processing completed.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")

    def send_connections(self):
        messagebox.showinfo("Pending", "Send Connections logic not implemented yet.")

    def train_model(self):
        messagebox.showinfo("Pending", "Train Model logic not implemented yet.")

    def edit_config(self):
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(__file__)
        config_path = os.path.join(base_path, "config.json")

        try:
            with open(config_path, "r") as f:
                config = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config:\n{e}")
            return

        editable_fields = ["target_label", "max_profiles", "interest_keywords", "model_path", "run_prediction"]

        editor = Toplevel(self.root)
        editor.title("Edit Config")
        entries = {}

        for i, key in enumerate(editable_fields):
            Label(editor, text=key).grid(row=i, column=0, sticky="w", padx=5, pady=5)
            entry = Entry(editor, width=50)

            value = config.get(key, "")
            if isinstance(value, list):
                value = ", ".join(value)
            entry.insert(0, str(value))
            entry.grid(row=i, column=1, padx=5, pady=5)
            entries[key] = entry

        def save_config():
            try:
                for key, entry in entries.items():
                    raw = entry.get().strip()
                    if key == "interest_keywords":
                        config[key] = [x.strip() for x in raw.split(",") if x.strip()]
                    elif key == "max_profiles":
                        config[key] = int(raw)
                    else:
                        config[key] = raw

                with open(config_path, "w") as f:
                    json.dump(config, f, indent=4)
                messagebox.showinfo("Saved", "Config updated successfully.")
                editor.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save config:\n{e}")
            print(f"[DEBUG] Writing config to: {config_path}")


        Button(editor, text="Save", command=save_config).grid(row=len(entries), column=0, columnspan=2, pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = LinkedInApp(root)
    root.mainloop()
