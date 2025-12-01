"""
SQLite Database Manager for ANU 6.0 Robot
Handles all local database operations
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import os

class RobotDatabase:
    """SQLite database manager for robot local storage"""
    
    def __init__(self, db_path: str = 'data/local_database.db'):
        """
        Initialize database connection
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_directory()
        self._init_database()
    
    def _ensure_directory(self):
        """Ensure database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Students table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER,
                level TEXT DEFAULT 'beginner',
                face_encoding BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP
            )
        ''')
        
        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                student_id TEXT,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                duration INTEGER,
                lesson_type TEXT,
                FOREIGN KEY (student_id) REFERENCES students(student_id)
            )
        ''')
        
        # Pronunciation records
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pronunciation_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT,
                session_id TEXT,
                phrase TEXT,
                target_phonemes TEXT,
                student_phonemes TEXT,
                score REAL,
                errors TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(student_id),
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        ''')
        
        # Learning progress
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT,
                lesson_id TEXT,
                pronunciation_score REAL,
                comprehension_score REAL,
                vocabulary_score REAL,
                engagement_score REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(student_id)
            )
        ''')
        
        # Interactions log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT,
                session_id TEXT,
                interaction_type TEXT,
                input_text TEXT,
                output_text TEXT,
                intent TEXT,
                confidence REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(student_id),
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        ''')
        
        # Robot state log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS robot_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                battery_level REAL,
                temperature REAL,
                cpu_usage REAL,
                memory_usage REAL,
                network_status TEXT,
                active_modules TEXT
            )
        ''')
        
        # Face recognition cache
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS face_cache (
                student_id TEXT PRIMARY KEY,
                face_encoding BLOB,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(student_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def add_student(self, student_id: str, name: str, age: int, 
                   level: str = 'beginner', face_encoding: Optional[bytes] = None):
        """Add a new student"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO students 
                (student_id, name, age, level, face_encoding, last_seen)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (student_id, name, age, level, face_encoding))
            
            if face_encoding:
                cursor.execute('''
                    INSERT OR REPLACE INTO face_cache 
                    (student_id, face_encoding, last_updated)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (student_id, face_encoding))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding student: {e}")
            return False
        finally:
            conn.close()
    
    def get_student(self, student_id: str) -> Optional[Dict]:
        """Get student information"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM students WHERE student_id = ?', (student_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()
    
    def create_session(self, student_id: str, lesson_type: str = 'general') -> str:
        """Create a new learning session"""
        import uuid
        session_id = str(uuid.uuid4())
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO sessions (session_id, student_id, lesson_type)
                VALUES (?, ?, ?)
            ''', (session_id, student_id, lesson_type))
            
            conn.commit()
            return session_id
        except Exception as e:
            print(f"Error creating session: {e}")
            return None
        finally:
            conn.close()
    
    def end_session(self, session_id: str):
        """End a session and calculate duration"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE sessions 
                SET end_time = CURRENT_TIMESTAMP,
                    duration = CAST((julianday(CURRENT_TIMESTAMP) - julianday(start_time)) * 86400 AS INTEGER)
                WHERE session_id = ?
            ''', (session_id,))
            
            conn.commit()
        except Exception as e:
            print(f"Error ending session: {e}")
        finally:
            conn.close()
    
    def save_pronunciation(self, student_id: str, session_id: str, 
                          phrase: str, target_phonemes: List[str],
                          student_phonemes: List[str], score: float,
                          errors: List[Dict]):
        """Save pronunciation record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO pronunciation_records
                (student_id, session_id, phrase, target_phonemes, 
                 student_phonemes, score, errors)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (student_id, session_id, phrase,
                  json.dumps(target_phonemes), json.dumps(student_phonemes),
                  score, json.dumps(errors)))
            
            conn.commit()
        except Exception as e:
            print(f"Error saving pronunciation: {e}")
        finally:
            conn.close()
    
    def save_progress(self, student_id: str, lesson_id: str,
                     pronunciation_score: float,
                     comprehension_score: Optional[float] = None,
                     vocabulary_score: Optional[float] = None,
                     engagement_score: Optional[float] = None):
        """Save learning progress"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO learning_progress
                (student_id, lesson_id, pronunciation_score, 
                 comprehension_score, vocabulary_score, engagement_score)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (student_id, lesson_id, pronunciation_score,
                  comprehension_score, vocabulary_score, engagement_score))
            
            conn.commit()
        except Exception as e:
            print(f"Error saving progress: {e}")
        finally:
            conn.close()
    
    def log_interaction(self, student_id: str, session_id: str,
                       interaction_type: str, input_text: str,
                       output_text: str, intent: str, confidence: float):
        """Log interaction"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO interactions
                (student_id, session_id, interaction_type, input_text,
                 output_text, intent, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (student_id, session_id, interaction_type, input_text,
                  output_text, intent, confidence))
            
            conn.commit()
        except Exception as e:
            print(f"Error logging interaction: {e}")
        finally:
            conn.close()
    
    def get_student_stats(self, student_id: str) -> Dict:
        """Get comprehensive student statistics"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Overall stats
            cursor.execute('''
                SELECT 
                    COUNT(DISTINCT session_id) as total_sessions,
                    AVG(pronunciation_score) as avg_pronunciation,
                    AVG(comprehension_score) as avg_comprehension,
                    AVG(vocabulary_score) as avg_vocabulary,
                    MAX(timestamp) as last_lesson
                FROM learning_progress
                WHERE student_id = ?
            ''', (student_id,))
            
            stats = cursor.fetchone()
            
            # Recent performance
            cursor.execute('''
                SELECT pronunciation_score, timestamp
                FROM learning_progress
                WHERE student_id = ?
                ORDER BY timestamp DESC
                LIMIT 10
            ''', (student_id,))
            
            recent_scores = [dict(row) for row in cursor.fetchall()]
            
            return {
                'total_sessions': stats['total_sessions'] or 0,
                'avg_pronunciation': round(stats['avg_pronunciation'] or 0, 2),
                'avg_comprehension': round(stats['avg_comprehension'] or 0, 2) if stats['avg_comprehension'] else None,
                'avg_vocabulary': round(stats['avg_vocabulary'] or 0, 2) if stats['avg_vocabulary'] else None,
                'last_lesson': stats['last_lesson'],
                'recent_scores': recent_scores
            }
        finally:
            conn.close()
    
    def get_face_encoding(self, student_id: str) -> Optional[bytes]:
        """Get face encoding from cache"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT face_encoding FROM face_cache WHERE student_id = ?', (student_id,))
            row = cursor.fetchone()
            if row and row[0]:
                return row[0]
            return None
        finally:
            conn.close()

