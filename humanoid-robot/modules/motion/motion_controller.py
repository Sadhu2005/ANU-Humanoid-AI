import threading
import time
from adafruit_servokit import ServoKit
from utils.motor_controller import MotorController

class MotionController:
    def __init__(self, input_queue, config):
        self.input_queue = input_queue
        self.config = config
        self.running = False
        
        # Initialize servo controller
        self.servo_kit = ServoKit(channels=16, address=self.config.PCA9685_ADDRESS)
        
        # Initialize motor controller
        self.motor_controller = MotorController(self.config.MOTOR_PINS)
        
        # Servo positions
        self.servo_positions = [90] * self.config.SERVO_COUNT  # Default to center
        
        # Predefined poses
        self.poses = {
            'neutral': [90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90],
            'wave': [90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 180],
            # Define more poses as needed
        }
    
    def run(self):
        """Run motion controller in a separate thread"""
        self.running = True
        
        print("Motion controller started.")
        while self.running:
            if not self.input_queue.empty():
                command = self.input_queue.get()
                self.execute_command(command)
            
            time.sleep(0.01)  # Short sleep to prevent CPU overload
    
    def execute_command(self, command):
        """Execute a motion command"""
        action = command.get('action')
        
        if action == 'move':
            self.move(
                command.get('direction'),
                command.get('distance', 0),
                command.get('speed', 0.5)
            )
        elif action == 'stop':
            self.stop_motors()
        elif action == 'gesture':
            self.execute_gesture(command.get('gesture'))
        elif action == 'pose':
            self.set_pose(command.get('pose'))
        elif action == 'servo':
            self.set_servo(
                command.get('servo_id'),
                command.get('position'),
                command.get('speed', 1.0)
            )
    
    def move(self, direction, distance=0, speed=0.5):
        """Move the robot in a specific direction"""
        # Convert direction to motor commands
        if direction == 'forward':
            self.motor_controller.move_forward(speed)
        elif direction == 'backward':
            self.motor_controller.move_backward(speed)
        elif direction == 'left':
            self.motor_controller.turn_left(speed)
        elif direction == 'right':
            self.motor_controller.turn_right(speed)
        
        # If distance is specified, stop after moving that distance
        if distance > 0:
            time.sleep(self.calculate_move_time(distance, speed))
            self.stop_motors()
    
    def stop_motors(self):
        """Stop all motors"""
        self.motor_controller.stop()
    
    def execute_gesture(self, gesture):
        """Execute a predefined gesture"""
        if gesture in self.poses:
            self.set_pose(self.poses[gesture])
            
            # For wave gesture, add animation
            if gesture == 'wave':
                self.animate_wave()
    
    def set_pose(self, pose):
        """Set servo positions to a predefined pose"""
        for i, position in enumerate(pose):
            self.set_servo(i, position, speed=0.5)
    
    def set_servo(self, servo_id, position, speed=1.0):
        """Set a servo to a specific position with controlled speed"""
        if servo_id < 0 or servo_id >= self.config.SERVO_COUNT:
            print(f"Invalid servo ID: {servo_id}")
            return
        
        # Check if position is within valid range
        min_pos, max_pos = self.config.SERVO_RANGES.get(servo_id, [0, 180])
        position = max(min_pos, min(max_pos, position))
        
        # Move servo gradually for smooth motion
        current_pos = self.servo_positions[servo_id]
        steps = abs(position - current_pos)
        step_delay = 0.02 / speed  # Adjust delay based on speed
        
        for step in range(1, steps + 1):
            intermediate_pos = current_pos + (position - current_pos) * step / steps
            self.servo_kit.servo[servo_id].angle = intermediate_pos
            time.sleep(step_delay)
        
        self.servo_positions[servo_id] = position
    
    def animate_wave(self):
        """Animate a waving motion"""
        # Wave arm back and forth
        for _ in range(3):
            self.set_servo(16, 180, speed=2.0)  # Wave arm up
            time.sleep(0.3)
            self.set_servo(16, 90, speed=2.0)   # Wave arm down
            time.sleep(0.3)
        
        # Return to neutral position
        self.set_servo(16, 90, speed=1.0)
    
    def calculate_move_time(self, distance, speed):
        """Calculate time needed to move a certain distance"""
        # This would be calibrated based on your specific hardware
        base_speed_cm_per_sec = 10  # Adjust based on your motors
        return distance / (base_speed_cm_per_sec * speed)
    
    def emergency_stop(self):
        """Immediately stop all motion"""
        self.stop_motors()
        # Set all servos to neutral position quickly
        for i, pos in enumerate(self.poses['neutral']):
            self.servo_kit.servo[i].angle = pos
            self.servo_positions[i] = pos
    
    def stop(self):
        """Stop motion controller"""
        self.running = False
        self.emergency_stop()  # Stop all motion when shutting down