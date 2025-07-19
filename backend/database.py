# backend/database.py

import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Any

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError

# --- Database Configuration ---
# Use DATABASE_URL environment variable for production (e.g., Render PostgreSQL)
# Fallback to SQLite for local development if DATABASE_URL is not set
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./resume_screening.db")

# Create a SQLAlchemy engine
# connect_args is needed for SQLite to allow multiple threads to access the same connection
# without issues, particularly with FastAPI's async nature.
# For PostgreSQL, this argument is not needed.
if "sqlite" in DATABASE_URL:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

# Create a SessionLocal class
# Each instance of SessionLocal will be a database session.
# The 'autocommit=False' and 'autoflush=False' settings ensure that changes are not
# immediately written to the database until session.commit() is called.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()

# --- SQLAlchemy ORM Models ---

class Resume(Base):
    """SQLAlchemy model for the 'resumes' table."""
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False) # Path to the stored file (local or S3 URL)
    raw_text = Column(String)
    extracted_skills = Column(String) # Stored as JSON string
    upload_date = Column(DateTime, default=datetime.now)

    # Define relationship to match_results
    match_results = relationship("MatchResult", back_populates="resume", cascade="all, delete-orphan")

    def to_dict(self):
        """Converts the SQLAlchemy object to a dictionary, parsing JSON fields."""
        return {
            "id": self.id,
            "filename": self.filename,
            "file_path": self.file_path,
            "raw_text": self.raw_text,
            "extracted_skills": json.loads(self.extracted_skills) if self.extracted_skills else [],
            "upload_date": self.upload_date.isoformat() if self.upload_date else None,
        }

class Job(Base):
    """SQLAlchemy model for the 'job_descriptions' table."""
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    description = Column(String, nullable=False)
    required_skills = Column(String) # Stored as JSON string
    created_date = Column(DateTime, default=datetime.now)

    # Define relationship to match_results
    match_results = relationship("MatchResult", back_populates="job", cascade="all, delete-orphan")

    def to_dict(self):
        """Converts the SQLAlchemy object to a dictionary, parsing JSON fields."""
        return {
            "id": self.id,
            "title": self.title,
            "company": self.company,
            "description": self.description,
            "required_skills": json.loads(self.required_skills) if self.required_skills else [],
            "created_date": self.created_date.isoformat() if self.created_date else None,
        }

class MatchResult(Base):
    """SQLAlchemy model for the 'match_results' table."""
    __tablename__ = "match_results"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False)
    overall_score = Column(Float)
    matched_skills = Column(String) # Stored as JSON string
    missing_skills = Column(String) # Stored as JSON string
    additional_skills = Column(String) # Stored as JSON string
    match_date = Column(DateTime, default=datetime.now)

    # Define relationships to parent tables
    resume = relationship("Resume", back_populates="match_results")
    job = relationship("Job", back_populates="match_results")

    def to_dict(self):
        """Converts the SQLAlchemy object to a dictionary, parsing JSON fields."""
        return {
            "id": self.id,
            "resume_id": self.resume_id,
            "job_id": self.job_id,
            "overall_score": self.overall_score,
            "matched_skills": json.loads(self.matched_skills) if self.matched_skills else [],
            "missing_skills": json.loads(self.missing_skills) if self.missing_skills else [],
            "additional_skills": json.loads(self.additional_skills) if self.additional_skills else [],
            "match_date": self.match_date.isoformat() if self.match_date else None,
        }

# --- Database Operations Class ---

class Database:
    def __init__(self):
        # No db_path needed anymore as it's handled by DATABASE_URL
        pass
    
    def init_database(self):
        """
        Initializes the database by creating all tables defined in Base.metadata.
        This should be called once at application startup.
        """
        try:
            Base.metadata.create_all(bind=engine)
            print("SQLAlchemy database tables created/checked successfully.")
        except SQLAlchemyError as e:
            print(f"SQLAlchemy database initialization error: {e}")
            raise # Re-raise to indicate a critical startup failure

    def get_db(self):
        """
        Dependency function to provide a database session.
        It yields a session and ensures it's closed after the request.
        """
        db_session = SessionLocal()
        try:
            yield db_session
        finally:
            db_session.close()

    # --- CRUD Operations using SQLAlchemy ORM ---

    def save_resume(self, db_session: Any, filename: str, file_path: str, raw_text: str, extracted_skills: List[str]) -> int:
        """Saves a resume to the database using SQLAlchemy session."""
        db_resume = Resume(
            filename=filename,
            file_path=file_path,
            raw_text=raw_text,
            extracted_skills=json.dumps(extracted_skills)
        )
        db_session.add(db_resume)
        db_session.commit()
        db_session.refresh(db_resume)
        return db_resume.id
    
    def save_job_description(self, db_session: Any, title: str, company: str, description: str, required_skills: List[str]) -> int:
        """Saves a job description to the database using SQLAlchemy session."""
        db_job = Job(
            title=title,
            company=company,
            description=description,
            required_skills=json.dumps(required_skills)
        )
        db_session.add(db_job)
        db_session.commit()
        db_session.refresh(db_job)
        return db_job.id
    
    def get_resume(self, db_session: Any, resume_id: int) -> Optional[Dict[str, Any]]:
        """Gets a specific resume by ID, returning as a dictionary."""
        resume = db_session.query(Resume).filter(Resume.id == resume_id).first()
        return resume.to_dict() if resume else None
    
    def get_job_description(self, db_session: Any, job_id: int) -> Optional[Dict[str, Any]]:
        """Gets a specific job description by ID, returning as a dictionary."""
        job = db_session.query(Job).filter(Job.id == job_id).first()
        return job.to_dict() if job else None
    
    def get_all_resumes(self, db_session: Any) -> List[Dict[str, Any]]:
        """Gets all resumes, returning as a list of dictionaries."""
        resumes = db_session.query(Resume).order_by(Resume.upload_date.desc()).all()
        return [r.to_dict() for r in resumes]
    
    def get_all_job_descriptions(self, db_session: Any) -> List[Dict[str, Any]]:
        """Gets all job descriptions, returning as a list of dictionaries."""
        jobs = db_session.query(Job).order_by(Job.created_date.desc()).all()
        return [j.to_dict() for j in jobs]
    
    def delete_resume(self, db_session: Any, resume_id: int) -> bool:
        """Deletes a resume by ID."""
        resume = db_session.query(Resume).filter(Resume.id == resume_id).first()
        if resume:
            db_session.delete(resume)
            db_session.commit()
            return True
        return False

    def delete_job_description(self, db_session: Any, job_id: int) -> bool:
        """Deletes a job description by ID."""
        job = db_session.query(Job).filter(Job.id == job_id).first()
        if job:
            db_session.delete(job)
            db_session.commit()
            return True
        return False
    
    def save_match_result(self, db_session: Any, resume_id: int, job_id: int, overall_score: float, 
                         matched_skills: List[str], missing_skills: List[str], 
                         additional_skills: List[str]) -> int:
        """Saves a match result to the database."""
        db_match = MatchResult(
            resume_id=resume_id,
            job_id=job_id,
            overall_score=overall_score,
            matched_skills=json.dumps(matched_skills),
            missing_skills=json.dumps(missing_skills),
            additional_skills=json.dumps(additional_skills)
        )
        db_session.add(db_match)
        db_session.commit()
        db_session.refresh(db_match)
        return db_match.id

    def get_match_results_for_resume(self, db_session: Any, resume_id: int) -> List[Dict[str, Any]]:
        """Gets all match results for a specific resume."""
        results = db_session.query(MatchResult).filter(MatchResult.resume_id == resume_id).order_by(MatchResult.match_date.desc()).all()
        return [r.to_dict() for r in results]

    def get_match_results_for_job(self, db_session: Any, job_id: int) -> List[Dict[str, Any]]:
        """Gets all match results for a specific job description."""
        results = db_session.query(MatchResult).filter(MatchResult.job_id == job_id).order_by(MatchResult.overall_score.desc(), MatchResult.match_date.desc()).all()
        return [r.to_dict() for r in results]

