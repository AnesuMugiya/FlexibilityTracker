"""
Stores best results per session, saves to CSV/JSON.
"""


import csv
from datetime import datetime

class PoseSession:
    def __init__(self, pose_name="Generic Pose"):
        self.pose_name = pose_name
        self.best_value = None
        self.worst_value = None
        self.session_start = datetime.now()

        # The following properties are for testing purposes. These slow down the code
        self.mode = False
        self.sum = 0
        self.count = 0

    def update_best(self, new_value):
        if self.best_value is None or new_value > self.best_value:
            self.best_value = new_value
        
        # The following functions are for testing purposes
        if self.mode == True:
            if self.worst_value is None or new_value < self.worst_value:
                self.worst_value = new_value
            self.count += 1
            self.sum = self.sum + new_value
        
        


    def save_result(self, filepath="data/progress.csv"):
        with open(filepath, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now(), self.pose_name, self.best_value])

    
