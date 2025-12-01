"""
Network Manager for ANU 6.0 Robot
Handles online/offline mode switching and server communication
"""

import requests
import time
import threading
from typing import Optional, Dict, Any
from queue import Queue
import json

class NetworkManager:
    """Manages network connectivity and server communication"""
    
    def __init__(self, server_url: str = "http://localhost:8000", 
                 check_interval: int = 30):
        """
        Initialize network manager
        
        Args:
            server_url: Server API URL
            check_interval: Network check interval in seconds
        """
        self.server_url = server_url
        self.check_interval = check_interval
        self.is_online = False
        self.last_check = 0
        self.sync_queue = Queue()
        self.running = False
        
        # Check initial connection
        self.check_connection()
    
    def check_connection(self) -> bool:
        """Check if server is reachable"""
        try:
            response = requests.get(
                f"{self.server_url}/api/health",
                timeout=5
            )
            if response.status_code == 200:
                self.is_online = True
                self.last_check = time.time()
                return True
        except Exception as e:
            print(f"Network check failed: {e}")
        
        self.is_online = False
        self.last_check = time.time()
        return False
    
    def start_monitoring(self):
        """Start network monitoring in background thread"""
        self.running = True
        thread = threading.Thread(target=self._monitor_loop, daemon=True)
        thread.start()
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.running:
            self.check_connection()
            time.sleep(self.check_interval)
    
    def sync_data(self, data: Dict[str, Any]) -> bool:
        """
        Sync data to server (or queue if offline)
        
        Args:
            data: Data to sync
        
        Returns:
            True if synced, False if queued
        """
        if self.is_online:
            try:
                response = requests.post(
                    f"{self.server_url}/api/robot/sync",
                    json=data,
                    timeout=10
                )
                if response.status_code == 200:
                    return True
            except Exception as e:
                print(f"Sync failed: {e}")
                self.is_online = False
        
        # Queue for later sync
        self.sync_queue.put({
            'data': data,
            'timestamp': time.time()
        })
        return False
    
    def sync_queue_to_server(self):
        """Sync queued data when back online"""
        if not self.is_online:
            return
        
        synced_count = 0
        while not self.sync_queue.empty():
            try:
                item = self.sync_queue.get_nowait()
                data = item['data']
                
                response = requests.post(
                    f"{self.server_url}/api/robot/sync",
                    json=data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    synced_count += 1
                else:
                    # Put back in queue if failed
                    self.sync_queue.put(item)
                    break
                    
            except Exception as e:
                print(f"Error syncing queued data: {e}")
                break
        
        if synced_count > 0:
            print(f"Synced {synced_count} items from queue")
    
    def get_robot_commands(self, robot_id: str) -> List[Dict]:
        """Get pending commands from server"""
        if not self.is_online:
            return []
        
        try:
            response = requests.get(
                f"{self.server_url}/api/robot/commands/{robot_id}",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('commands', [])
        except Exception as e:
            print(f"Error getting commands: {e}")
        
        return []
    
    def update_status(self, robot_id: str, status: Dict[str, Any]) -> bool:
        """Update robot status on server"""
        if not self.is_online:
            return False
        
        try:
            response = requests.post(
                f"{self.server_url}/api/robot/status",
                json={'robot_id': robot_id, **status},
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error updating status: {e}")
            return False
    
    def stop(self):
        """Stop network manager"""
        self.running = False

