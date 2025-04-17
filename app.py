from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import os
import tempfile
from typing import List
import json

from scripts import JobDescriptionProcessor, ResumeProcessor
from scripts.similarity.get_score import get_score
from scripts.utils import init_logging_config

# Initialize logging
init_logging_config()

app = FastAPI(title="Resume Matcher API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Create temporary directories for processing
TEMP_DIR = tempfile.mkdtemp()
os.chdir(TEMP_DIR)  # Change to temp directory

# Create necessary directories
os.makedirs("Data/Resumes", exist_ok=True)
os.makedirs("Data/JobDescription", exist_ok=True)
os.makedirs("Data/Processed/Resumes", exist_ok=True)
os.makedirs("Data/Processed/JobDescription", exist_ok=True)

@app.post("/match")
async def match_resume_job(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):
    """
    Match a resume with a job description and return similarity score and common keywords
    """
    try:
        # Save uploaded resume temporarily
        resume_path = os.path.join("Data", "Resumes", resume.filename)
        with open(resume_path, "wb") as f:
            f.write(await resume.read())
        
        # Save job description to a temporary file
        jd_path = os.path.join("Data", "JobDescription", "job_description.txt")
        with open(jd_path, "w", encoding="utf-8") as f:
            f.write(job_description)
        
        # Process resume
        resume_processor = ResumeProcessor(resume.filename)
        resume_processor.process()
        
        # Process job description
        jd_processor = JobDescriptionProcessor("job_description.txt")
        jd_processor.process()
        
        # Get processed files - find the actual filenames with unique IDs
        processed_resumes = [f for f in os.listdir("Data/Processed/Resumes") if f.startswith(f"Resume-{resume.filename}")]
        processed_jds = [f for f in os.listdir("Data/Processed/JobDescription") if f.startswith("JobDescription-job_description.txt")]
        
        if not processed_resumes:
            raise FileNotFoundError(f"No processed resume file found for {resume.filename}")
        if not processed_jds:
            raise FileNotFoundError("No processed job description file found")
            
        processed_resume = os.path.join("Data", "Processed", "Resumes", processed_resumes[0])
        processed_jd = os.path.join("Data", "Processed", "JobDescription", processed_jds[0])
        
        # Debug: Print paths and check if files exist
        print(f"Current directory: {os.getcwd()}")
        print(f"Resume path: {resume_path}")
        print(f"JD path: {jd_path}")
        print(f"Processed resume path: {processed_resume}")
        print(f"Processed JD path: {processed_jd}")
        print(f"Files in Data/Resumes: {os.listdir('Data/Resumes')}")
        print(f"Files in Data/JobDescription: {os.listdir('Data/JobDescription')}")
        print(f"Files in Data/Processed/Resumes: {os.listdir('Data/Processed/Resumes')}")
        print(f"Files in Data/Processed/JobDescription: {os.listdir('Data/Processed/JobDescription')}")
        
        # Read processed files
        with open(processed_resume) as f:
            resume_data = json.load(f)
        
        with open(processed_jd) as f:
            jd_data = json.load(f)
        
        # Get keywords and debug their contents
        resume_keywords = resume_data["extracted_keywords"]
        jd_keywords = jd_data["extracted_keywords"]
        
        print(f"Resume keywords: {resume_keywords}")
        print(f"Job description keywords: {jd_keywords}")
        
        # Calculate similarity score
        resume_string = " ".join(resume_keywords)
        jd_string = " ".join(jd_keywords)
        result = get_score(resume_string, jd_string)
        similarity_score = round(result[0].score * 100, 2)
        
        # Find common keywords - normalize case and handle duplicates
        resume_keywords_set = {kw.lower().strip() for kw in resume_keywords}
        jd_keywords_set = {kw.lower().strip() for kw in jd_keywords}
        common_keywords = list(resume_keywords_set & jd_keywords_set)
        
        # Find keywords that are in resume but not in job description
        resume_only_keywords = list(resume_keywords_set - jd_keywords_set)
        
        # Find keywords that are in job description but not in resume
        jd_only_keywords = list(jd_keywords_set - resume_keywords_set)
        
        print(f"Common keywords found: {common_keywords}")
        print(f"Resume-only keywords: {resume_only_keywords}")
        print(f"Job description-only keywords: {jd_only_keywords}")
        
        # Clean up temporary files
        os.remove(resume_path)
        os.remove(jd_path)
        os.remove(processed_resume)
        os.remove(processed_jd)
        
        return {
            "similarity_score": similarity_score,
            "common_keywords": common_keywords,
            "resume_only_keywords": resume_only_keywords,
            "job_description_only_keywords": jd_only_keywords
        }
        
    except Exception as e:
        print(f"Error details: {str(e)}")
        print(f"Current directory: {os.getcwd()}")
        print(f"TEMP_DIR: {TEMP_DIR}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 