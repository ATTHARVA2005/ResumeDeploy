# backend/database.py

import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Any

from sqlalchemy import create_engine, Column, String, Float, DateTime, ForeignKey, Text, Integer, Boolean
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError

# --- Database Configuration ---
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./resume_screening.db")

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# --- User Model ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    
    resumes = relationship("Resume", back_populates="owner", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="owner", cascade="all, delete-orphan")

# --- Resume Model ---
class Resume(Base):
    __tablename__ = "resumes"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    raw_text = Column(Text)
    extracted_skills = Column(String)
    upload_date = Column(DateTime, default=datetime.now)
    experience = Column(Text, default="[]")
    total_years_experience = Column(Integer, default=0)
    highest_education_level = Column(String, nullable=True)
    major = Column(String, nullable=True)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="resumes")

    match_results = relationship("MatchResult", back_populates="resume", cascade="all, delete-orphan")

# --- Job Model ---
class Job(Base):
    __tablename__ = "job_descriptions"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    required_skills = Column(String)
    created_date = Column(DateTime, default=datetime.now)
    required_experience_years = Column(Integer, default=None)
    required_certifications = Column(Text, default="[]")
    required_education_level = Column(String, nullable=True)
    required_major = Column(String, nullable=True)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="jobs")

    match_results = relationship("MatchResult", back_populates="job", cascade="all, delete-orphan")

# --- MatchResult Model ---
class MatchResult(Base):
    __tablename__ = "match_results"
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False)
    overall_score = Column(Float)
    matched_skills = Column(String)
    missing_skills = Column(String)
    additional_skills = Column(String)
    match_date = Column(DateTime, default=datetime.now)
    resume = relationship("Resume", back_populates="match_results")
    job = relationship("Job", back_populates="match_results")

# --- Database Operations Class ---
class Database:
    def init_database(self):
        try:
            Base.metadata.create_all(bind=engine)
            print("SQLAlchemy database tables created/checked successfully.")
        except SQLAlchemyError as e:
            print(f"SQLAlchemy database initialization error: {e}")
            raise

    # --- User Operations ---
    def get_user_by_email(self, db: Any, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def create_user(self, db: Any, email: str, hashed_password: str, name: Optional[str] = None, is_admin: bool = False) -> User:
        # Corrected: Instantiate User without 'is_admin' as a constructor arg,
        # then set the attribute directly.
        db_user = User(email=email, hashed_password=hashed_password, name=name)
        db_user.is_admin = is_admin # Set the is_admin attribute after instantiation

        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
           
    def get_user_by_id(self, db: Any, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    def get_all_users(self, db: Any) -> List[User]:
        return db.query(User).all()

    def delete_user(self, db: Any, user_id: int):
        user_to_delete = db.query(User).filter(User.id == user_id).first()
        if user_to_delete:
            db.delete(user_to_delete)
            db.commit()
            return True
        return False

    # --- Resume Operations ---
    def save_resume(self, db: Any, filename: str, file_path: str, raw_text: str, 
                    extracted_skills: List[str], user_id: int, experience: Optional[List[Dict]] = None, 
                    total_years_experience: Optional[int] = 0,
                    highest_education_level: Optional[str] = None,
                    major: Optional[str] = None
                    ) -> int:
        db_resume = Resume(
            filename=filename, file_path=file_path, raw_text=raw_text,
            extracted_skills=json.dumps(extracted_skills), user_id=user_id,
            experience=json.dumps(experience or []),
            total_years_experience=total_years_experience,
            highest_education_level=highest_education_level,
            major=major
        )
        db.add(db_resume)
        db.commit()
        db.refresh(db_resume)
        return db_resume.id

    def get_all_resumes_for_user(self, db: Any, user_id: int) -> List[Resume]:
        return db.query(Resume).filter(Resume.user_id == user_id).order_by(Resume.upload_date.desc()).all()

    # --- Job Description Operations ---
    def save_job_description(self, db: Any, title: str, company: str, description: str, 
                             required_skills: List[str], user_id: int, 
                             required_experience_years: Optional[int] = None,
                             required_certifications: Optional[List[str]] = None,
                             required_education_level: Optional[str] = None,
                             required_major: Optional[str] = None
                             ) -> int:
        db_job = Job(
            title=title, company=company, description=description,
            required_skills=json.dumps(required_skills), user_id=user_id,
            required_experience_years=required_experience_years,
            required_certifications=json.dumps(required_certifications or []),
            required_education_level=required_education_level,
            required_major=required_major
        )
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        return db_job.id

    def get_all_job_descriptions_for_user(self, db: Any, user_id: int) -> List[Job]:
        return db.query(Job).filter(Job.user_id == user_id).order_by(Job.created_date.desc()).all()