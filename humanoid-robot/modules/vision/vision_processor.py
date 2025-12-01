import threading
import time
import cv2
import face_recognition
from ultralytics import YOLO
import numpy as np
import os
import pickle

class VisionProcessor:
    def __init__(self, output_queue, config):
        self.output_queue = output_queue
        self.config = config
        self.running = False
        
        # Initialize camera
        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.camera.set(cv2.CAP_PROP_FPS, self.config.VISION_PROCESSING_FPS)
        
        # Load face database
        self.known_faces = self.load_face_database()
        
        # Load object detection model
        self.object_model = YOLO(self.config.OBJECT_DETECTION_MODEL)
        
    def load_face_database(self):
        """Load known faces from database"""
        known_faces = {'encodings': [], 'names': []}
        database_path = os.path.join(self.config.FACE_DATABASE_PATH, 'faces.pkl')
        
        if os.path.exists(database_path):
            with open(database_path, 'rb') as f:
                known_faces = pickle.load(f)
        
        return known_faces
    
    def save_face_database(self):
        """Save known faces to database"""
        os.makedirs(self.config.FACE_DATABASE_PATH, exist_ok=True)
        database_path = os.path.join(self.config.FACE_DATABASE_PATH, 'faces.pkl')
        
        with open(database_path, 'wb') as f:
            pickle.dump(self.known_faces, f)
    
    def add_face(self, image, name):
        """Add a new face to the database"""
        # Encode the face
        encodings = face_recognition.face_encodings(image)
        if encodings:
            self.known_faces['encodings'].append(encodings[0])
            self.known_faces['names'].append(name)
            self.save_face_database()
    
    def run(self):
        """Run vision processing in a separate thread"""
        if not self.camera or not self.camera.isOpened():
            print("Vision processor cannot start: camera not available")
            return
        
        self.running = True
        
        print("Vision processor started.")
        while self.running:
            try:
                ret, frame = self.camera.read()
                if not ret:
                    time.sleep(0.1)
                    continue
                
                # Process frame at reduced frequency to save CPU
                if int(time.time() * self.config.VISION_PROCESSING_FPS) % 2 == 0:
                    try:
                        # Detect faces
                        face_results = self.process_faces(frame)
                        
                        # Detect objects
                        object_results = self.process_objects(frame)
                        
                        # Send results to output queue if anything detected
                        if face_results.get('faces') or object_results.get('objects'):
                            self.output_queue.put({
                                'type': 'vision',
                                'faces': face_results.get('faces', []),
                                'objects': object_results.get('objects', []),
                                'timestamp': time.time()
                            })
                    except Exception as e:
                        print(f"Error processing vision frame: {e}")
                        continue
                
                # Sleep to control processing rate
                time.sleep(1 / self.config.VISION_PROCESSING_FPS)
            
            except Exception as e:
                print(f"Error in vision processing loop: {e}")
                time.sleep(1)  # Wait before retrying
    
    def process_faces(self, frame):
        """Process frame for face recognition"""
        # Convert to RGB (face_recognition uses RGB)
        rgb_frame = frame[:, :, ::-1]
        
        # Find faces
        face_locations = face_recognition.face_locations(
            rgb_frame, model=self.config.FACE_RECOGNITION_MODEL
        )
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        faces = []
        for face_encoding, face_location in zip(face_encodings, face_locations):
            # Compare with known faces
            matches = face_recognition.compare_faces(
                self.known_faces['encodings'], face_encoding
            )
            
            name = "Unknown"
            confidence = 0
            
            if True in matches:
                first_match_index = matches.index(True)
                name = self.known_faces['names'][first_match_index]
                confidence = face_recognition.face_distance(
                    [self.known_faces['encodings'][first_match_index]], 
                    face_encoding
                )[0]
                confidence = 1 - confidence  # Convert distance to confidence
            
            faces.append({
                'name': name,
                'confidence': confidence,
                'location': face_location,
                'recognized': name != "Unknown"
            })
        
        return {'faces': faces}
    
    def process_objects(self, frame):
        """Process frame for object detection"""
        results = self.object_model(frame, verbose=False)
        
        objects = []
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                label = result.names[class_id]
                
                objects.append({
                    'label': label,
                    'confidence': confidence,
                    'bbox': box.xyxy[0].tolist()
                })
        
        return {'objects': objects}
    
    def get_detected_people(self):
        """Get list of currently detected people"""
        # This would typically use the most recent vision results
        return []  # Implement based on your needs
    
    def stop(self):
        """Stop vision processing"""
        self.running = False
        self.camera.release()