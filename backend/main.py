# backend/main.py

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import os
import json
from typing import List, Optional, Annotated, Dict, Any
from datetime import timedelta
from dotenv import load_dotenv # NEW
load_dotenv()

# Import all necessary modules
from . import models, database, auth
from .resume_parser import ResumeParser
from .matcher import SkillMatcher
from .utils import save_upload_file, delete_file, FileValidator, fetch_text_from_url

app = FastAPI(title="ResumeRank", version="1.0.0")

# ... (existing imports) ...

@app.get("/admin-panel", response_class=HTMLResponse)
async def serve_admin_panel():
    return FileResponse("frontend/admin_panel.html")

# NEW: Route for the List of Users page
@app.get("/admin-panel/users", response_class=HTMLResponse)
async def serve_admin_users_page():
    return FileResponse("frontend/admin_users.html")
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
    print("SQLAlchemy database tables created/checked successfully.")
    print("Database startup complete.")

    # Get admin credentials from environment variables (NEW)
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

    if not ADMIN_EMAIL or not ADMIN_PASSWORD:
        print("WARNING: ADMIN_EMAIL or ADMIN_PASSWORD environment variables are not set. Admin user will not be created.")
        print("Please set ADMIN_EMAIL and ADMIN_PASSWORD in your .env file or Render environment settings for production.")
    else:
        # Create an initial admin user if none exists
        db = database.SessionLocal()
        try:
            if not db_operations.get_user_by_email(db, email=ADMIN_EMAIL):
                print(f"Creating initial admin user: {ADMIN_EMAIL}")
                hashed_password = auth.get_password_hash(ADMIN_PASSWORD)
                db_operations.create_user(db, email=ADMIN_EMAIL, hashed_password=hashed_password, name="Admin User", is_admin=True)
            else:
                print(f"Admin user {ADMIN_EMAIL} already exists.")
        finally:
            db.close()


resume_parser = ResumeParser()
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

@app.get("/admin-login", response_class=HTMLResponse)
async def serve_admin_login_page():
    return FileResponse("frontend/admin_login.html")

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

@app.get("/admin-panel", response_class=HTMLResponse)
async def serve_admin_panel():
    return FileResponse("frontend/admin_panel.html")


# --- Authentication Endpoints ---
@app.post("/api/register", response_model=models.User)
def register_user(user: models.UserCreate, db: Session = Depends(auth.get_db_session)):
    db_user = db_operations.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = auth.get_password_hash(user.password)
    return db_operations.create_user(db=db, email=user.email, hashed_password=hashed_password, name=user.name, is_admin=False)

@app.post("/api/login", response_model=models.Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], 
    db: Annotated[Session, Depends(auth.get_db_session) ]
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

@app.post("/api/admin/login", response_model=models.Token)
async def login_for_admin_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(auth.get_db_session)]
):
    user = db_operations.get_user_by_email(db, email=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Access Denied: This login is for administrators only. Please use the User Login.",
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
        file_path = await save_upload_file(file, UPLOADS_DIR)
        raw_text = resume_parser.extract_text(file_path)
        parsed_data_from_gemini = await resume_parser.parse_text_with_gemini(raw_text)
        
        filename_to_save = file.filename
        extracted_skills = parsed_data_from_gemini.get('extracted_skills', [])
        experience_entries = parsed_data_from_gemini.get('experience', [])
        total_years_experience = parsed_data_from_gemini.get('total_years_experience', 0)
        highest_education_level = parsed_data_from_gemini.get('highest_education_level', None)
        major = parsed_data_from_gemini.get('major', None)

        resume_id = db_operations.save_resume(
            db=db, user_id=current_user.id,
            filename=filename_to_save,
            file_path=file_path,
            raw_text=raw_text,
            extracted_skills=extracted_skills,
            experience=experience_entries,
            total_years_experience=total_years_experience,
            highest_education_level=highest_education_level,
            major=major
        )
        return {"status": "success", "message": "Resume uploaded and processed successfully.", "resume_id": resume_id}
    except Exception as e:
        if file_path and os.path.exists(file_path): delete_file(file_path)
        print(f"Error processing resume: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")
    finally:
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
       
    if resume_db.file_path and os.path.exists(resume_db.file_path):
        delete_file(resume_db.file_path)

    db.delete(resume_db)
    db.commit()
    return {"status": "success", "message": "Resume deleted successfully."}

# --- PROTECTED: Job Description Endpoints ---
@app.post("/api/job-description", response_model=dict)
async def add_job_description(
    job_desc: models.JobDescription,
    current_user: Annotated[models.User, Depends(auth.get_current_user)],
    db: Annotated[Session, Depends(auth.get_db_session)]
):
    parsed_job_data_from_gemini = await resume_parser.parse_job_description_with_gemini(job_desc.description)

    job_id = db_operations.save_job_description(
        db=db, user_id=current_user.id,
        title=parsed_job_data_from_gemini.get('title', job_desc.title),
        company=parsed_job_data_from_gemini.get('company', job_desc.company),
        description=job_desc.description,
        required_skills=parsed_job_data_from_gemini.get('required_skills', []),
        required_experience_years=parsed_job_data_from_gemini.get('required_experience_years', 0),
        required_certifications=parsed_job_data_from_gemini.get('required_certifications', []),
        required_education_level=parsed_job_data_from_gemini.get('required_education_level', None),
        required_major=parsed_job_data_from_gemini.get('major', None)
    )
    return {"status": "success", "message": "Job description added and processed successfully.", "job_id": job_id}

# MODIFIED ENDPOINT: Extract Job Description from URL (returns data, doesn't save)
@app.post("/api/extract-job-from-url", response_model=models.ExtractedJobDetails) # CHANGED response_model
async def extract_job_from_url( # CHANGED function name to reflect action
    job_url_data: models.JobDescriptionURL,
    current_user: Annotated[models.User, Depends(auth.get_current_user)], # Still requires authentication
):
    try:
        raw_text_from_url = await fetch_text_from_url(job_url_data.url)
        if not raw_text_from_url.strip():
            raise HTTPException(status_code=400, detail="Could not extract meaningful text from the provided URL.")

        parsed_job_data_from_gemini = await resume_parser.parse_job_description_with_gemini(raw_text_from_url)
        
        # Return extracted data for frontend to pre-fill
        return models.ExtractedJobDetails(
            title=parsed_job_data_from_gemini.get('title', f"Job from URL: {job_url_data.url[:50]}..."),
            company=parsed_job_data_from_gemini.get('company', "Unknown Company"),
            description=raw_text_from_url # Always return the full raw text
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error processing job description from URL: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extract job description from URL: {str(e)}")

@app.get("/api/job-descriptions", response_model=List[models.Job])
async def get_all_job_descriptions_for_current_user(
    current_user: Annotated[models.User, Depends(auth.get_current_user)],
    db: Annotated[Session, Depends(auth.get_db_session)]
):
    return db_operations.get_all_job_descriptions_for_user(db, user_id=current_user.id)

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
    job_desc: models.JobDescription,
    current_user: Annotated[models.User, Depends(auth.get_current_user)],
    db: Annotated[Session, Depends(auth.get_db_session)]
):
    job_db = db.query(database.Job).filter(database.Job.id == job_id).first()
    if not job_db:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job_db.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this job.")

    parsed_job_data_from_gemini = await resume_parser.parse_job_description_with_gemini(job_desc.description)

    job_db.title = parsed_job_data_from_gemini.get('title', job_desc.title)
    job_db.company = parsed_job_data_from_gemini.get('company', job_desc.company)
    job_db.description = job_desc.description
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
    job_id: int = Form(...),
    weights: Optional[str] = Form(None)
):
    job_db = db.query(database.Job).filter(database.Job.id == job_id).first()
    if not job_db:
        raise HTTPException(status_code=404, detail="Job description not found.")
    if job_db.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to match against this job.")

    parsed_weights = None
    if weights:
        try:
            weights_dict = json.loads(weights)
            parsed_weights = models.MatchWeights(**weights_dict).dict()
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format for weights.")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid weights: {e}")

    resumes = db_operations.get_all_resumes_for_user(db, user_id=current_user.id)
    if not resumes:
        return []

    all_match_results = []
    job = models.Job.from_orm(job_db)

    for resume_data in resumes:
        resume = models.Resume.from_orm(resume_data)
        
        score_data = matcher.calculate_match(
            resume_skills=resume.extracted_skills,
            job_skills=job.required_skills,
            resume_experience_years=resume.total_years_experience,
            job_required_experience_years=job.required_experience_years,
            job_required_certifications=job.required_certifications,
            resume_highest_education_level=resume.highest_education_level,
            resume_major=resume.major,
            job_required_education_level=job.required_education_level,
            job_required_major=job.required_major,
            weights=parsed_weights
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

# --- ADMIN PANEL ENDPOINTS ---
@app.get("/api/admin/users", response_model=List[models.User])
async def get_all_users(
    current_admin: Annotated[models.User, Depends(auth.get_current_admin_user)],
    db: Annotated[Session, Depends(auth.get_db_session)]
):
    """
    Admin-only endpoint to retrieve all users.
    """
    return db_operations.get_all_users(db)

@app.delete("/api/admin/users/{user_id}", response_model=dict)
async def delete_user_account(
    user_id: int,
    current_admin: Annotated[models.User, Depends(auth.get_current_admin_user)],
    db: Annotated[Session, Depends(auth.get_db_session)]
):
    """
    Admin-only endpoint to delete a user account and all associated data.
    """
    if current_admin.id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin cannot delete their own account via this panel.")

    user_to_delete = db_operations.get_user_by_id(db, user_id)
    if not user_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if db_operations.delete_user(db, user_id):
        return {"status": "success", "message": f"User {user_id} and associated data deleted successfully."}
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete user.")