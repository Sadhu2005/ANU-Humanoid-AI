import threading
import time
import RPi.GPIO as GPIO

class SensorManager:
    def __init__(self, output_queue, config):
        self.output_queue = output_queue
        self.config = config
        self.running = False
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        
        # Setup ultrasonic sensor
        GPIO.setup(self.config.ULTRASONIC_PINS['trigger'], GPIO.OUT)
        GPIO.setup(self.config.ULTRASONIC_PINS['echo'], GPIO.IN)
        
        # Setup PIR sensors
        for pin in self.config.PIR_PINS:
            GPIO.setup(pin, GPIO.IN)
        
        # Setup temperature sensor (assuming DHT11)
        GPIO.setup(self.config.TEMP_SENSOR_PIN, GPIO.IN)
        
        # Sensor data
        self.sensor_data = {
            'distance': 0,
            'motion_detected': False,
            'temperature': 0,
            'humidity': 0
        }
    
    def run(self):
        """Run sensor monitoring in a separate thread"""
        self.running = True
        
        print("Sensor manager started.")
        while self.running:
            # Read all sensors
            self.read_ultrasonic()
            self.read_pir()
            self.read_temperature()
            
            # Check for emergency conditions
            self.check_emergencies()
            
            # Send data to output queue
            self.output_queue.put(self.sensor_data.copy())
            
            time.sleep(0.1)  # Read sensors 10 times per second
    
    def read_ultrasonic(self):
        """Read distance from ultrasonic sensor"""
        # Send trigger pulse
        GPIO.output(self.config.ULTRASONIC_PINS['trigger'], True)
        time.sleep(0.00001)
        GPIO.output(self.config.ULTRASONIC_PINS['trigger'], False)
        
        # Measure echo pulse duration
        start_time = time.time()
        stop_time = time.time()
        
        while GPIO.input(self.config.ULTRASONIC_PINS['echo']) == 0:
            start_time = time.time()
        
        while GPIO.input(self.config.ULTRASONIC_PINS['echo']) == 1:
            stop_time = time.time()
        
        # Calculate distance
        time_elapsed = stop_time - start_time
        distance = (time_elapsed * 34300) / 2  # Speed of sound is 343 m/s
        
        self.sensor_data['distance'] = distance
    
    def read_pir(self):
        """Read PIR motion sensors"""
        motion_detected = False
        for pin in self.config.PIR_PINS:
            if GPIO.input(pin):
                motion_detected = True
                break
        
        self.sensor_data['motion_detected'] = motion_detected
    
    def read_temperature(self):
        """Read temperature and humidity from DHT11"""
        # This is a simplified implementation
        # For actual DHT11 reading, you'd need a proper library
        try:
            # Placeholder for actual DHT11 reading code
            self.sensor_data['temperature'] = 25  # Example value
            self.sensor_data['humidity'] = 50     # Example value
        except:
            # If reading fails, keep previous values
            pass
    
    def check_emergencies(self):
        """Check for emergency conditions"""
        # Check if obstacle is too close
        if self.sensor_data['distance'] < 20:  # 20 cm threshold
            self.sensor_data['obstacle_too_close'] = True
        else:
            self.sensor_data['obstacle_too_close'] = False
        
        # Check if temperature is too high
        if self.sensor_data['temperature'] > 40:  # 40°C threshold
            self.sensor_data['temperature_high'] = True
        else:
            self.sensor_data['temperature_high'] = False
    
    def get_battery_level(self):
        """Get battery level (placeholder)"""
        # Implement actual battery monitoring based on your hardware
        return "80%"  # Example value
    
    def stop(self):
        """Stop sensor monitoring"""
        self.running = False
        GPIO.cleanup()