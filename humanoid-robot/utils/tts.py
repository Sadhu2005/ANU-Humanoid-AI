"""
Text-to-Speech utility module for ANU 6.0
Supports multiple TTS engines with fallback options
"""

import os
import platform

class TextToSpeech:
    """Text-to-Speech handler with multiple engine support"""
    
    def __init__(self, engine='auto'):
        """
        Initialize TTS engine
        
        Args:
            engine: 'auto', 'pyttsx3', 'gtts', 'espeak', or 'coqui'
        """
        self.engine_name = engine
        self.engine = None
        self.tts_available = False
        
        if engine == 'auto':
            # Try to find the best available engine
            self.engine_name = self._detect_best_engine()
        
        self._initialize_engine()
    
    def _detect_best_engine(self):
        """Detect the best available TTS engine"""
        # Try Coqui TTS first (best quality)
        try:
            from TTS.api import TTS
            return 'coqui'
        except ImportError:
            pass
        
        # Try pyttsx3 (offline, cross-platform)
        try:
            import pyttsx3
            return 'pyttsx3'
        except ImportError:
            pass
        
        # Try gTTS (online, requires internet)
        try:
            from gtts import gTTS
            return 'gtts'
        except ImportError:
            pass
        
        # Fallback to espeak (Linux)
        if platform.system() == 'Linux':
            return 'espeak'
        
        return 'pyttsx3'  # Default fallback
    
    def _initialize_engine(self):
        """Initialize the selected TTS engine"""
        try:
            if self.engine_name == 'pyttsx3':
                import pyttsx3
                self.engine = pyttsx3.init()
                self.tts_available = True
                
                # Configure voice properties
                if self.engine:
                    voices = self.engine.getProperty('voices')
                    if voices:
                        # Try to find a female voice (more friendly for education)
                        for voice in voices:
                            if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                                self.engine.setProperty('voice', voice.id)
                                break
                    
                    self.engine.setProperty('rate', 150)  # Speech rate
                    self.engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
            
            elif self.engine_name == 'gtts':
                from gtts import gTTS
                import pygame
                self.gtts = gTTS
                self.pygame = pygame
                pygame.mixer.init()
                self.tts_available = True
            
            elif self.engine_name == 'coqui':
                from TTS.api import TTS
                # Use a lightweight model for edge devices
                self.tts_model = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False)
                self.tts_available = True
            
            elif self.engine_name == 'espeak':
                # espeak is available via command line on Linux
                self.tts_available = True
            
            else:
                print(f"Warning: Unknown TTS engine '{self.engine_name}'")
                self.tts_available = False
        
        except Exception as e:
            print(f"Error initializing TTS engine '{self.engine_name}': {e}")
            self.tts_available = False
    
    def speak(self, text, lang='en', slow=False):
        """
        Convert text to speech and play it
        
        Args:
            text: Text to speak
            lang: Language code ('en' for English, 'kn' for Kannada)
            slow: Whether to speak slowly (for learning purposes)
        """
        if not self.tts_available:
            print(f"[TTS] {text}")  # Fallback to console output
            return
        
        try:
            if self.engine_name == 'pyttsx3':
                if self.engine:
                    self.engine.say(text)
                    self.engine.runAndWait()
            
            elif self.engine_name == 'gtts':
                tts = self.gtts(text=text, lang=lang, slow=slow)
                tts.save('/tmp/tts_output.mp3')
                self.pygame.mixer.music.load('/tmp/tts_output.mp3')
                self.pygame.mixer.music.play()
                while self.pygame.mixer.music.get_busy():
                    self.pygame.time.Clock().tick(10)
            
            elif self.engine_name == 'coqui':
                # Generate speech
                output_path = '/tmp/tts_output.wav'
                self.tts_model.tts_to_file(text=text, file_path=output_path)
                
                # Play audio
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(output_path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
            
            elif self.engine_name == 'espeak':
                # Use espeak command line
                speed = 150 if not slow else 100
                os.system(f'espeak -s {speed} "{text}"')
        
        except Exception as e:
            print(f"Error during TTS: {e}")
            print(f"[TTS] {text}")  # Fallback to console
    
    def speak_bilingual(self, text_en, text_kn):
        """
        Speak in both English and Kannada
        
        Args:
            text_en: English text
            text_kn: Kannada text
        """
        self.speak(text_en, lang='en')
        self.speak(text_kn, lang='kn')
    
    def set_rate(self, rate):
        """Set speech rate (words per minute)"""
        if self.engine_name == 'pyttsx3' and self.engine:
            self.engine.setProperty('rate', rate)
    
    def set_volume(self, volume):
        """Set volume (0.0 to 1.0)"""
        if self.engine_name == 'pyttsx3' and self.engine:
            self.engine.setProperty('volume', max(0.0, min(1.0, volume)))

