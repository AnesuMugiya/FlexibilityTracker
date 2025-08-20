"""
Main entry point for Flexibility Progress Tracker and Launches GUI
"""

# Imports
import cv2
import tkinter as tk
from core.pose_estimator import PoseEstimator
from core.pose_analyser import PoseAnalyser
from core.session import PoseSession
from gui.app import GUIApp


def main():
    # Core components
    estimator = PoseEstimator()
    analyser = PoseAnalyser()
    session = PoseSession(pose_name="Split Test")  # You can change pose dynamically later

    # GUI app
    app = GUIApp(estimator, analyser, session)
    app.mainloop()


if __name__ == "__main__":
    main()