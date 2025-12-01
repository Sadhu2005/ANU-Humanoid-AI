# ANU 6.0 - Artificial Neural Universe 🤖
<p align="center"><img src="https://via.placeholder.com/600x300/134e4a/f5f5f4?text=ANU+6.0" alt="ANU 6.0 Project Banner"></p>
<p align="center"><strong>An AI-powered humanoid robot designed to be a personalized mentor and an intelligent friend for rural students in India.</strong><br /><br />
<img src="https://img.shields.io/badge/Status-In%20Development-blue" alt="Status">
<img src="https://img.shields.io/badge/Python-3.9%2B-blueviolet" alt="Python Version">
<img src="https://img.shields.io/badge/Platform-Raspberry%20Pi%205-orange" alt="Platform">
<img src="https://img.shields.io/badge/License-MIT-green" alt="License">
</p>

## 🎯 Our Mission

To bridge the educational and digital divide for students in rural Karnataka by providing an accessible, engaging, and distraction-free AI learning companion. ANU 6.0 aims to build English fluency, foster confidence, and become a gateway to technology and information for students and their households.

*This project was initiated by the EvoBot Crew at the Coorg Institute of Technology, Ponnampet.*

### 🚀 Quick Start

- **New to the project?** → Open `Anu-website/index.html` in your browser for an interactive visual overview
- **Developer?** → Jump to [Getting Started](#-getting-started) section
- **Want to understand the tech?** → Check out [Technology & Algorithm Stack](#-technology--algorithm-stack)
- **Interested in contributing?** → See [Contributing](#-contributing) section

---

## 🧐 The Problem

Rural students face significant hurdles in their educational journey:
- **Lack of Conversational Practice**: No environment to practice spoken English, limiting fluency.
- **The Distraction Dilemma**: Mobile phones, while a resource, are a primary source of distraction.
- **Resource Scarcity**: Limited access to personalized, high-quality teaching aids.
- **The Foundational Gap**: A weak foundation in English creates barriers to higher education and careers in technology.

---

## ✨ Our Solution: ANU 6.0

ANU 6.0 is a 17-DOF humanoid robot that acts as a physical, AI-powered mentor. It provides a focused, interactive, and bilingual (Kannada & English) learning experience, adapting to each student's unique pace and needs. It's a friend to practice with, a teacher to learn from, and a tool that makes advanced technology accessible and fun.

### Key Features
- 🗣️ **Bilingual Conversation**: Fluent in both Kannada and English for natural interaction.
- 🎓 **Personalized Learning Paths**: Assesses student levels and creates custom lesson plans.
- 🤖 **Physical & Engaging**: Performs gestures like waving and hugging to create a strong, friendly bond.
- 🌐 **Hybrid AI Brain**: Functions offline with on-device models and syncs with powerful cloud APIs when online.
- 👀 **Computer Vision**: Uses OpenCV for face recognition and environmental awareness.
- 📵 **Distraction-Free**: A dedicated device for learning, free from the distractions of mobile phones.

---

## 🚀 Project Architecture

The system follows a modular, three-stage flow:
1.  **Perception (Input)**: The robot gathers data using its webcam (visuals), microphone (voice commands), and environmental sensors (proximity, presence).
2.  **Processing (The Brain)**: The Raspberry Pi 5 processes this data. It transcribes speech, analyzes images, and uses its hybrid AI core (local models + cloud APIs) to make decisions.
3.  **Actuation (Output)**: The brain sends commands to the PCA9685 servo driver to perform physical actions and to the speaker to generate verbal responses.

---

## 🔬 Technology & Algorithm Stack

### End-to-End Pipeline

```
Student Speech/Video 
  → Audio Preprocessing 
  → Voice Activity Detection (VAD) 
  → Automatic Speech Recognition (ASR) 
  → Phoneme Extraction / Forced Alignment 
  → Pronunciation Scoring 
  → NLU / Intent & Dialog Management 
  → Response Generation (LLM or Rule-based) 
  → Text-to-Speech (TTS) 
  → Robot Animation / UI 
  → Logging & Adaptation (Profile Update)
```

### Detailed Technology Stack

| Component | Purpose | Algorithms/Tools | Tech/Libraries | Notes |
|-----------|---------|----------------|----------------|--------|
| **Audio Input & Preprocessing** | Capture clean audio, normalize, remove noise | WebRTC VAD, spectral noise reduction, STFT | `sounddevice`/`pyaudio`, `webrtcvad`, `librosa`, `sox`, FFmpeg | Run VAD on-device; use 16 kHz mono |
| **Voice Activity Detection (VAD)** | Detect when student is speaking | WebRTC VAD (frame-based), energy-thresholding | `webrtcvad` (Python) | Combine with silence padding for full utterances |
| **Automatic Speech Recognition (ASR)** | Convert speech → text | Whisper-small/medium, Vosk/Kaldi, HuBERT/CTC | `whisper`, `vosk`, Hugging Face ASR, ONNX Runtime | Use Vosk for offline; Whisper for higher accuracy |
| **Forced Alignment / Phoneme Extraction** | Align transcript → phoneme timecodes | Montreal Forced Aligner (MFA), Gentle, CTC-based phoneme PPGs | `montreal-forced-aligner`, Kaldi/Gentle, PyTorch | MFA accurate but heavy; Gentle more lightweight |
| **Pronunciation Scoring** | Score pronunciation, highlight errors | Phoneme Error Rate (PER), DTW on phoneme posteriors | Custom Python module with alignment output | Provide percent score + corrective hints |
| **Speech Enhancement** | Improve ASR in noisy environments | Spectral subtraction, RNNoise, DNN denoisers | `rnnoise`, `demucs`, ONNX denoiser | Keep model small; denoise only when needed |
| **Natural Language Understanding (NLU)** | Parse commands, answers, intents | DistilBERT/miniLM/BERT (fine-tuned), rule-based fallback | Hugging Face `transformers`, `sklearn` | Use quantized models for on-device |
| **Dialogue Management** | Control lesson flow, adapt difficulty | FSM for scripted lessons + adaptive policy (bandit/RL) | Custom FSM, `rasa` (optional), rule engine | Keep pedagogical logic deterministic |
| **LLM for Explanations** | Generate natural feedback | Phi-3/Llama2-7B/Vicuna (quantized), instruction-tuned 3B | Hugging Face, `ggml`/`llama.cpp`, LM Studio | Use sparingly; sanitize output |
| **Text-to-Speech (TTS)** | Synthesize bilingual speech | Tacotron2+WaveGlow/VITS, Coqui TTS, VITS variants | `Coqui TTS`, `torch`, `gTTS`, `RhVoice` | Provide slow playback; Kannada + English voices |
| **Computer Vision** | Detect attention, mouth shape, gestures | MediaPipe (FaceMesh, Hands, Pose), CNN for lip detection | `mediapipe`, OpenCV, `tf-lite` | Use with consent; helpful for visual feedback |
| **Robot Control & Animation** | Synchronize servos with TTS | Servo sequencing, animation queue, viseme mapping | PCA9685 + Adafruit lib, `pySerial`, ROS-lite | Map phonemes → visemes for gestures |
| **Edge Inference** | Run ML models on Raspberry Pi | Model quantization, ONNX Runtime, TensorRT | ONNX Runtime, TensorRT, TFLite, `bitsandbytes` | Convert to ONNX/quantized formats |
| **Backend & Dashboard** | Teacher dashboard, analytics | REST API, database, web UI | FastAPI/Flask, PostgreSQL/SQLite, React+Tailwind | Docker containers; support offline mode |
| **Data Privacy & Security** | Protect student data | Encryption, TLS, anonymization | AES encryption, TLS, consent forms | Local-only mode; minimal audio retention |
| **Monitoring & Metrics** | Measure performance and learning | WER, PER, pronunciation score, engagement | Prometheus+Grafana, CSV/Excel export | Track model performance and student progress |

### Recommended Concrete Stack

**Core Technologies:**
- **ASR**: Vosk (offline) or Whisper-small (local)
- **Pronunciation/Alignment**: Montreal Forced Aligner / Gentle + custom PER calculator
- **VAD/Preprocessing**: `webrtcvad` + `librosa`
- **NLU**: DistilBERT / miniLM (Hugging Face) - fine-tuned for intents
- **LLM**: Phi-3 or quantized Llama2-7B via LM Studio / `llama.cpp`
- **TTS**: Coqui TTS or VITS (local voices for English + Kannada)
- **Computer Vision**: MediaPipe (FaceMesh & Hands)
- **Edge Runtime**: ONNX Runtime or TFLite, `bitsandbytes` for quantization
- **Robot Hardware**: Raspberry Pi 5, PCA9685 (16-ch servo driver), ESP32-CAM
- **Backend**: FastAPI + React (Tailwind) + SQLite/Postgres
- **DevOps**: Docker, GitHub Actions, SD image builder for Pi

### End-to-End Algorithm Example

```python
# 1. Audio Capture & Preprocessing
audio = capture()
chunks = segment(audio, webrtcvad)

# 2. Speech Recognition
clean = denoise(chunks)
transcript = asr_model.predict(clean)  # Whisper/Vosk

# 3. Forced Alignment
alignment = forced_align(transcript, clean)  # MFA/Gentle

# 4. Pronunciation Scoring
score = pronunciation_scoring(alignment, canonical_phonemes)  # PER + DTW

# 5. Intent Detection & Lesson Management
intent = nlu.predict(transcript)
next_action = lesson_engine.tick(intent, score)

# 6. Response Generation
reply_text = response_gen(template_or_llm(next_action, score))

# 7. Text-to-Speech & Animation
tts_audio = tts.synthesize(reply_text, lang)
play(tts_audio)
animate(viseme_map(reply_text))

# 8. Logging & Adaptation
log(student_id, score, intent, timestamp)
update_profile(student_id, score)
adapt_next_content(student_id)
```

---

## 📁 Repository Structure
```
ANU-Humanoid-AI/
│
├── 🤖 humanoid-robot/          # All code that runs on the Raspberry Pi
│   ├── main.py                 # Main application entry point
│   ├── config.py               # Configuration settings
│   ├── requirements.txt        # Python dependencies for the robot
│   ├── data/                   # Local database and storage
│   │   └── local_database.db   # SQLite database
│   │
│   ├── modules/                # Individual functionality modules
│   │   ├── speech/             # Speech processing (STT & TTS)
│   │   │   └── speech_processor.py
│   │   ├── vision/             # Computer vision & face recognition
│   │   │   └── vision_processor.py
│   │   ├── llm/                # Language model processing
│   │   │   └── llm_processor.py
│   │   ├── motion/             # Robot movement control
│   │   │   └── motion_controller.py
│   │   └── sensors/            # Sensor management
│   │       └── sensor_manager.py
│   │
│   └── utils/                  # Utility functions
│       └── network_checker.py  # Network connectivity utilities
│
├── 🌐 Anu-Server/              # Backend server (API & Services)
│   ├── main.py                 # Server entry point
│   ├── requirements.txt        # Server dependencies
│   ├── Dockerfile              # Docker configuration
│   └── app/                    # Application code
│       ├── __init__.py
│       ├── api.py              # API endpoints
│       ├── models.py           # Data models
│       └── services.py         # Business logic
│
├── 🌍 Anu-website/              # Project website & documentation
│   ├── index.html              # Interactive landing page
│   └── Ground Work.mp4         # Project demonstration video
│
└── README.md                   # This file
```

---

## 🌐 ANU Website

The **Anu-website** directory contains our interactive project website that serves as a comprehensive showcase and documentation platform for ANU 6.0.

### Website Features

- **🎨 Modern UI/UX**: Built with Tailwind CSS, featuring animated gradients, particle effects, and smooth scroll animations
- **📱 Fully Responsive**: Optimized for desktop, tablet, and mobile devices
- **🎯 Interactive Sections**:
  - Hero section with animated statistics
  - Problem statement with visual representations
  - Solution overview with feature cards
  - Technology stack visualization
  - Impact metrics and charts
  - Development roadmap timeline
  - Team showcase
- **📊 Data Visualization**: 
  - Interactive charts using Chart.js
  - 3D robot visualization with Three.js
  - System architecture diagrams
- **🚀 Performance**: Lightweight, fast-loading with optimized animations

### Accessing the Website

Simply open `Anu-website/index.html` in any modern web browser. The website is self-contained and requires no server setup.

### Website Sections

1. **Home**: Hero section with project introduction and key statistics
2. **Challenge**: Detailed problem statement for rural education
3. **Solution**: ANU 6.0 features and capabilities
4. **Technology**: Technical architecture and stack details
5. **Impact**: Projected social, economic, and educational impact
6. **Roadmap**: Development timeline and milestones
7. **Team**: Team members and mentors

The website provides an excellent overview for anyone wanting to understand the project quickly and visually.

### Why the Website Matters

The **Anu-website** serves multiple important purposes:

1. **📖 Project Documentation**: Acts as a living, interactive documentation that explains the project's mission, technology, and impact
2. **🎓 Educational Tool**: Helps stakeholders, educators, and potential partners understand the project without diving into code
3. **📊 Visual Communication**: Uses charts, animations, and visualizations to convey complex technical concepts
4. **🌐 Public Outreach**: Serves as a public-facing showcase for the project
5. **📱 Accessibility**: Easy to share and view on any device, making the project accessible to non-technical audiences

### Website vs. README

- **README.md**: Technical documentation for developers, setup instructions, and code structure
- **Website (index.html)**: Visual, interactive presentation for all audiences including educators, students, and stakeholders

Together, they provide comprehensive documentation for both technical and non-technical audiences.

---

## ⚙️ Getting Started

### Prerequisites

- Raspberry Pi 5 (8GB RAM recommended) with Raspberry Pi OS (64-bit)
- Python 3.9 or newer
- All hardware components (servos, drivers, camera, microphone, etc.)
- Internet connection (for initial setup)

### Installation

1.  **Clone the repository**:
    ```bash
    git clone [https://github.com/your-username/anu-6.0.git](https://github.com/your-username/anu-6.0.git)
    cd anu-6.0/robot_brain
    ```
2.  **Create a virtual environment**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Set up environment variables**:
    ```bash
    cp .env.example .env
    # Edit .env with your API keys and configuration
    ```
5.  **Hardware setup**:
    - Follow the hardware assembly guide in `/hardware/assembly_guide.md`
    - Connect all servos to the PCA9685 controller
    - Connect camera and microphone to Raspberry Pi

### Configuration

Edit the `.env` file with your specific configuration:
```env
# API Keys
GEMINI_API_KEY=your_gemini_api_key_here

# Speech Recognition
SPEECH_RECOGNITION_ENGINE=google  # google or vosk
VOSK_MODEL_PATH=./datasets/models/vosk-model

# Text-to-Speech
TTS_ENGINE=pyttsx3  # pyttsx3, gtts, or espeak

# Camera Settings
CAMERA_RESOLUTION=640x480
CAMERA_FPS=30

# Servo Configuration
SERVO_FREQUENCY=50
SERVO_MIN_PULSE=500
SERVO_MAX_PULSE=2500
```

### Running the Robot
```bash
# Activate virtual environment
source .venv/bin/activate

# Run the main application
python main.py

# Or run with specific modules
python -m modules.speech_processing.voice_processor
```

### Viewing the Project Website

The ANU website provides a comprehensive visual overview of the project:

```bash
# Navigate to the website directory
cd Anu-website

# Open index.html in your browser
# On Linux/Mac:
open index.html
# On Windows:
start index.html
# Or simply double-click index.html in your file manager
```

The website is fully self-contained and includes:
- Interactive project showcase
- Technology stack visualization
- Development roadmap
- Team information
- Impact metrics and charts

No server setup required - just open the HTML file in any modern web browser!

---

## 🧪 Testing
Run the test suite to verify all components are working:
```bash
# Run all tests
python -m pytest tests/

# Run specific test modules
python -m pytest tests/test_speech.py -v
python -m pytest tests/test_vision.py -v
python -m pytest tests/test_motion.py -v
```

---

## 🤝 Contributing
We welcome contributions! Please read our `Contribution Guide` for details on our code of conduct and the process for submitting pull requests.

### Development Setup
1.  Fork the repository
2.  Create a feature branch: `git checkout -b feature/amazing-feature`
3.  Commit your changes: `git commit -m 'Add amazing feature'`
4.  Push to the branch: `git push origin feature/amazing-feature`
5.  Open a pull request

---

## 📝 License
This project is licensed under the MIT License - see the `LICENSE` file for details.

---

## 🙏 Acknowledgments
- Coorg Institute of Technology, Ponnampet
- EvoBot Crew team members
- Open source communities for various libraries and tools
- Raspberry Pi Foundation for hardware support

---

## 📞 Contact
For questions or support, please contact:
- **Project Lead**: Sadhu J - https://sadhujdeveloper.com
- **Development Team**: https://anuai.sadhujdeveloper.com

---

## 🔗 Useful Links
- **🌐 Project Website**: Open `Anu-website/index.html` in your browser for interactive project showcase
- **📚 GitHub Repository**: [ANU-AI-Humanoid](https://github.com/Sadhu2005/ANU-AI-Humanoid.git)
- **👤 Project Lead**: [Sadhu J - Portfolio](https://sadhujdeveloper.com)
- **🌍 Development Team**: [ANU AI Website](https://anuai.sadhujdeveloper.com)
- **💼 LinkedIn**: [Sadhu J](https://www.linkedin.com/in/sadhu-j-3387b228a)
- **📧 Contact**: sadhuj2005@gmail.com

## 📚 Documentation

Comprehensive documentation is available:

- **[📖 Project Documentation](./PROJECT_DOCUMENTATION.md)** - Complete project overview, architecture, and technical details
- **[🔬 Research Documentation](./RESEARCH_DOCUMENTATION.md)** - Current research activities and academic contributions
- **[📦 Product Documentation](./PRODUCT_DOCUMENTATION.md)** - Product portfolio, features, and business information
- **[🛠️ Setup Guide](./SETUP_GUIDE.md)** - Step-by-step installation and configuration
- **[📋 Documentation Index](./DOCUMENTATION_INDEX.md)** - Quick navigation to all documentation

For quick access, see the [Documentation Index](./DOCUMENTATION_INDEX.md).

<p align="center"> Made with ❤️ by the EvoBot Crew | Coorg Institute of Technology </p>