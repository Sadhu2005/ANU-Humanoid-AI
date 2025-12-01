"""
Business Logic Services for ANU 6.0 Server
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .database import ServerDatabase

class AnalyticsService:
    """Service for analytics and reporting"""
    
    def __init__(self, db: ServerDatabase):
        self.db = db
    
    def get_dashboard_stats(self) -> Dict:
        """Get dashboard statistics"""
        students = self.db.get_all_students()
        
        total_students = len(students)
        active_sessions = 0  # Would need session tracking
        total_lessons = 0
        
        pronunciation_scores = []
        for student in students:
            stats = self.db.aggregate_student_stats(student['student_id'])
            if stats and stats.get('avg_pronunciation'):
                pronunciation_scores.append(stats['avg_pronunciation'])
        
        avg_pronunciation = sum(pronunciation_scores) / len(pronunciation_scores) if pronunciation_scores else 0
        
        return {
            'total_students': total_students,
            'active_sessions': active_sessions,
            'avg_pronunciation': round(avg_pronunciation, 2),
            'total_lessons': total_lessons
        }
    
    def get_student_progress_trend(self, student_id: str, days: int = 30) -> List[Dict]:
        """Get student progress trend over time"""
        progress = self.db.get_student_progress(student_id, limit=100)
        
        # Group by date
        trends = {}
        for p in progress:
            date = p['timestamp'].date() if isinstance(p['timestamp'], datetime) else datetime.fromisoformat(str(p['timestamp'])).date()
            if date not in trends:
                trends[date] = []
            trends[date].append(p.get('pronunciation_score', 0))
        
        # Calculate daily averages
        result = []
        for date, scores in sorted(trends.items()):
            result.append({
                'date': date.isoformat(),
                'avg_score': sum(scores) / len(scores),
                'count': len(scores)
            })
        
        return result

class LessonService:
    """Service for lesson management"""
    
    def __init__(self, db: ServerDatabase):
        self.db = db
    
    def recommend_lesson(self, student_id: str) -> Optional[Dict]:
        """Recommend lesson for student"""
        student = self.db.get_student(student_id)
        if not student:
            return None
        
        level = student.get('level', 'beginner')
        lessons = self.db.get_lessons(level=level)
        
        if not lessons:
            return None
        
        # Get student progress to recommend appropriate lesson
        stats = self.db.aggregate_student_stats(student_id)
        avg_score = stats.get('avg_pronunciation', 50.0)
        
        # Filter lessons by difficulty
        if avg_score >= 80:
            difficulty_filter = 'advanced'
        elif avg_score >= 60:
            difficulty_filter = 'intermediate'
        else:
            difficulty_filter = 'beginner'
        
        # Return first matching lesson
        for lesson in lessons:
            if lesson.get('difficulty', 0.5) <= (avg_score / 100):
                return lesson
        
        return lessons[0] if lessons else None

class NotificationService:
    """Service for notifications and alerts"""
    
    def __init__(self, db: ServerDatabase):
        self.db = db
    
    def check_student_alerts(self, student_id: str) -> List[Dict]:
        """Check for alerts for a student"""
        alerts = []
        
        stats = self.db.aggregate_student_stats(student_id)
        
        # Low performance alert
        if stats.get('avg_pronunciation', 100) < 50:
            alerts.append({
                'type': 'low_performance',
                'message': 'Student performance is below average. Consider additional support.',
                'severity': 'warning'
            })
        
        # No recent activity
        last_lesson = stats.get('last_lesson')
        if last_lesson:
            if isinstance(last_lesson, str):
                last_lesson = datetime.fromisoformat(last_lesson)
            days_since = (datetime.utcnow() - last_lesson).days
            if days_since > 7:
                alerts.append({
                    'type': 'inactive',
                    'message': f'Student has not had a lesson in {days_since} days.',
                    'severity': 'info'
                })
        
        return alerts

