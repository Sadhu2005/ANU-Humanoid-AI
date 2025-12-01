"""
MongoDB Database Manager for ANU 6.0 Server
Handles all server-side database operations
"""

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from typing import Dict, List, Optional, Any
import os
from datetime import datetime
import json

class ServerDatabase:
    """MongoDB database manager for server"""
    
    def __init__(self, connection_string: Optional[str] = None, db_name: str = "anu_robot"):
        """
        Initialize MongoDB connection
        
        Args:
            connection_string: MongoDB connection string
            db_name: Database name
        """
        if connection_string is None:
            connection_string = os.getenv(
                'MONGODB_URI',
                'mongodb://localhost:27017/'
            )
        
        self.client = MongoClient(connection_string)
        self.db: Database = self.client[db_name]
        self._init_collections()
    
    def _init_collections(self):
        """Initialize collections with indexes"""
        # Students collection
        students = self.db.students
        students.create_index("student_id", unique=True)
        students.create_index("email")
        students.create_index("created_at")
        
        # Lessons collection
        lessons = self.db.lessons
        lessons.create_index("lesson_id", unique=True)
        lessons.create_index("level")
        lessons.create_index("difficulty")
        
        # Progress collection
        progress = self.db.progress
        progress.create_index([("student_id", 1), ("timestamp", -1)])
        progress.create_index("session_id")
        
        # Reviews collection
        reviews = self.db.reviews
        reviews.create_index([("student_id", 1), ("timestamp", -1)])
        reviews.create_index("lesson_id")
        
        # Analytics collection
        analytics = self.db.analytics
        analytics.create_index([("date", 1), ("metric", 1)])
        
        # Teacher dashboard data
        teachers = self.db.teachers
        teachers.create_index("teacher_id", unique=True)
        teachers.create_index("school_id")
    
    def add_student(self, student_data: Dict) -> bool:
        """Add or update student"""
        try:
            student_data['created_at'] = datetime.utcnow()
            student_data['updated_at'] = datetime.utcnow()
            
            self.db.students.update_one(
                {'student_id': student_data['student_id']},
                {'$set': student_data},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Error adding student: {e}")
            return False
    
    def get_student(self, student_id: str) -> Optional[Dict]:
        """Get student by ID"""
        return self.db.students.find_one({'student_id': student_id})
    
    def get_all_students(self, school_id: Optional[str] = None) -> List[Dict]:
        """Get all students, optionally filtered by school"""
        query = {}
        if school_id:
            query['school_id'] = school_id
        
        return list(self.db.students.find(query))
    
    def save_progress(self, progress_data: Dict):
        """Save learning progress"""
        progress_data['timestamp'] = datetime.utcnow()
        self.db.progress.insert_one(progress_data)
    
    def get_student_progress(self, student_id: str, limit: int = 100) -> List[Dict]:
        """Get student progress history"""
        return list(
            self.db.progress.find({'student_id': student_id})
            .sort('timestamp', -1)
            .limit(limit)
        )
    
    def add_review(self, review_data: Dict):
        """Add student review/feedback"""
        review_data['timestamp'] = datetime.utcnow()
        self.db.reviews.insert_one(review_data)
    
    def get_reviews(self, student_id: Optional[str] = None, 
                   lesson_id: Optional[str] = None) -> List[Dict]:
        """Get reviews, optionally filtered"""
        query = {}
        if student_id:
            query['student_id'] = student_id
        if lesson_id:
            query['lesson_id'] = lesson_id
        
        return list(
            self.db.reviews.find(query)
            .sort('timestamp', -1)
        )
    
    def log_interaction(self, student_id: str, session_id: Optional[str],
                       interaction_type: str, input_text: str,
                       output_text: str, intent: Optional[str] = None,
                       confidence: float = 0.0):
        """Log interaction"""
        interaction_data = {
            'student_id': student_id,
            'session_id': session_id,
            'interaction_type': interaction_type,
            'input_text': input_text,
            'output_text': output_text,
            'intent': intent,
            'confidence': confidence,
            'timestamp': datetime.utcnow()
        }
        self.db.interactions.insert_one(interaction_data)
    
    def add_lesson(self, lesson_data: Dict):
        """Add or update lesson"""
        lesson_data['updated_at'] = datetime.utcnow()
        self.db.lessons.update_one(
            {'lesson_id': lesson_data['lesson_id']},
            {'$set': lesson_data},
            upsert=True
        )
    
    def get_lessons(self, level: Optional[str] = None) -> List[Dict]:
        """Get lessons, optionally filtered by level"""
        query = {}
        if level:
            query['level'] = level
        
        return list(self.db.lessons.find(query))
    
    def save_analytics(self, metric: str, value: Any, metadata: Optional[Dict] = None):
        """Save analytics data"""
        analytics_data = {
            'metric': metric,
            'value': value,
            'date': datetime.utcnow().date(),
            'timestamp': datetime.utcnow(),
            'metadata': metadata or {}
        }
        self.db.analytics.insert_one(analytics_data)
    
    def get_analytics(self, metric: str, days: int = 30) -> List[Dict]:
        """Get analytics for a metric"""
        from datetime import timedelta
        start_date = datetime.utcnow() - timedelta(days=days)
        
        return list(
            self.db.analytics.find({
                'metric': metric,
                'timestamp': {'$gte': start_date}
            }).sort('timestamp', 1)
        )
    
    def aggregate_student_stats(self, student_id: str) -> Dict:
        """Aggregate comprehensive student statistics"""
        pipeline = [
            {'$match': {'student_id': student_id}},
            {'$group': {
                '_id': None,
                'avg_pronunciation': {'$avg': '$pronunciation_score'},
                'avg_comprehension': {'$avg': '$comprehension_score'},
                'avg_vocabulary': {'$avg': '$vocabulary_score'},
                'total_lessons': {'$sum': 1},
                'last_lesson': {'$max': '$timestamp'}
            }}
        ]
        
        result = list(self.db.progress.aggregate(pipeline))
        if result:
            return result[0]
        return {}
    
    def close(self):
        """Close database connection"""
        self.client.close()

