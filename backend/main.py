# backend/main.py

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session # Import Session for type hinting
import os
import json
from typing import List, Optional, Annotated # Keep Annotated for Python 3.9+

# Import custom modules
from .models import JobDescription, Resume, Job, MatchResult, ResumeScore
from .database import Database, SessionLocal, engine, Base

from .resume_parser import ResumeParser
from .skill_extractor import SkillExtractor
from .matcher import SkillMatcher
from .utils import save_upload_file, delete_file, FileValidator

# Renamed FastAPI title to "ResumeRank"
app = FastAPI(title="ResumeRank", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components (Database instance itself doesn't hold the session anymore)
db_operations = Database()

# --- Database Startup Event ---
@app.on_event("startup")
async def startup_event():
    """
    Event handler that runs when the FastAPI application starts up.
    It initializes the database tables using SQLAlchemy's Base.metadata.
    """
    print("Attempting to create/check database tables...")
    db_operations.init_database() # Call the init_database method from the Database class
    print("Database startup complete.")


# --- Dependency to get a database session ---
def get_db_session():
    """
    Dependency function to provide a database session.
    It yields a session and ensures it's closed after the request.
    This is how SQLAlchemy sessions are managed per request in FastAPI.
    """
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()

# Initialize other components
resume_parser = ResumeParser()
skill_extractor = SkillExtractor()
matcher = SkillMatcher()

# Create uploads directory if it doesn't exist
UPLOADS_DIR = "uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Serve static files from the frontend/static directory
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Serve images from the frontend/static/images directory
app.mount("/static/images", StaticFiles(directory="frontend/static/images"), name="images")


@app.get("/", response_class=HTMLResponse)
async def landing_page():
    """Serve the new landing page (index.html)."""
    try:
        with open("frontend/index.html", "r") as file:
            return HTMLResponse(content=file.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="index.html (landing page) not found. Ensure it's in the 'frontend' directory.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving landing page: {str(e)}")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    """Serve the main dashboard HTML file (now dashboard.html)."""
    try:
        with open("frontend/dashboard.html", "r") as file:
            return HTMLResponse(content=file.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="dashboard.html not found. Ensure it's in the 'frontend' directory.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving dashboard page: {str(e)}")

@app.get("/add-job", response_class=HTMLResponse)
async def add_job_page():
    """Serve the add_job.html page."""
    try:
        with open("frontend/add_job.html", "r") as file:
            return HTMLResponse(content=file.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="add_job.html not found. Ensure it's in the 'frontend' directory.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving add job page: {str(e)}")

@app.get("/uploaded-resumes", response_class=HTMLResponse)
async def uploaded_resumes_page():
    """Serve the uploaded_resumes.html page."""
    try:
        with open("frontend/uploaded_resumes.html", "r") as file:
            return HTMLResponse(content=file.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="uploaded_resumes.html not found. Ensure it's in the 'frontend' directory.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving uploaded resumes page: {str(e)}")

@app.get("/job-descriptions-page", response_class=HTMLResponse)
async def job_descriptions_page():
    """Serve the job_descriptions.html page."""
    try:
        with open("frontend/job_descriptions.html", "r") as file:
            return HTMLResponse(content=file.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="job_descriptions.html not found. Ensure it's in the 'frontend' directory.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving job descriptions page: {str(e)}")


@app.post("/api/upload-resume", response_model=dict)
async def upload_resume(db_session: Annotated[Session, Depends(get_db_session)], file: UploadFile = File(...)): # db_session first
    """
    Uploads a resume file, extracts text and skills, and saves data to the database.
    The physical file is saved temporarily and then deleted after processing.
    """
    is_valid, message = FileValidator.is_valid_file(file)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)

    file_path = None
    try:
        file_path = await save_upload_file(file, UPLOADS_DIR)
        
        resume_text = resume_parser.extract_text(file_path)
        if not resume_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from the resume. File might be empty or corrupted.")
        
        extracted_skills = skill_extractor.extract_skills(resume_text)
        
        resume_id = db_operations.save_resume(
            db_session=db_session,
            filename=file.filename,
            file_path=file_path,
            raw_text=resume_text,
            extracted_skills=extracted_skills
        )
        
        return {
            "resume_id": resume_id,
            "filename": file.filename,
            "extracted_skills": extracted_skills,
            "status": "success",
            "message": "Resume uploaded and processed successfully."
        }
        
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Detailed error during resume upload: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")
    finally:
        if file_path and os.path.exists(file_path):
            delete_file(file_path)

@app.post("/api/job-description", response_model=dict)
async def add_job_description(db_session: Annotated[Session, Depends(get_db_session)], job_desc: JobDescription): # FIX: Reordered parameters
    """Adds a job description to the database and extracts required skills."""
    try:
        required_skills = skill_extractor.extract_skills(job_desc.description)
        
        job_id = db_operations.save_job_description(
            db_session=db_session,
            title=job_desc.title,
            company=job_desc.company,
            description=job_desc.description,
            required_skills=required_skills
        )
        
        return {
            "job_id": job_id,
            "title": job_desc.title,
            "company": job_desc.company,
            "required_skills": required_skills,
            "status": "success",
            "message": "Job description added and skills extracted successfully."
        }
        
    except Exception as e:
        print(f"Detailed error during job description add: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing job description: {str(e)}")

class MatchResultResponse(MatchResult):
    filename: str

@app.post("/api/match-resumes", response_model=List[MatchResultResponse])
async def match_resumes(db_session: Annotated[Session, Depends(get_db_session)], job_id: int = Form(...)): # FIX: Reordered parameters
    """
    Matches all resumes against a specific job description and returns detailed match results.
    """
    try:
        job = db_operations.get_job_description(db_session, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job description not found.")
        
        resumes = db_operations.get_all_resumes(db_session)
        if not resumes:
            raise HTTPException(status_code=404, detail="No resumes found in the system to match.")
        
        all_match_results = []
        for resume in resumes:
            resume_skills_list = resume.get('extracted_skills', [])
            if not isinstance(resume_skills_list, list):
                try:
                    resume_skills_list = json.loads(resume_skills_list)
                except (json.JSONDecodeError, TypeError):
                    resume_skills_list = []

            score_data = matcher.calculate_match(
                resume_skills=resume_skills_list,
                job_skills=job['required_skills']
            )
            
            db_operations.save_match_result(
                db_session=db_session,
                resume_id=resume['id'],
                job_id=job['id'],
                overall_score=score_data['overall_score'],
                matched_skills=score_data['matched_skills'],
                missing_skills=score_data['missing_skills'],
                additional_skills=score_data['additional_skills']
            )

            all_match_results.append(MatchResultResponse(
                resume_id=resume['id'],
                job_id=job['id'],
                overall_score=score_data['overall_score'],
                matched_skills=score_data['matched_skills'],
                missing_skills=score_data['missing_skills'],
                additional_skills=score_data['additional_skills'],
                filename=resume['filename']
            ))
        
        all_match_results.sort(key=lambda x: x.overall_score, reverse=True)
        
        return all_match_results
        
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Detailed error during resume matching: {e}")
        raise HTTPException(status_code=500, detail=f"Error matching resumes: {str(e)}")

@app.get("/api/resumes", response_model=List[Resume])
async def get_all_resumes_api(db_session: Annotated[Session, Depends(get_db_session)]): # db_session first (no other params here)
    """Retrieves all uploaded resumes from the database."""
    try:
        resumes_data = db_operations.get_all_resumes(db_session)
        return [Resume(**r) for r in resumes_data]
    except Exception as e:
        print(f"Detailed error fetching all resumes: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching resumes: {str(e)}")

@app.get("/api/job-descriptions", response_model=List[Job])
async def get_all_job_descriptions_api(db_session: Annotated[Session, Depends(get_db_session)]): # db_session first (no other params here)
    """Retrieves all job descriptions from the database."""
    try:
        jobs_data = db_operations.get_all_job_descriptions(db_session)
        return [Job(**j) for j in jobs_data]
    except Exception as e:
        print(f"Detailed error fetching all job descriptions: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching job descriptions: {str(e)}")

@app.get("/api/resume/{resume_id}", response_model=Resume)
async def get_resume_details(resume_id: int, db_session: Annotated[Session, Depends(get_db_session)]): # FIX: Reordered parameters
    """Retrieves detailed information for a specific resume by ID."""
    try:
        resume = db_operations.get_resume(db_session, resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found.")
        return Resume(**resume)
    except Exception as e:
        print(f"Detailed error fetching resume {resume_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching resume: {str(e)}")

@app.get("/api/job-description/{job_id}", response_model=Job)
async def get_job_description_details(job_id: int, db_session: Annotated[Session, Depends(get_db_session)]): # FIX: Reordered parameters
    """Retrieves detailed information for a specific job description by ID."""
    try:
        job = db_operations.get_job_description(db_session, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job description not found.")
        return Job(**job)
    except Exception as e:
        print(f"Detailed error fetching job description {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching job description: {str(e)}")

@app.delete("/api/resume/{resume_id}", response_model=dict)
async def delete_resume(resume_id: int, db_session: Annotated[Session, Depends(get_db_session)]): # FIX: Reordered parameters
    """
    Deletes a resume from the database and its associated physical file.
    """
    try:
        resume_to_delete = db_operations.get_resume(db_session, resume_id)
        if not resume_to_delete:
            raise HTTPException(status_code=404, detail="Resume not found.")
        
        success = db_operations.delete_resume(db_session, resume_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete resume from database.")
        
        if resume_to_delete.get('file_path'):
            file_deleted = delete_file(resume_to_delete['file_path'])
            if not file_deleted:
                print(f"Warning: Could not delete physical file {resume_to_delete['file_path']} for resume ID {resume_id}.")
        
        return {"status": "success", "message": "Resume deleted successfully."}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Detailed error deleting resume {resume_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting resume: {str(e)}")

@app.delete("/api/job-description/{job_id}", response_model=dict)
async def delete_job_description(job_id: int, db_session: Annotated[Session, Depends(get_db_session)]): # FIX: Reordered parameters
    """
    Deletes a job description from the database.
    """
    try:
        job_to_delete = db_operations.get_job_description(db_session, job_id)
        if not job_to_delete:
            raise HTTPException(status_code=404, detail="Job description not found.")

        success = db_operations.delete_job_description(db_session, job_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete job description from database.")
            
        return {"status": "success", "message": "Job description deleted successfully."}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Detailed error deleting job description {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting job description: {str(e)}")


@app.get("/api/skills", response_model=dict)
async def get_available_skills():
    """
    Retrieves the content of the skills_database.json file.
    """
    try:
        skills_file_path = "data/skills_database.json"
        if not os.path.exists(skills_file_path):
            raise HTTPException(status_code=404, detail="skills_database.json not found. Please ensure it's in the 'data' directory.")
            
        with open(skills_file_path, "r") as file:
            skills_data = json.load(file)
        return skills_data
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error decoding skills_database.json. File might be malformed.")
    except Exception as e:
        print(f"Detailed error fetching skills: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching skills: {str(e)}")

# This __name__ == "__main__" block is primarily for direct script execution,
# but when running with `uvicorn run.py`, `run.py` handles the uvicorn.run call.
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
