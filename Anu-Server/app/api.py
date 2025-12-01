"""
FastAPI Server for ANU 6.0
Handles all server-client interactions
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uvicorn

from .database import ServerDatabase
from .langchain_service import LangChainService
from .models import *

app = FastAPI(title="ANU 6.0 Server API", version="6.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database and services
db = ServerDatabase()
langchain_service = LangChainService(db)

# Dependency
def get_db():
    return db

# ==================== Student Endpoints ====================

@app.post("/api/students/register", response_model=Dict)
async def register_student(student: StudentCreate):
    """Register a new student"""
    try:
        student_data = student.dict()
        success = db.add_student(student_data)
        if success:
            return {"status": "success", "student_id": student.student_id}
        raise HTTPException(status_code=400, detail="Failed to register student")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/students/{student_id}", response_model=Dict)
async def get_student(student_id: str):
    """Get student information"""
    student = db.get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@app.get("/api/students", response_model=List[Dict])
async def get_all_students(school_id: Optional[str] = None):
    """Get all students"""
    return db.get_all_students(school_id)

# ==================== Progress Endpoints ====================

@app.post("/api/progress/save")
async def save_progress(progress: ProgressData):
    """Save student progress"""
    try:
        db.save_progress(progress.dict())
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/progress/{student_id}", response_model=List[Dict])
async def get_progress(student_id: str, limit: int = 100):
    """Get student progress history"""
    return db.get_student_progress(student_id, limit)

@app.get("/api/progress/{student_id}/stats", response_model=Dict)
async def get_progress_stats(student_id: str):
    """Get aggregated student statistics"""
    return db.aggregate_student_stats(student_id)

# ==================== Review Endpoints ====================

@app.post("/api/reviews/submit")
async def submit_review(review: ReviewData):
    """Submit student review and get AI-generated reply"""
    try:
        reply = langchain_service.generate_review_based_reply(
            review.student_id,
            review.review_text
        )
        return {
            "status": "success",
            "reply": reply,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reviews/{student_id}", response_model=List[Dict])
async def get_reviews(student_id: str):
    """Get student reviews"""
    return db.get_reviews(student_id=student_id)

# ==================== Lesson Endpoints ====================

@app.post("/api/lessons/create")
async def create_lesson(lesson: LessonData):
    """Create or update a lesson"""
    try:
        db.add_lesson(lesson.dict())
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/lessons", response_model=List[Dict])
async def get_lessons(level: Optional[str] = None):
    """Get lessons"""
    return db.get_lessons(level)

@app.get("/api/lessons/recommend/{student_id}", response_model=Dict)
async def recommend_lesson(student_id: str):
    """Get recommended lesson for student"""
    try:
        recommendations = langchain_service._get_lesson_recommendations_tool(student_id)
        return {"recommendations": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Analytics Endpoints ====================

@app.post("/api/analytics/save")
async def save_analytics(metric: str, value: float, metadata: Optional[Dict] = None):
    """Save analytics data"""
    try:
        db.save_analytics(metric, value, metadata)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/{metric}", response_model=List[Dict])
async def get_analytics(metric: str, days: int = 30):
    """Get analytics data"""
    return db.get_analytics(metric, days)

# ==================== Robot Communication Endpoints ====================

@app.post("/api/robot/sync")
async def sync_robot_data(sync_data: RobotSyncData):
    """Sync data from robot to server"""
    try:
        # Save progress
        if sync_data.progress:
            db.save_progress(sync_data.progress)
        
        # Save interactions
        if sync_data.interactions:
            for interaction in sync_data.interactions:
                db.log_interaction(
                    interaction['student_id'],
                    interaction.get('session_id'),
                    interaction['type'],
                    interaction['input'],
                    interaction['output'],
                    interaction.get('intent', ''),
                    interaction.get('confidence', 0.0)
                )
        
        return {"status": "success", "synced_at": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/robot/commands/{robot_id}", response_model=Dict)
async def get_robot_commands(robot_id: str):
    """Get pending commands for robot"""
    # In production, implement command queue
    return {"commands": [], "status": "no_commands"}

@app.post("/api/robot/status")
async def update_robot_status(status: RobotStatus):
    """Update robot status"""
    try:
        db.save_analytics("robot_status", 1.0, status.dict())
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== AI/LLM Endpoints ====================

@app.post("/api/ai/chat")
async def chat_with_ai(chat_request: ChatRequest):
    """Chat with AI assistant"""
    try:
        response = langchain_service.answer_question(
            chat_request.question,
            chat_request.student_id
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/feedback")
async def generate_feedback(feedback_request: FeedbackRequest):
    """Generate personalized feedback"""
    try:
        feedback = langchain_service.generate_lesson_feedback(
            feedback_request.student_id,
            feedback_request.lesson_id,
            feedback_request.performance_data
        )
        return {"feedback": feedback}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Health Check ====================

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "6.0.0"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

