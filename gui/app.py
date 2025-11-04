# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
from PIL import Image, ImageTk
from datetime import datetime, timedelta
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from core.sources import CameraSource, VideoFileSource, ImageSource
from filters.oneEuro import OneEuro
from filters.kalman2D import Kalman2D

class GUIApp(tk.Tk):
    def __init__(self, estimator, analyzer, session):
        super().__init__()
        self.title("Flexibility Progress Tracker")
        self.geometry("1100x800")
        self.configure(bg='#f7f5f3')  # Warm off-white background
        
        # Colour palette
        self.colors = {
            'primary': '#7a9b76',      # Sage green
            'secondary': '#a8bfa8',    # Light sage
            'accent': '#e8ddd4',       # Warm beige
            'background': '#f7f5f3',   # Off-white
            'surface': '#ffffff',      # Pure white
            'text_primary': '#2d3436', # Dark grey
            'text_secondary': '#636e72', # Medium grey
            'success': '#6c7b7f',      # Muted teal
            'warning': '#fab1a0'       # Soft coral
        }
        
        # Configure modern ttk style
        self.setup_styles()

        self.estimator = estimator
        self.analyzer = analyzer
        # self.available_poses = analyzer.get_available_poses()
        self.session = session
        self.angle_filter = OneEuro(freq=30)
        self.kf_wrist = Kalman2D(dt=1/30)
        self.kf_initialized = False

        # Always initialize lists for plotting
        self.timestamps = []
        self.raw_angles = []
        self.filtered_angles = []

        # current source
        self.source = None
        
        # Display dimensions for consistent aspect ratio
        self.display_width = 640
        self.display_height = 480

        # Create main container with padding and modern styling
        self.main_frame = ttk.Frame(self, style='Main.TFrame')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Show initial selection screen
        self.show_selection_screen()

    def setup_styles(self):
        """Configure modern ttk styles with earthy colors"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure main frame
        style.configure('Main.TFrame', background=self.colors['background'])
        
        # Modern card-like frames
        style.configure('Card.TFrame', 
                       background=self.colors['surface'],
                       relief='flat',
                       borderwidth=1)
        
        # Selection screen styling
        style.configure('Selection.TFrame',
                       background=self.colors['surface'],
                       relief='flat',
                       borderwidth=0)
        
        # Modern buttons with hover effects
        style.configure('Primary.TButton',
                       background=self.colors['primary'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 11),
                       padding=(20, 12))
        
        style.map('Primary.TButton',
                 background=[('active', self.colors['secondary']),
                            ('pressed', '#6b8a67')])
        
        style.configure('Secondary.TButton',
                       background=self.colors['accent'],
                       foreground=self.colors['text_primary'],
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 10),
                       padding=(16, 10))
        
        style.map('Secondary.TButton',
                 background=[('active', '#ddd2c7'),
                            ('pressed', '#d4c9bc')])
        
        # Title labels
        style.configure('Title.TLabel',
                       background=self.colors['surface'],
                       foreground=self.colors['text_primary'],
                       font=('Segoe UI', 24, 'bold'))
        
        style.configure('Subtitle.TLabel',
                       background=self.colors['surface'],
                       foreground=self.colors['text_secondary'],
                       font=('Segoe UI', 12))
        
        style.configure('Header.TLabel',
                       background=self.colors['background'],
                       foreground=self.colors['text_primary'],
                       font=('Segoe UI', 16, 'bold'))
        
        # Radio button styling
        style.configure('Primary.TRadiobutton',
                    background=self.colors['surface'],
                    foreground=self.colors['text_primary'],
                    font=('Segoe UI', 11))

    def show_selection_screen(self):
        """Modern welcome screen with card-based layout"""
        # Clear any existing widgets
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Center container
        center_frame = ttk.Frame(self.main_frame, style='Main.TFrame')
        center_frame.place(relx=0.5, rely=0.5, anchor='center')

        # Welcome card
        card_frame = ttk.Frame(center_frame, style='Card.TFrame', padding=40)
        card_frame.pack()

        # App icon/title section
        title_section = ttk.Frame(card_frame, style='Selection.TFrame')
        title_section.pack(pady=(0, 30))

        # Main title
        title_label = ttk.Label(title_section, text="Flexibility Progress Tracker", 
                               style='Title.TLabel')
        title_label.pack()

        # Subtitle
        subtitle_label = ttk.Label(title_section, 
                                  text="Track your progress and improve your flexibility", 
                                  style='Subtitle.TLabel')
        subtitle_label.pack(pady=(8, 0))



        # === NEW: POSE SELECTION SECTION ===
        pose_section = ttk.Frame(card_frame, style='Selection.TFrame')
        pose_section.pack(pady=(0, 25))

        ttk.Label(pose_section, text="Select Pose to Track", 
                font=('Segoe UI', 14, 'bold'),
                background=self.colors['surface'],
                foreground=self.colors['text_primary']).pack(pady=(0, 15))

        # Pose selection dropdown
        self.selected_pose = tk.StringVar(value='front_split')
        
        pose_options = {
            'front_split': 'Front Split',
            'forward_fold': 'Forward Fold'
        }
        
        pose_frame = ttk.Frame(pose_section, style='Selection.TFrame')
        pose_frame.pack()
        
        for pose_key, pose_label in pose_options.items():
            ttk.Radiobutton(
                pose_frame,
                text=pose_label,
                variable=self.selected_pose,
                value=pose_key,
                style='Primary.TRadiobutton'
            ).pack(pady=5)

        # separator = ttk.Frame(card_frame, style='Selection.TFrame', height=2)
        # separator.pack(fill='x', pady=20)


        # Buttons section
        buttons_frame = ttk.Frame(card_frame, style='Selection.TFrame')
        buttons_frame.pack()

        # Input source buttons with icons
        input_frame = ttk.Frame(buttons_frame, style='Selection.TFrame')
        input_frame.pack(pady=(0, 20))

        ttk.Label(input_frame, text="Choose Input Source", 
                 font=('Segoe UI', 14, 'bold'),
                 background=self.colors['surface'],
                 foreground=self.colors['text_primary']).pack(pady=(0, 15))

        # Source buttons in a grid
        source_grid = ttk.Frame(input_frame, style='Selection.TFrame')
        source_grid.pack()

        ttk.Button(source_grid, text="📹 Live Camera", 
                  command=self.select_camera, 
                  style='Primary.TButton',
                  width=18).grid(row=0, column=0, padx=8, pady=5)
        
        ttk.Button(source_grid, text="🎬 Video File", 
                  command=self.select_video, 
                  style='Primary.TButton',
                  width=18).grid(row=0, column=1, padx=8, pady=5)
        
        ttk.Button(source_grid, text="🖼️ Image File", 
                  command=self.select_image, 
                  style='Primary.TButton',
                  width=18).grid(row=1, column=0, padx=8, pady=5)
        
        ttk.Button(source_grid, text="🧪 Test Mode", 
                  command=self.select_test, 
                  style='Primary.TButton',
                  width=18).grid(row=1, column=1, padx=8, pady=5)

        # Separator
        separator = ttk.Frame(buttons_frame, style='Selection.TFrame', height=1)
        separator.pack(fill='x', pady=20)

        # Exit button
        ttk.Button(buttons_frame, text="Exit Application", 
                  command=self.destroy, 
                  style='Secondary.TButton',
                  width=25).pack()

    def show_main_interface(self):
        """Modern main interface with improved layout"""
        # Clear selection screen
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Header
        header_frame = ttk.Frame(self.main_frame, style='Main.TFrame')
        header_frame.pack(fill='x', pady=(0, 20))

        ttk.Label(header_frame, text=f"Analyzing: {self.analyzer.get_pose_name()}", 
                style='Header.TLabel').pack(side='left')
        
        # Add pose indicator badge
        pose_badge = ttk.Label(header_frame, 
                            text=f"Metric: {self.analyzer.get_metric_unit()}", 
                            font=('Segoe UI', 10),
                            background=self.colors['accent'],
                            foreground=self.colors['text_primary'],
                            padding=(10, 5))
        pose_badge.pack(side='left', padx=20)

        
        # Main content area
        content_frame = ttk.Frame(self.main_frame, style='Main.TFrame')
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Video section (left side)
        video_section = ttk.Frame(content_frame, style='Card.TFrame', padding=20)
        video_section.pack(side=tk.LEFT, fill='both', expand=True, padx=(0, 10))

        ttk.Label(video_section, text="Live Feed", 
                 font=('Segoe UI', 12, 'bold'),
                 background=self.colors['surface'],
                 foreground=self.colors['text_primary']).pack(pady=(0, 10))

        # Video display with modern border
        video_container = tk.Frame(video_section, 
                                  bg=self.colors['surface'], 
                                  highlightbackground=self.colors['accent'],
                                  highlightthickness=2)
        video_container.pack(pady=(0, 10))

        self.video_label = tk.Label(video_container, 
                                   bg='#1a1a1a',  # Dark background for video
                                   highlightbackground=self.colors['accent'],
                                   highlightthickness=1)
        self.video_label.pack(padx=2, pady=2)

        # Plot section (right side - only in test mode)
        if self.session.mode == True:
            plot_section = ttk.Frame(content_frame, style='Card.TFrame', padding=20)
            plot_section.pack(side=tk.RIGHT, fill='both', expand=True)

            ttk.Label(plot_section, text="Angle Analysis", 
                     font=('Segoe UI', 12, 'bold'),
                     background=self.colors['surface'],
                     foreground=self.colors['text_primary']).pack(pady=(0, 10))

            # Configure matplotlib with colors
            plt.style.use('default')
            self.fig = Figure(figsize=(6, 4), dpi=100, facecolor=self.colors['surface'])
            self.ax = self.fig.add_subplot(111)
            self.ax.set_facecolor('#fafafa')
            self.ax.grid(True, alpha=0.3, color=self.colors['text_secondary'])
            self.ax.spines['top'].set_visible(False)
            self.ax.spines['right'].set_visible(False)
            self.ax.spines['left'].set_color(self.colors['text_secondary'])
            self.ax.spines['bottom'].set_color(self.colors['text_secondary'])
            
            self.ax.set_title("Angle over Time", fontsize=12, color=self.colors['text_primary'], pad=20)
            self.ax.set_xlabel("Time (s)", color=self.colors['text_secondary'])
            self.ax.set_ylabel("Angle (degrees)", color=self.colors['text_secondary'])

            self.canvas = FigureCanvasTkAgg(self.fig, master=plot_section)
            plot_widget = self.canvas.get_tk_widget()
            plot_widget.configure(bg=self.colors['surface'])
            plot_widget.pack(fill=tk.BOTH, expand=True)

        # Controls section at bottom
        controls_section = ttk.Frame(self.main_frame, style='Card.TFrame', padding=15)
        controls_section.pack(fill='x', pady=(20, 0))

        # Control buttons
        controls_left = ttk.Frame(controls_section, style='Card.TFrame')
        controls_left.pack(side='left')

        controls_right = ttk.Frame(controls_section, style='Card.TFrame')
        controls_right.pack(side='right')

        ttk.Button(controls_left, text="← Back to Sources", 
                  command=self.back_to_selection,
                  style='Secondary.TButton').pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(controls_right, text="💾 Save Best Result", 
                  command=self.save_best,
                  style='Primary.TButton').pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_right, text="Exit", 
                  command=self.destroy,
                  style='Secondary.TButton').pack(side=tk.LEFT, padx=(10, 0))

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
        # Reset test-mode data
        self.timestamps = []
        self.raw_angles = []
        self.filtered_angles = []

    def select_camera(self):

        # Set the selected pose in analyzer
        self.analyzer.set_pose(self.selected_pose.get())
        self.session.pose_name = self.analyzer.get_pose_name()

        self.session.best_value = None
        self.set_source(CameraSource(0))
        self.show_main_interface()
        self.after(0, self.update_frame)

    def select_video(self):
        path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4;*.mov;*.avi;*.mkv"), ("All files", "*.*")]
        )
        if not path: 
            return
        
        # Set the selected pose
        self.analyzer.set_pose(self.selected_pose.get())
        self.session.pose_name = self.analyzer.get_pose_name()


        self.session.best_value = None
        self.set_source(VideoFileSource(path))
        self.show_main_interface()
        self.after(0, self.update_frame)

    def select_image(self):
        path = filedialog.askopenfilename(
            title="Select Image File",
            filetypes=[("Image files", "*.jpg;*.jpeg;*.png;*.bmp"), ("All files", "*.*")]
        )
        if not path: 
            return
        
        # Set the selected pose
        self.analyzer.set_pose(self.selected_pose.get())
        self.session.pose_name = self.analyzer.get_pose_name()

        self.session.best_value = None
        self.set_source(ImageSource(path))
        self.show_main_interface()
        self.after(0, self.update_frame)

    def set_source(self, src):
        # release old
        if self.source:
            self.source.release()
        self.source = src

        self.kf_wrist = Kalman2D(dt=1/30)  # Reset filter for new source
        self.kf_initialized = False

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
        if (datetime.now() - self.session.session_start) > timedelta(seconds=60):
            self.session.save_result()
            msg = (
            f"Best value: {self.session.best_value:.2f}°\n"
            f"Worst value: {self.session.worst_value:.2f}°\n"
            f"Error range (Jitter): {(self.session.best_value - self.session.worst_value):.2f}°\n"
            f"Observed Average: {(self.session.sum/self.session.count):.2f}°"
            )

            messagebox.showinfo("Session Complete", msg)

            self.session.best_value = None
            self.session.worst_value = None
            self.session.count = 0
            self.session.sum = 0
            self.session.session_start = datetime.now() 

            # Reset test-mode data
            self.timestamps = []
            self.raw_angles = []
            self.filtered_angles = []

        else:
            return

    def save_best(self):
        self.session.save_result()
        messagebox.showinfo("✅ Saved Successfully", f"Best flexibility value saved: {self.session.best_value:.2f}°")

    def update_frame(self):
        if self.source is None:
            return

        ret, frame = self.source.read()
        if not ret or frame is None:
            # End of video: stop loop (or switch back to camera if you prefer)
            return

        # Process with MediaPipe
        frame_bgr, results = self.estimator.process_frame(frame)

        # === NEW: Use MultiPoseAnalyzer ===
        if results.pose_landmarks:
            lm = results.pose_landmarks.landmark
            h, w, _ = frame_bgr.shape
            
            # Analyze the selected pose
            pose_results = self.analyzer.analyze(lm, w, h, frame_bgr)
            
            # Get the primary metric (automatically switches based on pose type)
            if pose_results['confidence'] > 0.5:  # Only track if confident
                raw_metric = pose_results['primary_metric']
                smoothed_metric = self.angle_filter(raw_metric)
                
                # Update session with smoothed value
                self.session.update_best(smoothed_metric)
                
                # Display metric on screen
                metric_text = f"{smoothed_metric:.1f}{self.analyzer.get_metric_unit()}"
                
                # Find a good position based on pose type
                if self.analyzer.current_pose == 'front_split':
                    # Display near hips
                    hip_x = int((lm[23].x + lm[24].x) / 2 * w)
                    hip_y = int((lm[23].y + lm[24].y) / 2 * h)
                    pos = (hip_x, hip_y - 40)
                else:  # forward_fold or other
                    # Display near center top
                    pos = (int(w / 2) - 100, 50)
                
                cv2.putText(frame_bgr, metric_text, pos,
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 4, cv2.LINE_AA)
                cv2.putText(frame_bgr, metric_text, pos,
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (122, 155, 118), 2, cv2.LINE_AA)
                
                # Display form feedback if available
                if pose_results.get('feedback'):
                    y_offset = 150
                    for feedback in pose_results['feedback']:
                        cv2.putText(frame_bgr, feedback, (10, y_offset),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
                        cv2.putText(frame_bgr, feedback, (10, y_offset),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 150, 0), 1, cv2.LINE_AA)
                        y_offset += 30
                
                # Test mode plotting (if enabled)
                if self.session.mode == True:
                    t = (datetime.now() - self.session.session_start).total_seconds()
                    self.timestamps.append(t)
                    self.raw_angles.append(raw_metric)
                    self.filtered_angles.append(smoothed_metric)

                    if len(self.timestamps) % 10 == 0:
                        self.ax.clear()
                        self.ax.set_facecolor('#fafafa')
                        self.ax.grid(True, alpha=0.3, color=self.colors['text_secondary'])
                        self.ax.spines['top'].set_visible(False)
                        self.ax.spines['right'].set_visible(False)
                        
                        title = f"{self.analyzer.get_pose_name()} over Time"
                        self.ax.set_title(title, fontsize=12, color=self.colors['text_primary'])
                        self.ax.set_xlabel("Time (s)", color=self.colors['text_secondary'])
                        self.ax.set_ylabel(f"Metric ({self.analyzer.get_metric_unit()})", 
                                        color=self.colors['text_secondary'])
                        
                        self.ax.plot(self.timestamps, self.raw_angles, 
                                label="Raw", alpha=0.4, color="#69411F", linewidth=2)
                        self.ax.plot(self.timestamps, self.filtered_angles, 
                                label="Filtered", color=self.colors['primary'], linewidth=2)
                        
                        self.ax.legend(frameon=False, loc='upper right')
                        self.canvas.draw()

        # Resize and display frame
        frame_resized = self.resize_frame(frame_bgr)
        img = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        imgtk = ImageTk.PhotoImage(image=Image.fromarray(img))
        self.video_label.imgtk = imgtk
        self.video_label.configure(image=imgtk)

        if self.session.mode == True:
            self.test_mode()
            
        self.after(1, self.update_frame)


    def destroy(self):
        if self.source: 
            self.source.release()
        super().destroy()