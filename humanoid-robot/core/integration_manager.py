"""
Integration Manager - Connects all modules like human sensory organs
Coordinates vision, audio, motion, sensors, and learning systems
"""

import threading
import queue
import time
from typing import Dict, List, Optional

from modules.vision.complete_vision import CompleteVisionSystem
from modules.speech.complete_audio import CompleteAudioSystem
from modules.llm.llm_processor import LLMProcessor
from modules.motion.motion_controller import MotionController
from modules.sensors.sensor_manager import SensorManager
from modules.learning.adaptive_learner import AdaptiveLearner
from modules.learning.lstm_rl import ReinforcementLearner
from modules.speech.pronunciation_scorer import PronunciationScorer
from utils.database import RobotDatabase
from utils.network_manager import NetworkManager
from config import Config

class IntegrationManager:
    """Main integration manager - coordinates all systems"""
    
    def __init__(self):
        """Initialize all systems"""
        self.config = Config()
        self.running = False
        
        # Initialize databases
        self.local_db = RobotDatabase()
        
        # Initialize network manager
        self.network_manager = NetworkManager(
            server_url=self.config.get('SERVER_URL', 'http://localhost:8000')
        )
        self.network_manager.start_monitoring()
        
        # Message queues
        self.vision_queue = queue.Queue()
        self.audio_queue = queue.Queue()
        self.llm_queue = queue.Queue()
        self.motion_queue = queue.Queue()
        self.sensor_queue = queue.Queue()
        self.learning_queue = queue.Queue()
        
        # Initialize modules
        self.vision_system = CompleteVisionSystem(self.config)
        self.audio_system = CompleteAudioSystem(self.config, self.network_manager)
        self.llm_processor = LLMProcessor(self.llm_queue, self.config)
        self.motion_controller = MotionController(self.motion_queue, self.config)
        self.sensor_manager = SensorManager(self.sensor_queue, self.config)
        self.adaptive_learner = AdaptiveLearner()
        self.rl_learner = ReinforcementLearner()
        self.pronunciation_scorer = PronunciationScorer()
        
        # Current state
        self.current_student = None
        self.current_session = None
        self.current_context = {}
        
        # Priority system
        self.priority_levels = {
            'emergency': 5,
            'motion': 4,
            'speech': 3,
            'vision': 2,
            'learning': 1
        }
    
    def start(self):
        """Start all systems"""
        self.running = True
        
        # Start all modules in separate threads
        threads = [
            threading.Thread(target=self.vision_system.run, args=(self.vision_queue,), daemon=True),
            threading.Thread(target=self.audio_system.run, args=(self.audio_queue,), daemon=True),
            threading.Thread(target=self.llm_processor.run, daemon=True),
            threading.Thread(target=self.motion_controller.run, daemon=True),
            threading.Thread(target=self.sensor_manager.run, daemon=True),
            threading.Thread(target=self._main_loop, daemon=True),
            threading.Thread(target=self._sync_loop, daemon=True)
        ]
        
        for thread in threads:
            thread.start()
        
        print("ANU 6.0 Integration Manager started")
        print("All systems operational")
        
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop()
    
    def _main_loop(self):
        """Main decision-making loop"""
        while self.running:
            tasks = []
            
            # Check for emergencies (sensors)
            if not self.sensor_queue.empty():
                sensor_data = self.sensor_queue.get()
                if self._is_emergency(sensor_data):
                    self._handle_emergency(sensor_data)
                    continue
                tasks.append(('sensor', sensor_data))
            
            # Check for speech input
            if not self.audio_queue.empty():
                speech_data = self.audio_queue.get()
                tasks.append(('speech', speech_data))
            
            # Check for vision input
            if not self.vision_queue.empty():
                vision_data = self.vision_queue.get()
                tasks.append(('vision', vision_data))
            
            # Process tasks by priority
            if tasks:
                tasks.sort(key=lambda x: self.priority_levels.get(x[0], 0), reverse=True)
                
                for task_type, task_data in tasks:
                    self._process_task(task_type, task_data)
            
            time.sleep(0.01)
    
    def _process_task(self, task_type: str, task_data: Dict):
        """Process different types of tasks"""
        if task_type == 'speech':
            self._process_speech(task_data)
        elif task_type == 'vision':
            self._process_vision(task_data)
        elif task_type == 'sensor':
            self._process_sensor(task_data)
    
    def _process_speech(self, speech_data: Dict):
        """Process speech input"""
        text = speech_data.get('text', '')
        confidence = speech_data.get('confidence', 0)
        
        if confidence < self.config.MIN_CONFIDENCE:
            return
        
        # Check if it's a command
        if self._is_command(text):
            self._handle_command(text)
        else:
            # Process as learning interaction
            self._handle_learning_interaction(text, speech_data)
    
    def _process_vision(self, vision_data: Dict):
        """Process vision input"""
        data = vision_data.get('data', {})
        
        # Handle face recognition
        faces = data.get('faces', [])
        for face in faces:
            if face.get('recognized'):
                student_id = face.get('student_id')
                if student_id and student_id != self.current_student:
                    self._greet_student(student_id, face.get('name'))
                    self.current_student = student_id
                    self._start_session(student_id)
        
        # Handle attention detection
        attention = data.get('attention', [])
        for att in attention:
            if not att.get('attention'):
                # Student not paying attention
                self.audio_system.speak("Please look at me, I'm here to help you learn!")
    
    def _process_sensor(self, sensor_data: Dict):
        """Process sensor data"""
        # Update context
        self.current_context.update({
            'distance': sensor_data.get('distance', 0),
            'temperature': sensor_data.get('temperature', 0),
            'motion_detected': sensor_data.get('motion_detected', False)
        })
    
    def _handle_learning_interaction(self, text: str, speech_data: Dict):
        """Handle learning interaction with pronunciation scoring"""
        if not self.current_student:
            self.audio_system.speak("Hello! Please introduce yourself so we can start learning.")
            return
        
        # Get target phrase for current lesson
        target_phrase = self._get_current_target_phrase()
        
        if target_phrase:
            # Score pronunciation
            target_phonemes = self.pronunciation_scorer.extract_phonemes(target_phrase)
            student_phonemes = self.pronunciation_scorer.extract_phonemes(text)
            alignment = self.pronunciation_scorer.align_phonemes(student_phonemes, target_phonemes)
            
            score_result = self.pronunciation_scorer.calculate_pronunciation_score(
                student_phonemes, target_phonemes, alignment
            )
            
            # Save pronunciation record
            if self.current_session:
                self.local_db.save_pronunciation(
                    self.current_student,
                    self.current_session,
                    target_phrase,
                    target_phonemes,
                    student_phonemes,
                    score_result['score'],
                    score_result['errors']
                )
            
            # Generate feedback
            feedback = score_result['feedback']
            self.audio_system.speak(feedback)
            
            # Update progress
            self.adaptive_learner.update_progress(
                self.current_student,
                self._get_current_lesson_id(),
                score_result['score']
            )
            
            # Use RL to decide next action
            student_data = self.adaptive_learner.get_student_stats(self.current_student)
            action = self.rl_learner.select_action(
                self.rl_learner.get_state_vector(student_data),
                training=True
            )
            
            # Execute action
            self._execute_rl_action(action)
        
        # Process with LLM for general conversation
        context = self._get_current_context()
        response = self.llm_processor.process_query(text, context, 
                                                    use_online=self.network_manager.is_online)
        
        if response:
            self.audio_system.speak(response)
            self.motion_controller.execute_command({'action': 'gesture', 'gesture': 'nod'})
    
    def _greet_student(self, student_id: str, name: str):
        """Greet recognized student"""
        greeting = f"Hello {name}! Nice to see you again. Ready to learn?"
        self.audio_system.speak(greeting)
        self.motion_controller.execute_command({'action': 'gesture', 'gesture': 'wave'})
    
    def _start_session(self, student_id: str):
        """Start learning session"""
        self.current_session = self.local_db.create_session(student_id, 'interactive')
        self.current_student = student_id
        
        # Get recommended lesson
        lesson = self.adaptive_learner.get_next_lesson(student_id)
        self.current_context['current_lesson'] = lesson
    
    def _is_emergency(self, sensor_data: Dict) -> bool:
        """Check if emergency situation"""
        return (sensor_data.get('obstacle_too_close', False) or
                sensor_data.get('temperature_high', False))
    
    def _handle_emergency(self, emergency_data: Dict):
        """Handle emergency"""
        print(f"EMERGENCY: {emergency_data}")
        self.motion_controller.emergency_stop()
        self.audio_system.speak("Emergency situation detected. Stopping all movement.")
    
    def _is_command(self, text: str) -> bool:
        """Check if text is a command"""
        commands = ['stop', 'start', 'help', 'repeat', 'next', 'previous']
        return any(cmd in text.lower() for cmd in commands)
    
    def _handle_command(self, command: str):
        """Handle robot commands"""
        cmd_lower = command.lower()
        
        if 'stop' in cmd_lower:
            self.motion_controller.stop_motors()
            self.audio_system.speak("Stopping movement.")
        elif 'help' in cmd_lower:
            self.audio_system.speak("I'm here to help you learn English. Just speak to me!")
        elif 'repeat' in cmd_lower:
            # Repeat last phrase
            pass  # Implement repeat logic
    
    def _get_current_target_phrase(self) -> Optional[str]:
        """Get target phrase for current lesson"""
        lesson = self.current_context.get('current_lesson', {})
        return lesson.get('target_phrase', None)
    
    def _get_current_lesson_id(self) -> str:
        """Get current lesson ID"""
        return self.current_context.get('current_lesson', {}).get('lesson_id', 'default')
    
    def _get_current_context(self) -> Dict:
        """Get current context for LLM"""
        return {
            'student_id': self.current_student,
            'session_id': self.current_session,
            'time': time.strftime("%H:%M"),
            'context': self.current_context
        }
    
    def _execute_rl_action(self, action: int):
        """Execute RL action"""
        action_desc = self.rl_learner.get_action_description(action)
        
        if action_desc == 'increase_difficulty':
            # Increase lesson difficulty
            pass
        elif action_desc == 'decrease_difficulty':
            # Decrease lesson difficulty
            pass
        elif action_desc == 'repeat_lesson':
            self.audio_system.speak("Let's practice this again.")
        elif action_desc == 'change_topic':
            # Change lesson topic
            pass
    
    def _sync_loop(self):
        """Background sync loop"""
        while self.running:
            if self.network_manager.is_online:
                # Sync queued data
                self.network_manager.sync_queue_to_server()
                
                # Sync current progress
                if self.current_student:
                    stats = self.adaptive_learner.get_student_stats(self.current_student)
                    self.network_manager.sync_data({
                        'robot_id': 'robot_001',
                        'progress': {
                            'student_id': self.current_student,
                            'pronunciation_score': stats.get('avg_pronunciation', 0)
                        }
                    })
            
            time.sleep(60)  # Sync every minute
    
    def stop(self):
        """Stop all systems"""
        self.running = False
        self.vision_system.stop()
        self.audio_system.stop()
        self.llm_processor.stop()
        self.motion_controller.stop()
        self.sensor_manager.stop()
        self.network_manager.stop()
        print("ANU 6.0 stopped")

if __name__ == "__main__":
    manager = IntegrationManager()
    manager.start()

