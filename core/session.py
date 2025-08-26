"""
Stores best results per session, saves to CSV/JSON.
"""


import csv
from datetime import datetime

class PoseSession:
    def __init__(self, pose_name="Generic Pose"):
        self.pose_name = pose_name
        self.best_value = None

    def update_best(self, new_value):
        if self.best_value is None or new_value > self.best_value:
            self.best_value = new_value

    def save_result(self, filepath="data/progress.csv"):
        with open(filepath, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now(), self.pose_name, self.best_value])