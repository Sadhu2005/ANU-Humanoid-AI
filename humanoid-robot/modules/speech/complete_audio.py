"""
Complete Audio/Speech Implementation for ANU 6.0
Speech Recognition, TTS, and Audio Processing
"""

import pyaudio
import queue
import threading
import json
import numpy as np
import time
from typing import Optional, Dict, List

# Try to import speech recognition libraries
try:
    import vosk
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False

try:
    from silero_vad import load_silero_vad, apply_silero_vad
    SILERO_AVAILABLE = True
except ImportError:
    SILERO_AVAILABLE = False

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

from utils.tts import TextToSpeech
from utils.network_manager import NetworkManager

class CompleteAudioSystem:
    """Complete audio system with STT and TTS"""
    
    def __init__(self, config, network_manager: Optional[NetworkManager] = None):
        """
        Initialize audio system
        
        Args:
            config: Configuration object
            network_manager: Optional network manager for online features
        """
        self.config = config
        self.network_manager = network_manager
        self.running = False
        
        # Audio settings
        self.rate = 16000
        self.chunk_size = 8000
        self.channels = 1
        self.format = pyaudio.paInt16
        
        # Initialize audio
        try:
            self.audio = pyaudio.PyAudio()
        except Exception as e:
            print(f"Error initializing audio: {e}")
            self.audio = None
        
        # Initialize Vosk (offline)
        self.vosk_model = None
        self.vosk_recognizer = None
        if VOSK_AVAILABLE:
            try:
                import os
                if os.path.exists(self.config.VOSK_MODEL_PATH):
                    self.vosk_model = vosk.Model(self.config.VOSK_MODEL_PATH)
                    self.vosk_recognizer = vosk.KaldiRecognizer(
                        self.vosk_model, self.rate
                    )
                    self.offline_stt_available = True
                else:
                    print(f"Vosk model not found at {self.config.VOSK_MODEL_PATH}")
                    self.offline_stt_available = False
            except Exception as e:
                print(f"Error loading Vosk model: {e}")
                self.offline_stt_available = False
        else:
            self.offline_stt_available = False
        
        # Initialize Google Speech Recognition (online)
        if SPEECH_RECOGNITION_AVAILABLE:
            self.google_recognizer = sr.Recognizer()
            self.online_stt_available = True
        else:
            self.google_recognizer = None
            self.online_stt_available = False
        
        # Initialize VAD
        self.vad_model = None
        self.vad_available = False
        if SILERO_AVAILABLE:
            try:
                import os
                if os.path.exists(self.config.SILERO_VAD_PATH):
                    self.vad_model = load_silero_vad(self.config.SILERO_VAD_PATH)
                    self.apply_vad = apply_silero_vad
                    self.vad_available = True
                else:
                    self.vad_available = False
            except Exception as e:
                print(f"Error loading VAD: {e}")
                self.vad_available = False
        
        if not self.vad_available:
            # Fallback to simple energy-based VAD
            self.apply_vad = self._simple_vad
        
        # Initialize TTS
        try:
            self.tts_engine = TextToSpeech()
            self.tts_available = self.tts_engine.tts_available
        except Exception as e:
            print(f"Error initializing TTS: {e}")
            self.tts_engine = None
            self.tts_available = False
        
        # Audio queue
        self.audio_queue = queue.Queue()
        self.output_queue = None
    
    def _simple_vad(self, model, audio_data):
        """Simple energy-based VAD fallback"""
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        energy = np.abs(audio_array).mean()
        return energy > 1000  # Threshold
    
    def _recognize_offline(self, audio_data: bytes) -> Optional[Dict]:
        """Recognize speech using offline Vosk"""
        if not self.offline_stt_available or not self.vosk_recognizer:
            return None
        
        try:
            if self.vosk_recognizer.AcceptWaveform(audio_data):
                result = json.loads(self.vosk_recognizer.Result())
                if result.get('text'):
                    return {
                        'text': result['text'],
                        'confidence': result.get('confidence', 0.5),
                        'method': 'offline_vosk'
                    }
            else:
                # Partial result
                partial = json.loads(self.vosk_recognizer.PartialResult())
                if partial.get('partial'):
                    return {
                        'text': partial['partial'],
                        'confidence': 0.3,
                        'method': 'offline_vosk_partial'
                    }
        except Exception as e:
            print(f"Error in offline recognition: {e}")
        
        return None
    
    def _recognize_online(self, audio_data: bytes) -> Optional[Dict]:
        """Recognize speech using online Google STT"""
        if not self.online_stt_available or not self.network_manager or not self.network_manager.is_online:
            return None
        
        try:
            # Convert to AudioData format for speech_recognition
            audio_source = sr.AudioData(audio_data, self.rate, 2)
            text = self.google_recognizer.recognize_google(audio_source, language='en-IN')
            
            return {
                'text': text,
                'confidence': 0.9,  # Google doesn't provide confidence
                'method': 'online_google'
            }
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"Error with online recognition: {e}")
            return None
        except Exception as e:
            print(f"Error in online recognition: {e}")
            return None
    
    def recognize_speech(self, audio_data: bytes, prefer_offline: bool = True) -> Optional[Dict]:
        """
        Recognize speech (tries offline first, falls back to online)
        
        Args:
            audio_data: Audio data bytes
            prefer_offline: Whether to prefer offline recognition
        
        Returns:
            Recognition result or None
        """
        # Try offline first if available and preferred
        if prefer_offline and self.offline_stt_available:
            result = self._recognize_offline(audio_data)
            if result and result.get('confidence', 0) > self.config.MIN_CONFIDENCE:
                return result
        
        # Try online if offline failed or not preferred
        if self.online_stt_available and self.network_manager and self.network_manager.is_online:
            result = self._recognize_online(audio_data)
            if result:
                return result
        
        # Fallback to offline if online failed
        if not prefer_offline and self.offline_stt_available:
            result = self._recognize_offline(audio_data)
            if result:
                return result
        
        return None
    
    def run(self, output_queue):
        """
        Run audio processing in separate thread
        
        Args:
            output_queue: Queue for output data
        """
        if not self.audio:
            print("Audio system cannot start: audio not initialized")
            return
        
        self.output_queue = output_queue
        self.running = True
        
        # Start audio stream
        try:
            stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
        except Exception as e:
            print(f"Error opening audio stream: {e}")
            return
        
        print("Complete Audio System started. Listening...")
        
        audio_buffer = b''
        
        while self.running:
            try:
                # Read audio data
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                audio_buffer += data
                
                # Check for speech using VAD
                if self.apply_vad(self.vad_model, data) if self.vad_available else True:
                    # Accumulate audio until silence
                    if len(audio_buffer) >= self.rate * 2:  # 2 seconds max
                        # Try to recognize
                        result = self.recognize_speech(audio_buffer)
                        
                        if result and result.get('text'):
                            self.output_queue.put({
                                'type': 'speech',
                                'text': result['text'],
                                'confidence': result.get('confidence', 0.5),
                                'method': result.get('method', 'unknown')
                            })
                        
                        audio_buffer = b''
                else:
                    # No speech detected, clear buffer if too long
                    if len(audio_buffer) > self.rate * 3:
                        audio_buffer = b''
            
            except Exception as e:
                print(f"Error in audio processing: {e}")
                continue
        
        # Cleanup
        stream.stop_stream()
        stream.close()
    
    def speak(self, text: str, lang: str = 'en', slow: bool = False):
        """
        Convert text to speech
        
        Args:
            text: Text to speak
            lang: Language code
            slow: Whether to speak slowly
        """
        if self.tts_available and self.tts_engine:
            try:
                self.tts_engine.speak(text, lang=lang, slow=slow)
            except Exception as e:
                print(f"Error in TTS: {e}")
                print(f"[TTS] {text}")  # Fallback
        else:
            print(f"[TTS] {text}")  # Fallback to console
    
    def speak_bilingual(self, text_en: str, text_kn: str):
        """Speak in both English and Kannada"""
        if self.tts_engine:
            self.tts_engine.speak_bilingual(text_en, text_kn)
    
    def stop(self):
        """Stop audio system"""
        self.running = False
        if self.audio:
            try:
                self.audio.terminate()
            except:
                pass

