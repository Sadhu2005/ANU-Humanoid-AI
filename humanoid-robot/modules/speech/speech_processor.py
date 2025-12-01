import threading
import queue
import json
import os
import pyaudio
import vosk
from utils.tts import TextToSpeech

class SpeechProcessor:
    def __init__(self, output_queue, config):
        self.output_queue = output_queue
        self.config = config
        self.running = False
        self.tts_available = False
        
        try:
            self.audio = pyaudio.PyAudio()
        except Exception as e:
            print(f"Warning: Could not initialize audio: {e}")
            self.audio = None
        
        # Initialize Vosk model with error handling
        try:
            if os.path.exists(self.config.VOSK_MODEL_PATH):
                self.vosk_model = vosk.Model(self.config.VOSK_MODEL_PATH)
                self.vosk_available = True
            else:
                print(f"Warning: Vosk model not found at {self.config.VOSK_MODEL_PATH}")
                self.vosk_model = None
                self.vosk_available = False
        except Exception as e:
            print(f"Warning: Could not load Vosk model: {e}")
            self.vosk_model = None
            self.vosk_available = False
        
        # Initialize Silero VAD with error handling
        try:
            from silero_vad import load_silero_vad, apply_silero_vad
            if os.path.exists(self.config.SILERO_VAD_PATH):
                self.vad_model = load_silero_vad(self.config.SILERO_VAD_PATH)
                self.apply_vad = apply_silero_vad
                self.vad_available = True
            else:
                print(f"Warning: Silero VAD model not found at {self.config.SILERO_VAD_PATH}")
                self.vad_model = None
                self.vad_available = False
        except Exception as e:
            print(f"Warning: Could not load Silero VAD: {e}")
            self.vad_model = None
            self.vad_available = False
            # Fallback: simple energy-based VAD
            self.apply_vad = self._simple_vad
        
        # Initialize TTS
        try:
            self.tts_engine = TextToSpeech()
            self.tts_available = self.tts_engine.tts_available
        except Exception as e:
            print(f"Warning: Could not initialize TTS: {e}")
            self.tts_engine = None
            self.tts_available = False
        
        # Audio settings
        self.rate = 16000
        self.chunk_size = 8000
    
    def _simple_vad(self, model, data):
        """Simple energy-based VAD fallback"""
        import numpy as np
        audio_data = np.frombuffer(data, dtype=np.int16)
        energy = np.abs(audio_data).mean()
        return energy > 1000  # Threshold for speech detection
        
    def run(self):
        """Run speech processing in a separate thread"""
        if not self.audio or not self.vosk_available:
            print("Speech processor cannot start: missing audio or Vosk model")
            return
        
        self.running = True
        stream = None
        
        try:
            # Start audio stream
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            rec = vosk.KaldiRecognizer(self.vosk_model, self.rate)
            
            print("Speech processor started. Listening...")
            while self.running:
                try:
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                    
                    # Check if speech is detected using VAD
                    if self.apply_vad(self.vad_model, data) if self.vad_available else True:
                        if rec.AcceptWaveform(data):
                            result = json.loads(rec.Result())
                            if result.get('text'):
                                # Add to output queue
                                self.output_queue.put({
                                    'type': 'speech',
                                    'text': result['text'],
                                    'confidence': result.get('confidence', 0.5)
                                })
                except Exception as e:
                    print(f"Error in speech processing loop: {e}")
                    continue
        
        except Exception as e:
            print(f"Error starting speech processor: {e}")
        finally:
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                except:
                    pass
    
    def speak(self, text):
        """Convert text to speech"""
        if self.tts_available and self.tts_engine:
            try:
                self.tts_engine.speak(text)
            except Exception as e:
                print(f"Error in TTS: {e}")
                print(f"[TTS] {text}")  # Fallback
        else:
            print(f"[TTS] {text}")  # Fallback to console
    
    def stop(self):
        """Stop speech processing"""
        self.running = False
        if self.audio:
            try:
                self.audio.terminate()
            except:
                pass