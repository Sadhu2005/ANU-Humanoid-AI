"""
LangChain Service for ANU 6.0 Server
Handles review-based replies and data access using LangChain
"""

from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain, RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.vectorstores import MongoDBAtlasVectorSearch
from langchain.embeddings import OpenAIEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from typing import Dict, List, Optional
import os
from .database import ServerDatabase

class LangChainService:
    """LangChain service for intelligent responses and data access"""
    
    def __init__(self, db: ServerDatabase):
        """
        Initialize LangChain service
        
        Args:
            db: ServerDatabase instance
        """
        self.db = db
        
        # Initialize LLM (use OpenAI or local model)
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.llm = ChatOpenAI(
                temperature=0.7,
                model_name="gpt-3.5-turbo"
            )
            self.embeddings = OpenAIEmbeddings()
        else:
            # Fallback to local model or Gemini
            from langchain.llms import HuggingFacePipeline
            # Use local model if available
            self.llm = None
            self.embeddings = None
        
        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Initialize tools
        self.tools = self._create_tools()
        
        # Initialize agent
        if self.llm:
            self.agent = initialize_agent(
                tools=self.tools,
                llm=self.llm,
                agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
                memory=self.memory,
                verbose=True
            )
        else:
            self.agent = None
    
    def _create_tools(self) -> List[Tool]:
        """Create LangChain tools for data access"""
        tools = [
            Tool(
                name="GetStudentProgress",
                func=self._get_student_progress_tool,
                description="Get student learning progress and statistics. Input: student_id"
            ),
            Tool(
                name="GetStudentReviews",
                func=self._get_student_reviews_tool,
                description="Get student reviews and feedback. Input: student_id"
            ),
            Tool(
                name="GetLessonRecommendations",
                func=self._get_lesson_recommendations_tool,
                description="Get recommended lessons for a student. Input: student_id"
            ),
            Tool(
                name="GetAnalytics",
                func=self._get_analytics_tool,
                description="Get analytics data. Input: metric_name"
            )
        ]
        return tools
    
    def _get_student_progress_tool(self, student_id: str) -> str:
        """Tool function to get student progress"""
        stats = self.db.aggregate_student_stats(student_id)
        return f"Student {student_id} progress: {stats}"
    
    def _get_student_reviews_tool(self, student_id: str) -> str:
        """Tool function to get student reviews"""
        reviews = self.db.get_reviews(student_id=student_id)
        return f"Reviews for {student_id}: {reviews[:5]}"  # Last 5 reviews
    
    def _get_lesson_recommendations_tool(self, student_id: str) -> str:
        """Tool function to get lesson recommendations"""
        student = self.db.get_student(student_id)
        if student:
            level = student.get('level', 'beginner')
            lessons = self.db.get_lessons(level=level)
            return f"Recommended lessons for {student_id}: {lessons[:3]}"
        return f"No recommendations found for {student_id}"
    
    def _get_analytics_tool(self, metric: str) -> str:
        """Tool function to get analytics"""
        analytics = self.db.get_analytics(metric, days=30)
        return f"Analytics for {metric}: {analytics}"
    
    def generate_review_based_reply(self, student_id: str, 
                                   review_text: str) -> str:
        """
        Generate intelligent reply based on student review
        
        Args:
            student_id: Student identifier
            review_text: Review/feedback text from student
        
        Returns:
            Generated reply
        """
        # Get student context
        student = self.db.get_student(student_id)
        progress = self.db.get_student_progress(student_id, limit=10)
        reviews = self.db.get_reviews(student_id=student_id, limit=5)
        
        # Create prompt template
        prompt_template = PromptTemplate(
            input_variables=["student_name", "review", "progress", "history"],
            template="""
You are a helpful AI assistant for ANU 6.0, an educational robot helping rural students learn English.

Student: {student_name}
Review: {review}

Recent Progress:
{progress}

Review History:
{history}

Generate a personalized, encouraging, and helpful reply to the student's review. 
Be warm, supportive, and specific. Address their concerns and celebrate their progress.
Keep the response concise (2-3 sentences) and in simple English suitable for students aged 6-16.

Reply:
"""
        )
        
        # Format context
        student_name = student.get('name', 'Student') if student else 'Student'
        progress_summary = self._format_progress(progress)
        review_history = self._format_reviews(reviews)
        
        if self.llm:
            chain = LLMChain(llm=self.llm, prompt=prompt_template)
            reply = chain.run(
                student_name=student_name,
                review=review_text,
                progress=progress_summary,
                history=review_history
            )
        else:
            # Fallback response
            reply = f"Thank you for your feedback, {student_name}! We appreciate your input and will use it to improve your learning experience."
        
        # Save review
        self.db.add_review({
            'student_id': student_id,
            'review_text': review_text,
            'reply': reply,
            'type': 'feedback'
        })
        
        return reply
    
    def answer_question(self, question: str, student_id: Optional[str] = None) -> str:
        """
        Answer questions using LangChain agent
        
        Args:
            question: Question to answer
            student_id: Optional student ID for context
        
        Returns:
            Answer
        """
        if not self.agent:
            return "I'm sorry, the AI service is not available right now."
        
        # Add student context if provided
        if student_id:
            context = f"Student ID: {student_id}. "
            question = context + question
        
        try:
            response = self.agent.run(question)
            return response
        except Exception as e:
            print(f"Error in LangChain agent: {e}")
            return "I apologize, but I couldn't process that question. Please try rephrasing it."
    
    def _format_progress(self, progress: List[Dict]) -> str:
        """Format progress data for prompt"""
        if not progress:
            return "No recent progress data."
        
        summary = []
        for p in progress[:5]:
            summary.append(
                f"Score: {p.get('pronunciation_score', 0):.1f}% "
                f"on {p.get('timestamp', 'unknown')}"
            )
        return "\n".join(summary)
    
    def _format_reviews(self, reviews: List[Dict]) -> str:
        """Format reviews for prompt"""
        if not reviews:
            return "No previous reviews."
        
        summary = []
        for r in reviews[:3]:
            summary.append(f"Review: {r.get('review_text', 'N/A')}")
        return "\n".join(summary)
    
    def generate_lesson_feedback(self, student_id: str, lesson_id: str,
                                performance_data: Dict) -> str:
        """
        Generate personalized lesson feedback
        
        Args:
            student_id: Student identifier
            lesson_id: Lesson identifier
            performance_data: Performance metrics
        
        Returns:
            Feedback text
        """
        student = self.db.get_student(student_id)
        student_name = student.get('name', 'Student') if student else 'Student'
        
        score = performance_data.get('pronunciation_score', 0)
        errors = performance_data.get('errors', [])
        
        if score >= 90:
            feedback = f"Excellent work, {student_name}! You scored {score:.1f}%! Your pronunciation is very clear. Keep up the great practice!"
        elif score >= 75:
            feedback = f"Good job, {student_name}! You scored {score:.1f}%. You're making great progress. Focus on the sounds we practiced today."
        elif score >= 60:
            feedback = f"Nice try, {student_name}! You scored {score:.1f}%. Let's practice those tricky sounds again. Remember: {self._format_error_hints(errors)}"
        else:
            feedback = f"Keep practicing, {student_name}! You scored {score:.1f}%. Don't worry, learning takes time. Let's try this lesson again with some helpful tips."
        
        return feedback
    
    def _format_error_hints(self, errors: List[Dict]) -> str:
        """Format error hints for feedback"""
        if not errors:
            return ""
        
        hints = [error.get('hint', '') for error in errors[:3]]
        return ". ".join(hints)

