# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
from PIL import Image, ImageTk
from datetime import datetime, timedelta

from core.sources import CameraSource, VideoFileSource, ImageSource
from core.filters import OneEuro

class GUIApp(tk.Tk):
    def __init__(self, estimator, analyzer, session):
        super().__init__()
        self.title("Flexibility Progress Tracker")
        self.geometry("900x700")

        self.estimator = estimator
        self.analyzer = analyzer
        self.session = session
        self.angle_filter = OneEuro(freq=30, min_cutoff=2.0 , beta=0.01, d_cutoff=1.0)

        # current source
        self.source = None
        
        # Display dimensions for consistent aspect ratio
        self.display_width = 640
        self.display_height = 480

        # Create main container
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Show initial selection screen
        self.show_selection_screen()

    def show_selection_screen(self):
        # Clear any existing widgets
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Create selection screen
        selection_frame = ttk.Frame(self.main_frame)
        selection_frame.pack(expand=True)

        # Title
        title_label = ttk.Label(selection_frame, text="Choose Input Source", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=20)

        # Button frame
        button_frame = ttk.Frame(selection_frame)
        button_frame.pack(pady=20)

        # Source selection buttons
        ttk.Button(button_frame, text="Use Camera", 
                  command=self.select_camera, width=20).pack(pady=10)
        ttk.Button(button_frame, text="Open Video File", 
                  command=self.select_video, width=20).pack(pady=10)
        ttk.Button(button_frame, text="Open Image File", 
                  command=self.select_image, width=20).pack(pady=10)
        
        # Mode selection
        ttk.Button(button_frame, text="Test Mode", 
                  command=self.select_test, width=20).pack(pady=10)

        # Quit button
        ttk.Button(button_frame, text="Quit", 
                  command=self.destroy, width=20).pack(pady=20)

    def show_main_interface(self):
        # Clear selection screen
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Video display frame with fixed size
        video_frame = ttk.Frame(self.main_frame)
        video_frame.pack(pady=10)

        self.video_label = tk.Label(video_frame, bg='black')
        self.video_label.pack()

        # Controls frame
        controls_frame = ttk.Frame(self.main_frame)
        controls_frame.pack(pady=10)

        ttk.Button(controls_frame, text="Back to Selection", 
                  command=self.back_to_selection).pack(side=tk.LEFT, padx=5)
        # ttk.Button(controls_frame, text="Use Camera", 
        #           command=self.use_camera).pack(side=tk.LEFT, padx=5)
        # ttk.Button(controls_frame, text="Open Video…", 
        #           command=self.open_video).pack(side=tk.LEFT, padx=5)
        # ttk.Button(controls_frame, text="Open Image…", 
        #           command=self.open_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Save Best", 
                  command=self.save_best).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Quit", 
                  command=self.destroy).pack(side=tk.LEFT, padx=5)

    def resize_frame(self, frame):
        """Resize frame to maintain aspect ratio within display dimensions"""
        h, w = frame.shape[:2]
        
        # Calculate scaling factor to fit within display dimensions
        scale_w = self.display_width / w
        scale_h = self.display_height / h
        scale = min(scale_w, scale_h)
        
        # Calculate new dimensions
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # Resize frame
        resized = cv2.resize(frame, (new_w, new_h))
        
        return resized

    def back_to_selection(self):
        # Release current source
        if self.source:
            self.source.release()
            self.source = None
        
        # Reset best value
        self.session.best_value = None
        
        # Show selection screen
        self.show_selection_screen()

    def select_test(self):
        self.session.mode = True


    def select_camera(self):
        self.session.best_value = None
        self.set_source(CameraSource(0))
        self.show_main_interface()
        self.after(0, self.update_frame)

    def select_video(self):
        path = filedialog.askopenfilename(
            filetypes=[("Video files", "*.mp4;*.mov;*.avi;*.mkv"), ("All files", "*.*")]
        )
        if not path: 
            return
        self.session.best_value = None
        self.set_source(VideoFileSource(path))
        self.show_main_interface()
        self.after(0, self.update_frame)

    def select_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg;*.jpeg;*.png;*.bmp"), ("All files", "*.*")]
        )
        if not path: 
            return
        self.session.best_value = None
        self.set_source(ImageSource(path))
        self.show_main_interface()
        self.after(0, self.update_frame)

    def set_source(self, src):
        # release old
        if self.source:
            self.source.release()
        self.source = src

    def use_camera(self):
        self.session.best_value = None
        self.set_source(CameraSource(0))
        self.after(0, self.update_frame)
        

    def open_video(self):
        path = filedialog.askopenfilename(
            filetypes=[("Video files", "*.mp4;*.mov;*.avi;*.mkv"), ("All files", "*.*")]
        )
        if not path: return
        self.session.best_value = None
        self.set_source(VideoFileSource(path))
        self.after(0, self.update_frame)

    def open_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg;*.jpeg;*.png;*.bmp"), ("All files", "*.*")]
        )
        if not path: return
        self.session.best_value = None
        self.set_source(ImageSource(path))
        self.after(0, self.update_frame)

    def test_mode(self):
        if (datetime.now() - self.session.session_start) > timedelta(seconds=30):
            self.session.save_result()
            msg = (
            f"Best value: {self.session.best_value:.2f}\n"
            f"Worst value: {self.session.worst_value:.2f}\n"
            f"Error range (Jitter): {(self.session.best_value - self.session.worst_value):.2f}\n"
            f"Observed Average: {(self.session.sum/self.session.count):.2f}"
            )

            messagebox.showinfo("Session Summary", msg)

            self.session.best_value = None
            self.session.worst_value = None
            self.session.count = 0
            self.session.sum = 0
            self.session.session_start = datetime.now() 

        else:
            return


    def save_best(self):
        self.session.save_result()
        messagebox.showinfo("Saved", f"Best value saved: {self.session.best_value}")


    def update_frame(self):
        if self.source is None:
            return

        ret, frame = self.source.read()
        if not ret or frame is None:
            # End of video: stop loop (or switch back to camera if you prefer)
            return

        # Process with MediaPipe
        frame_bgr, results = self.estimator.process_frame(frame)

        # Example angle: LEFT elbow
        if results.pose_landmarks:
            lm = results.pose_landmarks.landmark
            h, w, _ = frame_bgr.shape
            LS = self.estimator.mp_pose.PoseLandmark.RIGHT_SHOULDER.value
            LE = self.estimator.mp_pose.PoseLandmark.RIGHT_ELBOW.value
            LW = self.estimator.mp_pose.PoseLandmark.RIGHT_WRIST.value

            sh = (lm[LS].x * w, lm[LS].y * h)
            el = (lm[LE].x * w, lm[LE].y * h)
            wr = (lm[LW].x * w, lm[LW].y * h)

            raw_angle = self.analyzer.calculate_angle(sh, el, wr)
            smoothed_angle = self.angle_filter(raw_angle)

            self.session.update_best(smoothed_angle)

            cv2.putText(frame_bgr, f"{smoothed_angle:.2f} {chr(176)}",
                        (int(el[0]), int(el[1])),
                        cv2.FONT_HERSHEY_SIMPLEX, 2.5, (255,255,255), 2, cv2.LINE_AA)

        # Resize frame to fit display area
        frame_resized = self.resize_frame(frame_bgr)

        # Convert to RGB and display in Tkinter
        img = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        imgtk = ImageTk.PhotoImage(image=Image.fromarray(img))
        self.video_label.imgtk = imgtk
        self.video_label.configure(image=imgtk)

        if self.session.mode == True:
            self.test_mode()
            
        # Schedule next frame:
        # - Camera/video: keep looping ~30–60 FPS
        # - Image: keep refreshing so the window stays responsive
        
        self.after(10, self.update_frame)

    def destroy(self):
        if self.source: 
            self.source.release()
        super().destroy()