"""
Pydantic models for API requests/responses
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime

class StudentCreate(BaseModel):
    student_id: str
    name: str
    age: int
    level: str = "beginner"
    school_id: Optional[str] = None
    email: Optional[str] = None

class ProgressData(BaseModel):
    student_id: str
    lesson_id: str
    pronunciation_score: float
    comprehension_score: Optional[float] = None
    vocabulary_score: Optional[float] = None
    engagement_score: Optional[float] = None
    session_id: Optional[str] = None

class ReviewData(BaseModel):
    student_id: str
    review_text: str
    lesson_id: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)

class LessonData(BaseModel):
    lesson_id: str
    title: str
    level: str
    difficulty: float = Field(0.5, ge=0.0, le=1.0)
    content: Dict[str, Any]
    duration: int  # minutes

class RobotSyncData(BaseModel):
    robot_id: str
    progress: Optional[ProgressData] = None
    interactions: Optional[List[Dict]] = None
    sensor_data: Optional[Dict] = None

class RobotStatus(BaseModel):
    robot_id: str
    battery_level: float
    temperature: float
    network_status: str
    active_modules: List[str]

class ChatRequest(BaseModel):
    question: str
    student_id: Optional[str] = None

class FeedbackRequest(BaseModel):
    student_id: str
    lesson_id: str
    performance_data: Dict[str, Any]

