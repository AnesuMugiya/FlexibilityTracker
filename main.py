"""
Main entry point for Flexibility Progress Tracker and Launches GUI
"""

# Imports
import cv2
import tkinter as tk
from core.pose_estimator import PoseEstimator
from core.multi_pose_analyzer import MultiPoseAnalyzer
# from core.pose_analyzer import PoseAnalyzer
from core.session import PoseSession
from gui.app import GUIApp


def main():
    # Core components
    estimator = PoseEstimator()
    analyser = MultiPoseAnalyzer() 
    session = PoseSession(pose_name="Front Split")  # Will be updated by GUI
    
    # GUI app
    app = GUIApp(estimator, analyser, session)
    app.mainloop()


if __name__ == "__main__":
    main()