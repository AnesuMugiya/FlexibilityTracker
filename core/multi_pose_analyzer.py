"""
Multi-pose analysis system that can measure different flexibility poses
Extensible framework for adding new pose types
"""

import numpy as np
import cv2

class PoseAnalyzer:
    """Base analyzer with common angle/distance calculations"""
    
    @staticmethod
    def calculate_angle(a, b, c):
        """Calculate angle at point b formed by points a-b-c"""
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)
        
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(radians * 180.0 / np.pi)
        
        if angle > 180.0:
            angle = 360 - angle
            
        return angle
    
    @staticmethod
    def calculate_distance(p1, p2):
        """Calculate Euclidean distance between two points"""
        p1 = np.array(p1)
        p2 = np.array(p2)
        return np.linalg.norm(p1 - p2)
    
    @staticmethod
    def point_to_line_distance(point, line_start, line_end):
        """Calculate perpendicular distance from point to line"""
        point = np.array(point)
        line_start = np.array(line_start)
        line_end = np.array(line_end)
        
        # Vector from line_start to line_end
        line_vec = line_end - line_start
        # Vector from line_start to point
        point_vec = point - line_start
        
        # Project point onto line
        line_len = np.linalg.norm(line_vec)
        if line_len == 0:
            return np.linalg.norm(point_vec)
        
        line_unitvec = line_vec / line_len
        proj_length = np.dot(point_vec, line_unitvec)
        proj = line_start + proj_length * line_unitvec
        
        return np.linalg.norm(point - proj)


class FrontSplitAnalyzer(PoseAnalyzer):
    """Analyzes front split poses"""
    
    def __init__(self, calibration_factor=None):
        self.calibration_factor = calibration_factor
        self.reference_height = None
        self.name = "Front Split"
        self.unit = "%"  # Primary metric unit
    
    def analyze(self, landmarks, image_width, image_height, draw_frame=None):
        """Main analysis method"""
        results = {'pose_type': 'front_split'}
        
        # Extract key points
        left_hip = (landmarks[23].x * image_width, landmarks[23].y * image_height)
        right_hip = (landmarks[24].x * image_width, landmarks[24].y * image_height)
        hip_center = ((left_hip[0] + right_hip[0]) / 2, (left_hip[1] + right_hip[1]) / 2)
        
        left_shoulder = (landmarks[11].x * image_width, landmarks[11].y * image_height)
        right_shoulder = (landmarks[12].x * image_width, landmarks[12].y * image_height)
        shoulder_center = ((left_shoulder[0] + right_shoulder[0]) / 2, 
                          (left_shoulder[1] + right_shoulder[1]) / 2)
        
        left_knee = (landmarks[25].x * image_width, landmarks[25].y * image_height)
        right_knee = (landmarks[26].x * image_width, landmarks[26].y * image_height)
        
        left_ankle = (landmarks[27].x * image_width, landmarks[27].y * image_height)
        right_ankle = (landmarks[28].x * image_width, landmarks[28].y * image_height)
        
        # Determine front/back legs
        if left_knee[1] > right_knee[1]:
            front_hip, front_knee, front_ankle = left_hip, left_knee, left_ankle
            back_hip, back_knee, back_ankle = right_hip, right_knee, right_ankle
        else:
            front_hip, front_knee, front_ankle = right_hip, right_knee, right_ankle
            back_hip, back_knee, back_ankle = left_hip, left_knee, left_ankle
        
        # Calculations
        hip_flexor_angle = self.calculate_angle(front_ankle, front_hip, shoulder_center)
        hip_opening_angle = self.calculate_angle(front_ankle, hip_center, back_ankle)
        front_knee_angle = self.calculate_angle(front_hip, front_knee, front_ankle)
        back_knee_angle = self.calculate_angle(back_hip, back_knee, back_ankle)
        
        # Floor distance
        floor_level = max(left_ankle[1], right_ankle[1], 
                         landmarks[29].y * image_height, landmarks[30].y * image_height)
        hip_to_floor_px = floor_level - hip_center[1]
        
        # Auto-calibrate
        if self.calibration_factor is None:
            self._auto_calibrate(landmarks, image_height)
        
        # Calculate split percentage
        angle_factor = min(hip_opening_angle / 180.0, 1.0)
        
        if self.calibration_factor:
            hip_to_floor_cm = hip_to_floor_px * self.calibration_factor
            results['hip_to_floor_cm'] = hip_to_floor_cm
            distance_factor = max(0, min(1.0, 1.0 - (hip_to_floor_cm / 50.0)))
        else:
            distance_factor = max(0, min(1.0, 1.0 - (hip_to_floor_px / (image_height * 0.3))))
        
        split_percentage = ((angle_factor * 0.6) + (distance_factor * 0.4)) * 100
        
        # Store results
        results['primary_metric'] = split_percentage
        results['hip_opening_angle'] = hip_opening_angle
        results['hip_flexor_angle'] = hip_flexor_angle
        results['front_knee_angle'] = front_knee_angle
        results['back_knee_angle'] = back_knee_angle
        results['hip_to_floor_px'] = hip_to_floor_px
        
        # Confidence
        key_landmarks = [23, 24, 25, 26, 27, 28]
        results['confidence'] = np.mean([landmarks[i].visibility for i in key_landmarks])
        
        # Form feedback
        results['feedback'] = []
        if front_knee_angle < 160:
            results['feedback'].append("Straighten front leg")
        if back_knee_angle < 160:
            results['feedback'].append("Straighten back leg")
        
        # Draw annotations
        if draw_frame is not None:
            self._draw_annotations(draw_frame, hip_center, floor_level, results)
        
        return results
    
    def _auto_calibrate(self, landmarks, image_height, assumed_height_cm=135):
        """Auto-calibrate using person's height"""
        nose_y = landmarks[0].y * image_height
        left_ankle_y = landmarks[27].y * image_height
        right_ankle_y = landmarks[28].y * image_height
        avg_ankle_y = (left_ankle_y + right_ankle_y) / 2
        
        person_height_pixels = avg_ankle_y - nose_y
        if person_height_pixels > 0:
            self.calibration_factor = assumed_height_cm / person_height_pixels
            self.reference_height = person_height_pixels
    
    def _draw_annotations(self, frame, hip_center, floor_level, results):
        """Draw measurements on frame"""
        # Floor line
        cv2.line(frame, (0, int(floor_level)), (frame.shape[1], int(floor_level)),
                (100, 100, 255), 2, cv2.LINE_AA)
        
        # Hip to floor line
        cv2.line(frame, (int(hip_center[0]), int(hip_center[1])),
                (int(hip_center[0]), int(floor_level)),
                (0, 255, 255), 2, cv2.LINE_AA)
        
        # Display metrics
        y = 30
        metrics = [
            f"Split Progress: {results['primary_metric']:.1f}%",
            f"Hip Opening: {results['hip_opening_angle']:.1f}",
        ]
        
        if 'hip_to_floor_cm' in results:
            metrics.append(f"Hip to Floor: {results['hip_to_floor_cm']:.1f} cm")
        
        for text in metrics:
            cv2.putText(frame, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.7, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX,
                       0.7, (122, 155, 118), 1, cv2.LINE_AA)
            y += 30


class ForwardFoldAnalyzer(PoseAnalyzer):
    """Analyzes forward fold (standing or seated)"""
    
    def __init__(self, calibration_factor=None):
        self.calibration_factor = calibration_factor
        self.name = "Forward Fold"
        self.unit = "°"
    
    def analyze(self, landmarks, image_width, image_height, draw_frame=None):
        """Analyze forward fold pose"""
        results = {'pose_type': 'forward_fold'}
        
        # Key points
        left_hip = (landmarks[23].x * image_width, landmarks[23].y * image_height)
        right_hip = (landmarks[24].x * image_width, landmarks[24].y * image_height)
        hip_center = ((left_hip[0] + right_hip[0]) / 2, (left_hip[1] + right_hip[1]) / 2)
        
        left_shoulder = (landmarks[11].x * image_width, landmarks[11].y * image_height)
        right_shoulder = (landmarks[12].x * image_width, landmarks[12].y * image_height)
        shoulder_center = ((left_shoulder[0] + right_shoulder[0]) / 2, 
                          (left_shoulder[1] + right_shoulder[1]) / 2)
        
        left_knee = (landmarks[25].x * image_width, landmarks[25].y * image_height)
        right_knee = (landmarks[26].x * image_width, landmarks[26].y * image_height)
        knee_center = ((left_knee[0] + right_knee[0]) / 2, (left_knee[1] + right_knee[1]) / 2)
        
        left_ankle = (landmarks[27].x * image_width, landmarks[27].y * image_height)
        right_ankle = (landmarks[28].x * image_width, landmarks[28].y * image_height)
        ankle_center = ((left_ankle[0] + right_ankle[0]) / 2, (left_ankle[1] + right_ankle[1]) / 2)
        
        # Torso angle (hip to shoulder relative to vertical)
        vertical_ref = (hip_center[0], 0)  # Point directly above hip
        torso_angle = self.calculate_angle(vertical_ref, hip_center, shoulder_center)
        
        # Hip flexion angle (torso to legs)
        hip_flexion = self.calculate_angle(shoulder_center, hip_center, knee_center)
        
        # Hand to floor distance (if hands visible)
        left_wrist = (landmarks[15].x * image_width, landmarks[15].y * image_height)
        right_wrist = (landmarks[16].x * image_width, landmarks[16].y * image_height)
        wrist_center = ((left_wrist[0] + right_wrist[0]) / 2, (left_wrist[1] + right_wrist[1]) / 2)
        
        floor_level = max(left_ankle[1], right_ankle[1])
        hands_to_floor_px = floor_level - wrist_center[1]
        
        # Flexibility score (0-100%)
        # Perfect forward fold: torso parallel to legs (hip_flexion near 0°)
        flexibility_score = max(0, 100 - (hip_flexion / 180.0 * 100))
        
        results['primary_metric'] = hip_flexion
        results['torso_angle'] = torso_angle
        results['hip_flexion'] = hip_flexion
        results['flexibility_score'] = flexibility_score
        results['hands_to_floor_px'] = hands_to_floor_px
        
        # Confidence
        key_landmarks = [11, 12, 23, 24, 25, 26]
        results['confidence'] = np.mean([landmarks[i].visibility for i in key_landmarks])
        
        results['feedback'] = []
        if hip_flexion > 45:
            results['feedback'].append("Bend deeper from hips")
        if hands_to_floor_px > 50:
            results['feedback'].append("Reach closer to floor")
        
        if draw_frame is not None:
            self._draw_annotations(draw_frame, shoulder_center, hip_center, 
                                 knee_center, wrist_center, floor_level, results)
        
        return results
    
    def _draw_annotations(self, frame, shoulder, hip, knee, wrist, floor, results):
        """Draw measurements"""
        # Spine line
        cv2.line(frame, (int(shoulder[0]), int(shoulder[1])),
                (int(hip[0]), int(hip[1])), (0, 255, 0), 2, cv2.LINE_AA)
        
        # Display
        y = 30
        metrics = [
            f"Hip Flexion: {results['hip_flexion']:.1f}",
            f"Flexibility: {results['flexibility_score']:.1f}%"
        ]
        
        for text in metrics:
            cv2.putText(frame, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX,
                       0.7, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX,
                       0.7, (122, 155, 118), 1, cv2.LINE_AA)
            y += 30


class MultiPoseAnalyzer:
    """
    Main analyzer that can switch between different pose types
    Usage:
        analyzer = MultiPoseAnalyzer()
        analyzer.set_pose('front_split')
        results = analyzer.analyze(landmarks, width, height, frame)
    """
    
    def __init__(self):
        self.analyzers = {
            'front_split': FrontSplitAnalyzer(),
            'forward_fold': ForwardFoldAnalyzer(),
        }
        self.current_pose = 'front_split'
    
    def set_pose(self, pose_name):
        """Change the active pose type"""
        if pose_name in self.analyzers:
            self.current_pose = pose_name
        else:
            raise ValueError(f"Unknown pose: {pose_name}. Available: {list(self.analyzers.keys())}")
    
    def get_available_poses(self):
        """Return list of available pose types"""
        return list(self.analyzers.keys())
    
    def get_pose_name(self):
        """Get current pose name"""
        return self.analyzers[self.current_pose].name
    
    def get_metric_unit(self):
        """Get unit for current pose's primary metric"""
        return self.analyzers[self.current_pose].unit
    
    def analyze(self, landmarks, image_width, image_height, draw_frame=None):
        """Analyze current pose"""
        return self.analyzers[self.current_pose].analyze(
            landmarks, image_width, image_height, draw_frame
        )
    
    def calculate_angle(self, a, b, c):
        """Convenience method for simple angle calculations"""
        return PoseAnalyzer.calculate_angle(a, b, c)