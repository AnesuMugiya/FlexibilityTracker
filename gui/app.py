"""
Tkinter (or PyQt) main app class
"""

import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk

class GUIApp(tk.Tk):
    def __init__(self, estimator, analyser, session):
        super().__init__()
        self.title("Flexibility Progress Tracker")
        self.geometry("800x600")

        self.estimator = estimator
        self.analyser = analyser
        self.session = session

        # Video display
        self.video_label = tk.Label(self)
        self.video_label.pack()

        # Controls
        self.button_frame = ttk.Frame(self)
        self.button_frame.pack(pady=10)

        ttk.Button(self.button_frame, text="Save Best Pose", command=self.save_pose).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="Quit", command=self.destroy).pack(side=tk.LEFT, padx=5)

        # Capture
        self.cap = cv2.VideoCapture(0)
        self.update_frame()

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame, results = self.estimator.process_frame(frame)

            # Kept getting errors here for reasons unknown
            try:
                # Example: track elbow angle (replace later with split metrics)
                if results.pose_landmarks:
                    landmarks = results.pose_landmarks.landmark
                    # Convert normalized coords to pixel coords
                    h, w, _ = frame.shape
                    shoulder = [landmarks[11].x * w, landmarks[11].y * h]
                    elbow = [landmarks[13].x * w, landmarks[13].y * h]
                    wrist = [landmarks[15].x * w, landmarks[15].y * h]

                    angle = self.analyser.calculate_angle(shoulder, elbow, wrist)
                    self.session.update_best(angle)


                # Draw angle near the elbow
                if angle is not None:
                    cv2.putText(
                        frame,
                        f"{angle:.2f}°",
                        (int(elbow[0]), int(elbow[1])),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2, cv2.LINE_AA
                    )
            except:
                pass
            # Convert frame for Tkinter
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

        self.after(10, self.update_frame)

    def save_pose(self):
        self.session.save_result()
        print(f"Saved best value: {self.session.best_value}")
