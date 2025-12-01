"""
ANU 6.0 Main Entry Point
Uses Integration Manager to coordinate all systems
"""

from core.integration_manager import IntegrationManager

if __name__ == "__main__":
    # Create and start integration manager
    robot = IntegrationManager()
    robot.start()
    def __init__(self):
        self.config = Config()
        self.running = False
        
        # Initialize message queues
        self.speech_queue = queue.Queue()
        self.vision_queue = queue.Queue()
        self.llm_queue = queue.Queue()
        self.motion_queue = queue.Queue()
        self.sensor_queue = queue.Queue()
        
        # Initialize modules
        self.speech_processor = SpeechProcessor(self.speech_queue, self.config)
        self.vision_processor = VisionProcessor(self.vision_queue, self.config)
        self.llm_processor = LLMProcessor(self.llm_queue, self.config)
        self.motion_controller = MotionController(self.motion_queue, self.config)
        self.sensor_manager = SensorManager(self.sensor_queue, self.config)
        
        # Priority system
        self.priority_levels = {
            'emergency': 5,    # Safety critical
            'motion': 4,       # Movement commands
            'query': 3,        # User questions
            'sensing': 2,      # Sensor data
            'idle': 1          # Background tasks
        }
        
    def start(self):
        """Start all modules"""
        self.running = True
        
        # Start modules in separate threads
        threads = [
            threading.Thread(target=self.speech_processor.run),
            threading.Thread(target=self.vision_processor.run),
            threading.Thread(target=self.llm_processor.run),
            threading.Thread(target=self.motion_controller.run),
            threading.Thread(target=self.sensor_manager.run),
            threading.Thread(target=self.main_loop)
        ]
        
        for thread in threads:
            thread.daemon = True
            thread.start()
        
        print("Humanoid Robot started. Press Ctrl+C to stop.")
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop()
    
    def main_loop(self):
        """Main decision-making loop"""
        while self.running:
            # Check for highest priority task
            tasks = []
            
            # Check sensor queue for emergencies
            if not self.sensor_queue.empty():
                sensor_data = self.sensor_queue.get()
                if self.is_emergency(sensor_data):
                    self.handle_emergency(sensor_data)
                    continue
            
            # Check for motion commands
            if not self.motion_queue.empty():
                tasks.append(('motion', self.motion_queue.get()))
            
            # Check for speech input
            if not self.speech_queue.empty():
                tasks.append(('speech', self.speech_queue.get()))
            
            # Check for vision input
            if not self.vision_queue.empty():
                tasks.append(('vision', self.vision_queue.get()))
            
            # Process tasks by priority
            if tasks:
                # Sort by priority
                tasks.sort(key=lambda x: self.priority_levels.get(x[0], 0), reverse=True)
                
                for task_type, task_data in tasks:
                    self.process_task(task_type, task_data)
            
            time.sleep(0.01)  # Prevent CPU overload
    
    def is_emergency(self, sensor_data):
        """Check if sensor data indicates an emergency"""
        # Implement emergency detection logic
        if sensor_data.get('obstacle_too_close', False):
            return True
        if sensor_data.get('temperature_high', False):
            return True
        return False
    
    def handle_emergency(self, emergency_data):
        """Handle emergency situations"""
        print(f"EMERGENCY: {emergency_data}")
        # Stop all motion immediately
        self.motion_controller.emergency_stop()
        
        # Notify user if possible
        if self.speech_processor.tts_available:
            self.speech_processor.speak("Emergency situation detected. Stopping all movement.")
    
    def process_task(self, task_type, task_data):
        """Process different types of tasks"""
        if task_type == 'speech':
            self.process_speech(task_data)
        elif task_type == 'vision':
            self.process_vision(task_data)
        elif task_type == 'motion':
            self.process_motion(task_data)
    
    def process_speech(self, speech_data):
        """Process speech commands"""
        text = speech_data.get('text', '')
        confidence = speech_data.get('confidence', 0)
        
        if confidence > self.config.MIN_CONFIDENCE:
            # Check if this is a motion command
            motion_command = self.parse_motion_command(text)
            if motion_command:
                self.motion_queue.put(motion_command)
            else:
                # Send to LLM for processing
                self.llm_queue.put({
                    'type': 'query',
                    'text': text,
                    'context': self.get_current_context()
                })
    
    def process_vision(self, vision_data):
        """Process vision data"""
        # Handle face recognition
        if 'faces' in vision_data:
            for face in vision_data['faces']:
                if face['recognized']:
                    # Greet known person
                    greeting = f"Hello {face['name']}, nice to see you again."
                    self.speech_processor.speak(greeting)
                else:
                    # Ask for introduction
                    self.speech_processor.speak("I don't recognize you. Could you please tell me your name?")
        
        # Handle object detection
        if 'objects' in vision_data:
            # Process detected objects
            pass
    
    def process_motion(self, motion_command):
        """Process motion commands"""
        self.motion_controller.execute_command(motion_command)
    
    def parse_motion_command(self, text):
        """Convert natural language to motion commands"""
        text_lower = text.lower()
        
        # Simple command parsing - expand this with more sophisticated NLP
        if any(word in text_lower for word in ['move', 'go', 'walk']):
            if 'forward' in text_lower:
                return {'action': 'move', 'direction': 'forward', 'distance': 50}
            elif 'backward' in text_lower:
                return {'action': 'move', 'direction': 'backward', 'distance': 50}
            elif 'left' in text_lower:
                return {'action': 'move', 'direction': 'left', 'angle': 45}
            elif 'right' in text_lower:
                return {'action': 'move', 'direction': 'right', 'angle': 45}
        
        elif any(word in text_lower for word in ['stop', 'halt']):
            return {'action': 'stop'}
        
        elif any(word in text_lower for word in ['wave', 'hello']):
            return {'action': 'gesture', 'gesture': 'wave'}
        
        return None
    
    def get_current_context(self):
        """Get current context for LLM"""
        return {
            'location': 'unknown',  # Could integrate with sensors
            'people_present': self.vision_processor.get_detected_people(),
            'time': time.strftime("%H:%M"),
            'battery_level': self.sensor_manager.get_battery_level()
        }
    
    def stop(self):
        """Stop all modules gracefully"""
        self.running = False
        self.speech_processor.stop()
        self.vision_processor.stop()
        self.llm_processor.stop()
        self.motion_controller.stop()
        self.sensor_manager.stop()
        print("Humanoid Robot stopped.")

if __name__ == "__main__":
    robot = HumanoidRobot()
    robot.start()