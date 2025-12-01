"""
Complete Computer Vision Implementation for ANU 6.0
Object Detection, Face Recognition, and Environmental Awareness
"""

import cv2
import numpy as np
import face_recognition
from ultralytics import YOLO
import pickle
import os
import time
import threading
from typing import List, Dict, Optional, Tuple

class CompleteVisionSystem:
    """Complete vision system with object detection and face recognition"""
    
    def __init__(self, config):
        """
        Initialize vision system
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.running = False
        
        # Initialize camera
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            print("Warning: Could not open camera")
        
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.camera.set(cv2.CAP_PROP_FPS, 30)
        
        # Load face database
        self.known_faces = self._load_face_database()
        
        # Load YOLO model for object detection
        try:
            self.object_model = YOLO(self.config.OBJECT_DETECTION_MODEL)
            self.object_detection_enabled = True
        except Exception as e:
            print(f"Warning: Could not load YOLO model: {e}")
            self.object_model = None
            self.object_detection_enabled = False
        
        # Vision processing settings
        self.face_detection_interval = 5  # Process faces every 5 frames
        self.object_detection_interval = 10  # Process objects every 10 frames
        self.frame_count = 0
        
        # Threading
        self.processing_thread = None
        self.output_queue = None
    
    def _load_face_database(self) -> Dict:
        """Load known faces from database"""
        known_faces = {
            'encodings': [],
            'names': [],
            'student_ids': []
        }
        
        database_path = os.path.join(self.config.FACE_DATABASE_PATH, 'faces.pkl')
        
        if os.path.exists(database_path):
            try:
                with open(database_path, 'rb') as f:
                    data = pickle.load(f)
                    known_faces = data
            except Exception as e:
                print(f"Error loading face database: {e}")
        
        return known_faces
    
    def _save_face_database(self):
        """Save face database"""
        os.makedirs(self.config.FACE_DATABASE_PATH, exist_ok=True)
        database_path = os.path.join(self.config.FACE_DATABASE_PATH, 'faces.pkl')
        
        try:
            with open(database_path, 'wb') as f:
                pickle.dump(self.known_faces, f)
        except Exception as e:
            print(f"Error saving face database: {e}")
    
    def add_face(self, image: np.ndarray, name: str, student_id: str) -> bool:
        """
        Add a new face to the database
        
        Args:
            image: Face image (RGB format)
            name: Person's name
            student_id: Student ID
        
        Returns:
            True if successful
        """
        try:
            # Find face locations
            face_locations = face_recognition.face_locations(
                image, model=self.config.FACE_RECOGNITION_MODEL
            )
            
            if not face_locations:
                print("No face found in image")
                return False
            
            # Get face encodings
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            if face_encodings:
                # Use first face
                encoding = face_encodings[0]
                
                self.known_faces['encodings'].append(encoding)
                self.known_faces['names'].append(name)
                self.known_faces['student_ids'].append(student_id)
                
                self._save_face_database()
                print(f"Added face for {name} (ID: {student_id})")
                return True
            
            return False
        
        except Exception as e:
            print(f"Error adding face: {e}")
            return False
    
    def detect_faces(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect and recognize faces in frame
        
        Args:
            frame: Input frame (BGR format)
        
        Returns:
            List of detected faces with recognition info
        """
        # Convert BGR to RGB
        rgb_frame = frame[:, :, ::-1]
        
        # Find face locations
        face_locations = face_recognition.face_locations(
            rgb_frame, model=self.config.FACE_RECOGNITION_MODEL
        )
        
        if not face_locations:
            return []
        
        # Get face encodings
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        faces = []
        for face_encoding, face_location in zip(face_encodings, face_locations):
            # Compare with known faces
            matches = face_recognition.compare_faces(
                self.known_faces['encodings'], face_encoding, tolerance=0.6
            )
            
            name = "Unknown"
            student_id = None
            confidence = 0.0
            
            if True in matches:
                # Find best match
                face_distances = face_recognition.face_distance(
                    self.known_faces['encodings'], face_encoding
                )
                best_match_index = np.argmin(face_distances)
                
                if matches[best_match_index]:
                    name = self.known_faces['names'][best_match_index]
                    student_id = self.known_faces['student_ids'][best_match_index]
                    confidence = 1.0 - face_distances[best_match_index]
            
            faces.append({
                'name': name,
                'student_id': student_id,
                'confidence': float(confidence),
                'location': face_location,  # (top, right, bottom, left)
                'recognized': name != "Unknown"
            })
        
        return faces
    
    def detect_objects(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect objects in frame using YOLO
        
        Args:
            frame: Input frame (BGR format)
        
        Returns:
            List of detected objects
        """
        if not self.object_detection_enabled or not self.object_model:
            return []
        
        try:
            results = self.object_model(frame, verbose=False, conf=0.5)
            
            objects = []
            for result in results:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    label = result.names[class_id]
                    
                    # Get bounding box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    
                    objects.append({
                        'label': label,
                        'confidence': confidence,
                        'bbox': [x1, y1, x2, y2],
                        'center': [(x1 + x2) / 2, (y1 + y2) / 2]
                    })
            
            return objects
        
        except Exception as e:
            print(f"Error in object detection: {e}")
            return []
    
    def detect_attention(self, frame: np.ndarray, face_location: Tuple) -> Dict:
        """
        Detect if person is paying attention (simplified)
        
        Args:
            frame: Input frame
            face_location: Face location tuple
        
        Returns:
            Attention metrics
        """
        top, right, bottom, left = face_location
        
        # Extract face region
        face_region = frame[top:bottom, left:right]
        
        if face_region.size == 0:
            return {'attention': False, 'confidence': 0.0}
        
        # Simple heuristic: check if face is centered and visible
        frame_center_x = frame.shape[1] / 2
        face_center_x = (left + right) / 2
        
        # Calculate distance from center
        distance_from_center = abs(face_center_x - frame_center_x) / frame_center_x
        
        # Attention if face is reasonably centered
        attention = distance_from_center < 0.3
        
        return {
            'attention': attention,
            'confidence': 1.0 - min(distance_from_center, 1.0),
            'face_center': [face_center_x, (top + bottom) / 2]
        }
    
    def process_frame(self, frame: np.ndarray) -> Dict:
        """
        Process a single frame (complete vision pipeline)
        
        Args:
            frame: Input frame
        
        Returns:
            Complete vision analysis
        """
        self.frame_count += 1
        
        result = {
            'faces': [],
            'objects': [],
            'attention': [],
            'timestamp': time.time(),
            'frame_number': self.frame_count
        }
        
        # Face detection (every N frames)
        if self.frame_count % self.face_detection_interval == 0:
            faces = self.detect_faces(frame)
            result['faces'] = faces
            
            # Check attention for each face
            for face in faces:
                if face['recognized']:
                    attention = self.detect_attention(frame, face['location'])
                    attention['student_id'] = face['student_id']
                    attention['name'] = face['name']
                    result['attention'].append(attention)
        
        # Object detection (every N frames)
        if self.frame_count % self.object_detection_interval == 0:
            objects = self.detect_objects(frame)
            result['objects'] = objects
        
        return result
    
    def run(self, output_queue):
        """
        Run vision processing in separate thread
        
        Args:
            output_queue: Queue for output data
        """
        self.output_queue = output_queue
        self.running = True
        
        print("Complete Vision System started")
        
        while self.running:
            ret, frame = self.camera.read()
            if not ret:
                time.sleep(0.1)
                continue
            
            # Process frame
            try:
                vision_data = self.process_frame(frame)
                
                # Send to output queue if there's meaningful data
                if vision_data['faces'] or vision_data['objects'] or vision_data['attention']:
                    self.output_queue.put({
                        'type': 'vision',
                        'data': vision_data
                    })
            
            except Exception as e:
                print(f"Error processing frame: {e}")
                continue
            
            # Control processing rate
            time.sleep(1.0 / self.config.VISION_PROCESSING_FPS)
    
    def stop(self):
        """Stop vision system"""
        self.running = False
        if self.camera:
            self.camera.release()
    
    def get_detected_people(self) -> List[str]:
        """Get list of currently detected people (student IDs)"""
        # This would typically use the most recent vision results
        # For now, return empty list
        return []

