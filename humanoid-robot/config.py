import os

class Config:
    # Hardware settings
    PCA9685_ADDRESS = 0x40
    SERVO_COUNT = 17
    MOTOR_PINS = {
        'front_left': [1, 2],
        'front_right': [3, 4],
        'back_left': [5, 6],
        'back_right': [7, 8]
    }
    
    # Speech settings
    VOSK_MODEL_PATH = os.path.join('models', 'vosk', 'indian-english')
    MIN_CONFIDENCE = 0.7
    SILERO_VAD_PATH = os.path.join('models', 'silero_vad')
    
    # Vision settings
    FACE_RECOGNITION_MODEL = 'hog'  # Use 'cnn' for better accuracy but slower
    OBJECT_DETECTION_MODEL = 'yolov8n'
    FACE_DATABASE_PATH = os.path.join('data', 'faces')
    
    # LLM settings
    OFFLINE_LLM_PATH = os.path.join('models', 'llm', 'tinyllama-1.1b')
    ONLINE_LLM_PROVIDER = 'gemini'  # Options: gemini, perplexity, deepseek
    ONLINE_LLM_API_KEY = os.getenv('LLM_API_KEY', '')
    
    # Motion settings
    SERVO_RANGES = {
        'head_yaw': [0, 180],
        'head_pitch': [0, 180],
        # Define ranges for all 17 servos
    }
    
    # Sensor settings
    ULTRASONIC_PINS = {'trigger': 23, 'echo': 24}
    PIR_PINS = [25, 26]
    TEMP_SENSOR_PIN = 27
    
    # Performance settings
    VISION_PROCESSING_FPS = 5  # Lower FPS to reduce CPU load
    LLM_CONTEXT_LENGTH = 512   # Shorter context for faster processing
    
    # Server settings
    SERVER_URL = os.getenv('SERVER_URL', 'http://localhost:8000')
    ROBOT_ID = os.getenv('ROBOT_ID', 'robot_001')
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        return getattr(self, key, default)