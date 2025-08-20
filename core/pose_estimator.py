"""
Handles MediaPipe pose detection & webcam feed.
"""


import cv2
import mediapipe as mp

class PoseEstimator:

    
    # min_detection_confidence set what detection confidence wewant
    # min_tracking_confidence defines tracking confidence to maintain state
    # For more accurate model or tighter detections use higher confidence scores on these parameters
    # Needs to be a trade off. Higher scores = less detections especially for lower quality cameras and less maintanence of state
    # Test to find the best score
    def __init__(self, min_detection_conf=0.5, min_tracking_conf=0.5):
        # imports pose estimation model from mediapipe
        self.mp_pose = mp.solutions.pose 
        # Setup mediapipe instance as variable pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=min_detection_conf,
            min_tracking_confidence=min_tracking_conf
        ) 
        # Drawing utitilities for visualising poses
        self.mp_drawing = mp.solutions.drawing_utils 

    def process_frame(self, frame):
        """Process frame with MediaPipe and return results + annotated image"""
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = self.pose.process(image)

        # Convert back for OpenCV rendering
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        if results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                image, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS
            )

        return image, results