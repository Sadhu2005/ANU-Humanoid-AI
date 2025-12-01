"""
Adaptive Learning Module for ANU 6.0
Tracks student progress and adapts lesson difficulty
Based on the methodology from the project presentation
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional

class AdaptiveLearner:
    """Adaptive learning system that personalizes lessons based on student performance"""
    
    def __init__(self, db_path: str = 'data/local_database.db'):
        """
        Initialize adaptive learner
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables for student progress"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Students table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                name TEXT,
                age INTEGER,
                level TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Progress table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT,
                lesson_id TEXT,
                pronunciation_score REAL,
                comprehension_score REAL,
                vocabulary_score REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(student_id)
            )
        ''')
        
        # Learning profile table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_profile (
                student_id TEXT PRIMARY KEY,
                current_level TEXT,
                difficulty_level REAL,
                vocabulary_strength REAL,
                learning_curve REAL,
                weak_phonemes TEXT,
                strong_areas TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(student_id)
            )
        ''')
        
        # Lesson history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lesson_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT,
                lesson_id TEXT,
                lesson_type TEXT,
                completed BOOLEAN,
                time_spent INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(student_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def register_student(self, student_id: str, name: str, age: int, initial_level: str = 'beginner'):
        """
        Register a new student
        
        Args:
            student_id: Unique student identifier
            name: Student name
            age: Student age
            initial_level: Initial proficiency level
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO students (student_id, name, age, level)
                VALUES (?, ?, ?, ?)
            ''', (student_id, name, age, initial_level))
            
            # Initialize learning profile
            cursor.execute('''
                INSERT OR REPLACE INTO learning_profile 
                (student_id, current_level, difficulty_level, vocabulary_strength, learning_curve)
                VALUES (?, ?, ?, ?, ?)
            ''', (student_id, initial_level, 0.5, 0.5, 0.0))
            
            conn.commit()
        except Exception as e:
            print(f"Error registering student: {e}")
        finally:
            conn.close()
    
    def update_progress(self, 
                       student_id: str,
                       lesson_id: str,
                       pronunciation_score: float,
                       comprehension_score: Optional[float] = None,
                       vocabulary_score: Optional[float] = None):
        """
        Update student progress after a lesson
        
        Args:
            student_id: Student identifier
            lesson_id: Lesson identifier
            pronunciation_score: Pronunciation accuracy (0-100)
            comprehension_score: Comprehension score (0-100)
            vocabulary_score: Vocabulary score (0-100)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO progress 
                (student_id, lesson_id, pronunciation_score, comprehension_score, vocabulary_score)
                VALUES (?, ?, ?, ?, ?)
            ''', (student_id, lesson_id, pronunciation_score, comprehension_score, vocabulary_score))
            
            # Update learning profile
            self._update_learning_profile(cursor, student_id, pronunciation_score)
            
            conn.commit()
        except Exception as e:
            print(f"Error updating progress: {e}")
        finally:
            conn.close()
    
    def _update_learning_profile(self, cursor, student_id: str, score: float):
        """Update learning profile based on performance"""
        # Get recent performance
        cursor.execute('''
            SELECT AVG(pronunciation_score) as avg_score,
                   COUNT(*) as lesson_count
            FROM progress
            WHERE student_id = ?
            ORDER BY timestamp DESC
            LIMIT 10
        ''', (student_id,))
        
        result = cursor.fetchone()
        if result and result[1] > 0:
            avg_score = result[0]
            lesson_count = result[1]
            
            # Calculate difficulty level (0.0 = easy, 1.0 = hard)
            if avg_score >= 85:
                difficulty = min(1.0, 0.5 + (lesson_count * 0.05))
            elif avg_score >= 70:
                difficulty = 0.5
            else:
                difficulty = max(0.0, 0.5 - ((70 - avg_score) / 100))
            
            # Calculate learning curve (improvement rate)
            cursor.execute('''
                SELECT pronunciation_score
                FROM progress
                WHERE student_id = ?
                ORDER BY timestamp
                LIMIT 5
            ''', (student_id,))
            
            early_scores = [row[0] for row in cursor.fetchall()]
            if len(early_scores) >= 3:
                early_avg = sum(early_scores) / len(early_scores)
                learning_curve = (avg_score - early_avg) / max(1, lesson_count)
            else:
                learning_curve = 0.0
            
            # Update profile
            cursor.execute('''
                UPDATE learning_profile
                SET difficulty_level = ?,
                    learning_curve = ?,
                    last_updated = CURRENT_TIMESTAMP
                WHERE student_id = ?
            ''', (difficulty, learning_curve, student_id))
    
    def get_next_lesson(self, student_id: str) -> Dict:
        """
        Get next lesson recommendation based on student profile
        
        Args:
            student_id: Student identifier
        
        Returns:
            Dictionary with recommended lesson details
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get student profile
            cursor.execute('''
                SELECT current_level, difficulty_level, vocabulary_strength, weak_phonemes
                FROM learning_profile
                WHERE student_id = ?
            ''', (student_id,))
            
            profile = cursor.fetchone()
            if not profile:
                return self._get_default_lesson()
            
            level, difficulty, vocab_strength, weak_phonemes = profile
            
            # Get recent errors
            cursor.execute('''
                SELECT pronunciation_score
                FROM progress
                WHERE student_id = ?
                ORDER BY timestamp DESC
                LIMIT 5
            ''', (student_id,))
            
            recent_scores = [row[0] for row in cursor.fetchall()]
            avg_recent = sum(recent_scores) / len(recent_scores) if recent_scores else 50.0
            
            # Determine lesson type and difficulty
            if avg_recent >= 80:
                lesson_type = 'advanced'
                lesson_difficulty = min(1.0, difficulty + 0.1)
            elif avg_recent >= 60:
                lesson_type = 'intermediate'
                lesson_difficulty = difficulty
            else:
                lesson_type = 'beginner'
                lesson_difficulty = max(0.0, difficulty - 0.1)
            
            return {
                'lesson_type': lesson_type,
                'difficulty': round(lesson_difficulty, 2),
                'focus_areas': self._parse_weak_phonemes(weak_phonemes),
                'vocabulary_level': vocab_strength,
                'recommended_duration': self._calculate_duration(lesson_difficulty)
            }
        
        except Exception as e:
            print(f"Error getting next lesson: {e}")
            return self._get_default_lesson()
        finally:
            conn.close()
    
    def _parse_weak_phonemes(self, weak_phonemes_str: Optional[str]) -> List[str]:
        """Parse weak phonemes from database"""
        if not weak_phonemes_str:
            return []
        try:
            return json.loads(weak_phonemes_str)
        except:
            return []
    
    def _calculate_duration(self, difficulty: float) -> int:
        """Calculate recommended lesson duration in minutes"""
        base_duration = 15
        return int(base_duration + (difficulty * 10))
    
    def _get_default_lesson(self) -> Dict:
        """Get default lesson when profile not found"""
        return {
            'lesson_type': 'beginner',
            'difficulty': 0.5,
            'focus_areas': [],
            'vocabulary_level': 0.5,
            'recommended_duration': 15
        }
    
    def get_student_stats(self, student_id: str) -> Dict:
        """Get comprehensive student statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Overall stats
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_lessons,
                    AVG(pronunciation_score) as avg_pronunciation,
                    AVG(comprehension_score) as avg_comprehension,
                    AVG(vocabulary_score) as avg_vocabulary,
                    MAX(timestamp) as last_lesson
                FROM progress
                WHERE student_id = ?
            ''', (student_id,))
            
            stats = cursor.fetchone()
            
            # Profile
            cursor.execute('''
                SELECT current_level, difficulty_level, learning_curve
                FROM learning_profile
                WHERE student_id = ?
            ''', (student_id,))
            
            profile = cursor.fetchone()
            
            return {
                'total_lessons': stats[0] or 0,
                'avg_pronunciation': round(stats[1] or 0, 2),
                'avg_comprehension': round(stats[2] or 0, 2) if stats[2] else None,
                'avg_vocabulary': round(stats[3] or 0, 2) if stats[3] else None,
                'last_lesson': stats[4],
                'current_level': profile[0] if profile else 'beginner',
                'difficulty_level': round(profile[1], 2) if profile else 0.5,
                'learning_curve': round(profile[2], 2) if profile else 0.0
            }
        
        except Exception as e:
            print(f"Error getting student stats: {e}")
            return {}
        finally:
            conn.close()

