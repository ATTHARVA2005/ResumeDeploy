# backend/main.py

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import os
import json
from typing import List, Optional, Annotated, Dict, Any
from datetime import timedelta

# Import all necessary modules
from . import models, database, auth
from .resume_parser import ResumeParser # Updated usage for ResumeParser
# REMOVED: from .skill_extractor import SkillExtractor (as it's being removed)
from .matcher import SkillMatcher
from .utils import save_upload_file, delete_file, FileValidator

app = FastAPI(title="ResumeRank", version="1.0.0")

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Database Initialization ---
db_operations = database.Database()
@app.on_event("startup")
def startup_event():
    db_operations.init_database()
    print("Database startup complete.")

# --- Instantiated Classes ---
resume_parser = ResumeParser() # Instance of our updated ResumeParser
# REMOVED: skill_extractor = SkillExtractor() (as it's being removed)
matcher = SkillMatcher()

UPLOADS_DIR = "uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)

# --- Static File and HTML Page Serving ---
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_landing_page():
    return FileResponse("frontend/index.html")

@app.get("/login", response_class=HTMLResponse)
async def serve_login_page():
    return FileResponse("frontend/login.html")

@app.get("/signup", response_class=HTMLResponse)
async def serve_signup_page():
    return FileResponse("frontend/signup.html")
    
@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    return FileResponse("frontend/dashboard.html")

@app.get("/uploaded-resumes", response_class=HTMLResponse)
async def serve_uploaded_resumes():
    return FileResponse("frontend/uploaded_resumes.html")

@app.get("/job-descriptions-page", response_class=HTMLResponse)
async def serve_job_descriptions():
    return FileResponse("frontend/job_descriptions.html")


# --- Authentication Endpoints ---
@app.post("/api/register", response_model=models.User)
def register_user(user: models.UserCreate, db: Session = Depends(auth.get_db_session)):
    db_user = db_operations.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = auth.get_password_hash(user.password)
    return db_operations.create_user(db=db, email=user.email, hashed_password=hashed_password)

@app.post("/api/login", response_model=models.Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], 
    db: Session = Depends(auth.get_db_session)
):
    user = db_operations.get_user_by_email(db, email=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# --- PROTECTED: Resume Endpoints ---
@app.post("/api/upload-resume", response_model=dict)
async def upload_resume(
    current_user: Annotated[models.User, Depends(auth.get_current_user)],
    db: Annotated[Session, Depends(auth.get_db_session)],
    file: UploadFile = File(...)
):
    is_valid, message = FileValidator.is_valid_file(file)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)
    
    file_path = None
    try:
        # Save the uploaded file temporarily to extract text
        file_path = await save_upload_file(file, UPLOADS_DIR)
        
        # Extract raw text using local parser
        raw_text = resume_parser.extract_text(file_path)
        
        # Use Gemini to parse and structure the extracted text
        parsed_data_from_gemini = await resume_parser.parse_text_with_gemini(raw_text)
        
        # Extract data fields from Gemini's structured output
        filename_to_save = file.filename # Use original filename for record
        extracted_skills = parsed_data_from_gemini.get('extracted_skills', [])
        experience_entries = parsed_data_from_gemini.get('experience', [])
        total_years_experience = parsed_data_from_gemini.get('total_years_experience', 0)
        highest_education_level = parsed_data_from_gemini.get('highest_education_level', None)
        major = parsed_data_from_gemini.get('major', None)

        resume_id = db_operations.save_resume(
            db=db, user_id=current_user.id,
            filename=filename_to_save,
            file_path=file_path, # Store the path to the temporary file for now
            raw_text=raw_text, # Store the raw text that Gemini processed
            extracted_skills=extracted_skills,
            experience=experience_entries,
            total_years_experience=total_years_experience,
            highest_education_level=highest_education_level,
            major=major
        )
        return {"status": "success", "message": "Resume uploaded and processed successfully.", "resume_id": resume_id}
    except Exception as e:
        # It's crucial to delete the temporary file even if an error occurs
        if file_path and os.path.exists(file_path): delete_file(file_path)
        print(f"Error processing resume: {str(e)}") # Log the error for debugging
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")
    finally:
        # Ensure temporary file is deleted after processing (success or failure)
        # This will delete the file immediately after its content is read and processed by Gemini
        if file_path and os.path.exists(file_path): delete_file(file_path)

@app.get("/api/resumes", response_model=List[models.Resume])
async def get_all_resumes_for_current_user(
    current_user: Annotated[models.User, Depends(auth.get_current_user)],
    db: Annotated[Session, Depends(auth.get_db_session)]
):
    return db_operations.get_all_resumes_for_user(db, user_id=current_user.id)

@app.get("/api/resume/{resume_id}", response_model=models.Resume)
async def get_resume_details(
    resume_id: int,
    current_user: Annotated[models.User, Depends(auth.get_current_user)],
    db: Annotated[Session, Depends(auth.get_db_session)]
):
    resume_db = db.query(database.Resume).filter(database.Resume.id == resume_id).first()
    if not resume_db:
        raise HTTPException(status_code=404, detail="Resume not found.")
    if resume_db.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this resume.")
    return resume_db

@app.delete("/api/resume/{resume_id}", response_model=dict)
async def delete_resume(
    resume_id: int,
    current_user: Annotated[models.User, Depends(auth.get_current_user)],
    db: Annotated[Session, Depends(auth.get_db_session)]
):
    resume_db = db.query(database.Resume).filter(database.Resume.id == resume_id).first()
    if not resume_db:
        raise HTTPException(status_code=404, detail="Resume not found.")
    if resume_db.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this resume.")
    
    # Also delete the associated file if it exists and still points to a local file
    if resume_db.file_path and os.path.exists(resume_db.file_path):
        delete_file(resume_db.file_path)

    db.delete(resume_db)
    db.commit()
    return {"status": "success", "message": "Resume deleted successfully."}

# --- PROTECTED: Job Description Endpoints ---
@app.post("/api/job-description", response_model=dict)
async def add_job_description(
    job_desc: models.JobDescription, # Simplified Pydantic model now
    current_user: Annotated[models.User, Depends(auth.get_current_user)],
    db: Annotated[Session, Depends(auth.get_db_session)]
):
    # Use Gemini to parse and structure the job description
    parsed_job_data_from_gemini = await resume_parser.parse_job_description_with_gemini(job_desc.description)

    job_id = db_operations.save_job_description(
        db=db, user_id=current_user.id,
        title=parsed_job_data_from_gemini.get('title', job_desc.title), # Use Gemini's title, fallback to user input
        company=parsed_job_data_from_gemini.get('company', job_desc.company), # Use Gemini's company, fallback to user input
        description=job_desc.description, # Keep the original description
        required_skills=parsed_job_data_from_gemini.get('required_skills', []),
        required_experience_years=parsed_job_data_from_gemini.get('required_experience_years', 0),
        required_certifications=parsed_job_data_from_gemini.get('required_certifications', []),
        required_education_level=parsed_job_data_from_gemini.get('required_education_level', None),
        required_major=parsed_job_data_from_gemini.get('required_major', None)
    )
    return {"status": "success", "message": "Job description added and processed successfully.", "job_id": job_id}

@app.get("/api/job-descriptions", response_model=List[models.Job])
async def get_all_job_descriptions_for_current_user(
    current_user: Annotated[models.User, Depends(auth.get_current_user)],
    db: Annotated[Session, Depends(auth.get_db_session)]
):
    return db_operations.get_all_job_descriptions_for_user(db, user_id=current_user.id)

# --- Endpoints for managing a single job ---

@app.get("/api/job-description/{job_id}", response_model=models.Job)
async def get_job_description_details(
    job_id: int,
    current_user: Annotated[models.User, Depends(auth.get_current_user)],
    db: Annotated[Session, Depends(auth.get_db_session)]
):
    job_db = db.query(database.Job).filter(database.Job.id == job_id).first()
    if not job_db:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job_db.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this job.")
    return job_db

@app.put("/api/job-description/{job_id}", response_model=models.Job)
async def update_job_description(
    job_id: int,
    job_desc: models.JobDescription, # Simplified Pydantic model now
    current_user: Annotated[models.User, Depends(auth.get_current_user)],
    db: Annotated[Session, Depends(auth.get_db_session)]
):
    job_db = db.query(database.Job).filter(database.Job.id == job_id).first()
    if not job_db:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job_db.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this job.")

    # Use Gemini to re-parse and structure the updated job description
    parsed_job_data_from_gemini = await resume_parser.parse_job_description_with_gemini(job_desc.description)

    # Update fields from Gemini's output
    job_db.title = parsed_job_data_from_gemini.get('title', job_desc.title) # Use Gemini's title, fallback to user input
    job_db.company = parsed_job_data_from_gemini.get('company', job_desc.company) # Use Gemini's company, fallback to user input
    job_db.description = job_desc.description # Keep the original description
    job_db.required_experience_years = parsed_job_data_from_gemini.get('required_experience_years', 0)
    job_db.required_certifications = json.dumps(parsed_job_data_from_gemini.get('required_certifications', []))
    job_db.required_education_level = parsed_job_data_from_gemini.get('required_education_level', None)
    job_db.required_major = parsed_job_data_from_gemini.get('major', None)

    job_db.required_skills = json.dumps(parsed_job_data_from_gemini.get('required_skills', []))
    
    db.commit()
    db.refresh(job_db)
    return job_db

@app.delete("/api/job-description/{job_id}", response_model=dict)
async def delete_job_description(
    job_id: int,
    current_user: Annotated[models.User, Depends(auth.get_current_user)],
    db: Annotated[Session, Depends(auth.get_db_session)]
):
    job_db = db.query(database.Job).filter(database.Job.id == job_id).first()
    if not job_db:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job_db.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this job.")
        
    db.delete(job_db)
    db.commit()
    return {"status": "success", "message": "Job description deleted successfully."}

@app.post("/api/match-resumes", response_model=List[models.MatchResultResponse])
async def match_resumes_for_user(
    current_user: Annotated[models.User, Depends(auth.get_current_user)],
    db: Annotated[Session, Depends(auth.get_db_session)],
    job_id: int = Form(...)
):
    # 1. Fetch the job and verify ownership
    job_db = db.query(database.Job).filter(database.Job.id == job_id).first()
    if not job_db:
        raise HTTPException(status_code=404, detail="Job description not found.")
    if job_db.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to match against this job.")

    # 2. Fetch all resumes for the current user
    resumes = db_operations.get_all_resumes_for_user(db, user_id=current_user.id)
    if not resumes:
        return [] # Return an empty list if the user has no resumes

    all_match_results = []
    job = models.Job.from_orm(job_db) # Convert to Pydantic model for easy access

    for resume_data in resumes:
        resume = models.Resume.from_orm(resume_data) # Convert to Pydantic model
        
        # 3. Calculate the match score
        score_data = matcher.calculate_match(
            resume_skills=resume.extracted_skills,
            job_skills=job.required_skills,
            resume_experience_years=resume.total_years_experience,
            job_required_experience_years=job.required_experience_years,
            job_required_certifications=job.required_certifications,
            resume_highest_education_level=resume.highest_education_level,
            resume_major=resume.major,
            job_required_education_level=job.required_education_level,
            job_required_major=job.required_major
        )
        
        all_match_results.append(models.MatchResultResponse(
            resume_id=resume.id,
            job_id=job.id,
            overall_score=score_data['overall_score'],
            matched_skills=score_data['matched_skills'],
            missing_skills=score_data['missing_skills'],
            additional_skills=score_data['additional_skills'],
            filename=resume.filename,
            match_details=score_data['match_details']
        ))
    
    all_match_results.sort(key=lambda x: x.overall_score, reverse=True)
    return all_match_results