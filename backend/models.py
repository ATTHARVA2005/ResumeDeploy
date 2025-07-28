# backend/models.py

from pydantic import BaseModel, Field, validator, ConfigDict, model_validator
from typing import List, Dict, Optional, Any
from datetime import datetime
import json
import math

# --- Helper Function for Validation ---
def parse_json_string(value):
    """Parses a JSON string into a Python list, returns as is otherwise."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return []
    return value

# --- Structured Data Models ---
class ExperienceEntry(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None

# --- User Models ---
class UserBase(BaseModel):
    email: str
    name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- Token Models ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# --- API Models ---
class JobDescription(BaseModel):
    title: str
    company: str
    description: str

class JobDescriptionURL(BaseModel):
    url: str

# NEW: Model for extracted job details from URL
class ExtractedJobDetails(BaseModel):
    title: str
    company: str
    description: str
    # You might also include these if you want to show them pre-parsed in the form
    # required_skills: List[str] = []
    # required_experience_years: Optional[int] = 0
    # required_certifications: List[str] = []
    # required_education_level: Optional[str] = None
    # required_major: Optional[str] = None


class MatchWeights(BaseModel):
    skills: float = Field(default=0.6, ge=0.0, le=1.0)
    experience: float = Field(default=0.2, ge=0.0, le=1.0)
    certifications: float = Field(default=0.1, ge=0.0, le=1.0)
    education: float = Field(default=0.1, ge=0.0, le=1.0)

    @model_validator(mode='after')
    def sum_weights_must_be_one(self):
        total_weights = self.skills + self.experience + self.certifications + self.education
        if not math.isclose(total_weights, 1.0, rel_tol=1e-5):
            raise ValueError(f"Sum of all weights must be approximately 1.0 (currently {total_weights})")
        return self

class Resume(BaseModel):
    id: int
    filename: str
    raw_text: str
    upload_date: Optional[datetime] = None
    experience: Optional[List[ExperienceEntry]] = []
    total_years_experience: Optional[int] = 0
    extracted_skills: List[str] = []
    highest_education_level: Optional[str] = None
    major: Optional[str] = None

    _parse_experience = validator('experience', pre=True, allow_reuse=True)(parse_json_string)
    _parse_extracted_skills = validator('extracted_skills', pre=True, allow_reuse=True)(parse_json_string)

    model_config = ConfigDict(from_attributes=True)
        
class Job(BaseModel):
    id: int
    title: str
    company: str
    description: str
    required_skills: List[str] = []
    created_date: Optional[datetime] = None
    required_experience_years: Optional[int] = None
    required_certifications: List[str] = []
    required_education_level: Optional[str] = None
    required_major: Optional[str] = None


    _parse_required_skills = validator('required_skills', pre=True, allow_reuse=True)(parse_json_string)
    _parse_required_certifications = validator('required_certifications', pre=True, allow_reuse=True)(parse_json_string)

    model_config = ConfigDict(from_attributes=True)

class MatchResult(BaseModel):
    id: Optional[int] = None
    resume_id: int
    job_id: int
    overall_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    additional_skills: List[str]
    match_date: Optional[datetime] = None

class MatchResultResponse(MatchResult):
    filename: str
    match_details: Dict[str, Any]