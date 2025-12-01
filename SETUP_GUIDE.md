# ANU 6.0 Setup Guide

Complete setup guide for ANU 6.0 Humanoid Robot based on the project presentation specifications.

## 📋 Table of Contents

1. [Hardware Requirements](#hardware-requirements)
2. [Software Requirements](#software-requirements)
3. [Hardware Assembly](#hardware-assembly)
4. [Software Installation](#software-installation)
5. [Configuration](#configuration)
6. [First Run](#first-run)
7. [Troubleshooting](#troubleshooting)

---

## 🔧 Hardware Requirements

Based on the project presentation, you need:

### Core Components
- **Raspberry Pi 5** (8GB RAM recommended)
  - MicroSD card (64GB minimum, Class 10 or better)
  - Power supply (5V, 5A minimum)
  
### Robot Components
- **17 DOF Humanoid Robot Kit** with MG995 Servo Motors
- **PCA9685** PWM Servo Driver (16-channel)
- **HD Webcam** (for face recognition using OpenCV)
- **USB Microphone** (for speech recognition)
- **Bluetooth Speaker** (for TTS responses)
- **10 Battery** (5V, 5A power supply for servos)

### Sensors
- **Ultrasonic Sensor** (HC-SR04) - for obstacle detection
- **PIR Motion Sensors** (2x) - for presence detection
- **Temperature Sensor** (DHT11) - for monitoring

### Additional
- **Jumper wires** for connections
- **Breadboard** (optional, for prototyping)
- **Mounting hardware** for components

---

## 💻 Software Requirements

### Operating System
- **Raspberry Pi OS** (64-bit) - Latest version
- Python 3.9 or newer

### Python Packages
All required packages are listed in `humanoid-robot/requirements.txt`

### Models & Data
- **Vosk Model** (Indian English) - for offline speech recognition
- **Silero VAD Model** - for voice activity detection
- **YOLO Model** (yolov8n) - for object detection
- **Face Recognition Database** - for known faces

---

## 🔨 Hardware Assembly

### Step 1: Assemble Robot Frame
1. Follow the 17 DOF humanoid robot kit assembly instructions
2. Mount all 17 MG995 servo motors in their designated positions
3. Ensure all joints move freely

### Step 2: Connect Servo Motors
1. Connect all servos to the PCA9685 board:
   - Each servo has 3 wires: Power (Red), Ground (Black), Signal (Yellow/White)
   - Connect Power and Ground to PCA9685 power rails
   - Connect Signal wires to PCA9685 channels (0-16)

2. Connect PCA9685 to Raspberry Pi:
   - VCC → 3.3V (Pi)
   - GND → GND (Pi)
   - SDA → GPIO 2 (SDA)
   - SCL → GPIO 3 (SCL)

### Step 3: Connect Sensors

**Ultrasonic Sensor (HC-SR04):**
- VCC → 5V (Pi)
- GND → GND (Pi)
- Trig → GPIO 23
- Echo → GPIO 24

**PIR Sensors:**
- Sensor 1: VCC → 5V, GND → GND, OUT → GPIO 25
- Sensor 2: VCC → 5V, GND → GND, OUT → GPIO 26

**Temperature Sensor (DHT11):**
- VCC → 3.3V
- GND → GND
- DATA → GPIO 27

### Step 4: Connect Audio/Video

**Webcam:**
- Connect USB webcam to any USB port on Raspberry Pi

**Microphone:**
- Connect USB microphone to Raspberry Pi

**Bluetooth Speaker:**
- Pair with Raspberry Pi via Bluetooth settings
- Set as default audio output

### Step 5: Power Supply
1. Connect 5V, 5A power supply to PCA9685 for servos
2. Ensure Raspberry Pi has separate power supply
3. **Important:** Do not power servos from Raspberry Pi directly!

---

## 📦 Software Installation

### Step 1: Update System
```bash
sudo apt update
sudo apt upgrade -y
```

### Step 2: Install System Dependencies
```bash
sudo apt install -y python3-pip python3-venv git i2c-tools
sudo apt install -y espeak espeak-data libespeak1 libespeak-dev
sudo apt install -y portaudio19-dev python3-pyaudio
sudo apt install -y libopencv-dev python3-opencv
```

### Step 3: Enable I2C
```bash
sudo raspi-config
# Navigate to: Interface Options → I2C → Enable
sudo reboot
```

### Step 4: Clone Repository
```bash
cd ~
git clone https://github.com/Sadhu2005/ANU-AI-Humanoid.git
cd ANU-AI-Humanoid/humanoid-robot
```

### Step 5: Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 6: Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 7: Download Models

**Vosk Model (Indian English):**
```bash
mkdir -p models/vosk
cd models/vosk
wget https://alphacephei.com/vosk/models/vosk-model-small-en-in-0.4.zip
unzip vosk-model-small-en-in-0.4.zip
mv vosk-model-small-en-in-0.4 indian-english
cd ../..
```

**Silero VAD Model:**
```bash
mkdir -p models/silero_vad
# The model will be downloaded automatically on first use
```

**YOLO Model:**
```bash
# Will be downloaded automatically on first use
```

### Step 8: Create Data Directories
```bash
mkdir -p data/faces
mkdir -p logs
```

---

## ⚙️ Configuration

### Step 1: Copy Environment File
```bash
cp .env.example .env
```

### Step 2: Edit Configuration
```bash
nano .env
```

**Key configurations:**
```env
# API Keys
GEMINI_API_KEY=your_actual_api_key_here

# Paths (adjust if needed)
VOSK_MODEL_PATH=./models/vosk/indian-english
SILERO_VAD_PATH=./models/silero_vad

# Hardware
PCA9685_ADDRESS=0x40
SERVO_COUNT=17

# Motor pins (adjust based on your wiring)
MOTOR_FRONT_LEFT=1,2,3
MOTOR_FRONT_RIGHT=4,5,6
MOTOR_BACK_LEFT=7,8,9
MOTOR_BACK_RIGHT=10,11,12
```

### Step 3: Calibrate Servos
```bash
python3 calibrate_servos.py
# Follow on-screen instructions to set servo ranges
```

---

## 🚀 First Run

### Step 1: Test Hardware
```bash
# Test servos
python3 test_servos.py

# Test camera
python3 test_camera.py

# Test microphone
python3 test_microphone.py

# Test sensors
python3 test_sensors.py
```

### Step 2: Register First Student
```python
from modules.learning.adaptive_learner import AdaptiveLearner

learner = AdaptiveLearner()
learner.register_student(
    student_id="STU001",
    name="Test Student",
    age=10,
    initial_level="beginner"
)
```

### Step 3: Run Robot
```bash
python3 main.py
```

The robot should:
1. Initialize all modules
2. Start listening for speech
3. Process vision input
4. Be ready for interaction

---

## 🎓 Usage Guide

### For Students

1. **Starting a Lesson:**
   - Stand in front of the robot
   - Robot will recognize you (if registered)
   - Say "Hello ANU" to start

2. **During Lesson:**
   - Speak clearly into the microphone
   - Robot will provide pronunciation feedback
   - Follow robot's gestures and instructions

3. **Getting Help:**
   - Say "Help" for assistance
   - Say "Repeat" to hear again
   - Say "Stop" to end lesson

### For Teachers

1. **Monitor Progress:**
   ```python
   from modules.learning.adaptive_learner import AdaptiveLearner
   
   learner = AdaptiveLearner()
   stats = learner.get_student_stats("STU001")
   print(stats)
   ```

2. **View Dashboard:**
   - Access web dashboard (if server is running)
   - View student progress charts
   - Assign lessons

---

## 🔍 Troubleshooting

### Servos Not Moving
- Check PCA9685 connections
- Verify I2C is enabled: `sudo i2cdetect -y 1`
- Check power supply (5V, 5A)

### Speech Not Recognized
- Test microphone: `arecord -d 5 test.wav && aplay test.wav`
- Check Vosk model path in `.env`
- Verify microphone permissions

### Camera Not Working
- Check USB connection
- Test with: `raspistill -o test.jpg`
- Verify camera permissions

### Import Errors
- Ensure virtual environment is activated
- Reinstall requirements: `pip install -r requirements.txt --force-reinstall`

### Low Performance
- Reduce `VISION_PROCESSING_FPS` in config
- Use smaller models (yolov8n instead of yolov8m)
- Close unnecessary applications

---

## 📞 Support

For issues or questions:
- **GitHub Issues**: [Create an issue](https://github.com/Sadhu2005/ANU-AI-Humanoid/issues)
- **Email**: sadhuj2005@gmail.com
- **Project Website**: Open `Anu-website/index.html`

---

## 📚 Additional Resources

- [Raspberry Pi Documentation](https://www.raspberrypi.org/documentation/)
- [PCA9685 Datasheet](https://cdn-shop.adafruit.com/datasheets/PCA9685.pdf)
- [Vosk Documentation](https://alphacephei.com/vosk/)
- [OpenCV Documentation](https://docs.opencv.org/)

---

**Last Updated**: January 2025
**Version**: 6.0

