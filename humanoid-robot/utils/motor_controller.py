"""
Motor Controller utility for ANU 6.0 robot
Handles DC motor control for robot movement
"""

import time
import RPi.GPIO as GPIO

class MotorController:
    """Controls DC motors for robot locomotion"""
    
    def __init__(self, motor_pins):
        """
        Initialize motor controller
        
        Args:
            motor_pins: Dictionary with motor pin configurations
                Example: {
                    'front_left': [enable_pin, in1_pin, in2_pin],
                    'front_right': [enable_pin, in1_pin, in2_pin],
                    'back_left': [enable_pin, in1_pin, in2_pin],
                    'back_right': [enable_pin, in1_pin, in2_pin]
                }
        """
        self.motor_pins = motor_pins
        self.current_speed = 0.0
        self.is_moving = False
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Initialize all motor pins
        for motor_name, pins in motor_pins.items():
            if len(pins) >= 3:
                enable_pin, in1_pin, in2_pin = pins[0], pins[1], pins[2]
                
                # Setup pins as outputs
                GPIO.setup(enable_pin, GPIO.OUT)
                GPIO.setup(in1_pin, GPIO.OUT)
                GPIO.setup(in2_pin, GPIO.OUT)
                
                # Initialize PWM for speed control
                pwm = GPIO.PWM(enable_pin, 1000)  # 1000 Hz frequency
                pwm.start(0)
                motor_pins[motor_name].append(pwm)  # Store PWM object
    
    def move_forward(self, speed=0.5):
        """Move robot forward"""
        self._set_all_motors_forward(speed)
        self.is_moving = True
        self.current_speed = speed
    
    def move_backward(self, speed=0.5):
        """Move robot backward"""
        self._set_all_motors_backward(speed)
        self.is_moving = True
        self.current_speed = speed
    
    def turn_left(self, speed=0.5):
        """Turn robot left (rotate in place)"""
        self._set_motors_turn_left(speed)
        self.is_moving = True
        self.current_speed = speed
    
    def turn_right(self, speed=0.5):
        """Turn robot right (rotate in place)"""
        self._set_motors_turn_right(speed)
        self.is_moving = True
        self.current_speed = speed
    
    def stop(self):
        """Stop all motors"""
        for motor_name, pins in self.motor_pins.items():
            if len(pins) >= 4:
                pwm = pins[3]  # PWM object
                pwm.ChangeDutyCycle(0)
                
                # Set direction pins to low
                if len(pins) >= 3:
                    GPIO.output(pins[1], GPIO.LOW)
                    GPIO.output(pins[2], GPIO.LOW)
        
        self.is_moving = False
        self.current_speed = 0.0
    
    def _set_all_motors_forward(self, speed):
        """Set all motors to move forward"""
        duty_cycle = int(speed * 100)
        
        for motor_name, pins in self.motor_pins.items():
            if len(pins) >= 4:
                pwm = pins[3]
                in1_pin, in2_pin = pins[1], pins[2]
                
                # Set direction: forward
                GPIO.output(in1_pin, GPIO.HIGH)
                GPIO.output(in2_pin, GPIO.LOW)
                
                # Set speed
                pwm.ChangeDutyCycle(duty_cycle)
    
    def _set_all_motors_backward(self, speed):
        """Set all motors to move backward"""
        duty_cycle = int(speed * 100)
        
        for motor_name, pins in self.motor_pins.items():
            if len(pins) >= 4:
                pwm = pins[3]
                in1_pin, in2_pin = pins[1], pins[2]
                
                # Set direction: backward
                GPIO.output(in1_pin, GPIO.LOW)
                GPIO.output(in2_pin, GPIO.HIGH)
                
                # Set speed
                pwm.ChangeDutyCycle(duty_cycle)
    
    def _set_motors_turn_left(self, speed):
        """Set motors to turn left"""
        duty_cycle = int(speed * 100)
        
        # Left motors backward, right motors forward
        for motor_name, pins in self.motor_pins.items():
            if len(pins) >= 4:
                pwm = pins[3]
                in1_pin, in2_pin = pins[1], pins[2]
                
                if 'left' in motor_name:
                    # Left side: backward
                    GPIO.output(in1_pin, GPIO.LOW)
                    GPIO.output(in2_pin, GPIO.HIGH)
                else:
                    # Right side: forward
                    GPIO.output(in1_pin, GPIO.HIGH)
                    GPIO.output(in2_pin, GPIO.LOW)
                
                pwm.ChangeDutyCycle(duty_cycle)
    
    def _set_motors_turn_right(self, speed):
        """Set motors to turn right"""
        duty_cycle = int(speed * 100)
        
        # Left motors forward, right motors backward
        for motor_name, pins in self.motor_pins.items():
            if len(pins) >= 4:
                pwm = pins[3]
                in1_pin, in2_pin = pins[1], pins[2]
                
                if 'left' in motor_name:
                    # Left side: forward
                    GPIO.output(in1_pin, GPIO.HIGH)
                    GPIO.output(in2_pin, GPIO.LOW)
                else:
                    # Right side: backward
                    GPIO.output(in1_pin, GPIO.LOW)
                    GPIO.output(in2_pin, GPIO.HIGH)
                
                pwm.ChangeDutyCycle(duty_cycle)
    
    def cleanup(self):
        """Cleanup GPIO resources"""
        self.stop()
        for motor_name, pins in self.motor_pins.items():
            if len(pins) >= 4:
                pwm = pins[3]
                pwm.stop()
        GPIO.cleanup()

