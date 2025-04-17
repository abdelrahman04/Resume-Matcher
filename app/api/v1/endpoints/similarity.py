from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import json
import os
from scripts.similarity.get_similarity_score import get_similarity_score
from scripts.similarity.get_score import get_score

router = APIRouter()

@router.post("/score")
async def get_similarity_score_endpoint(resume: UploadFile = File(...), job_description: UploadFile = File(...)):
    try:
        # Read and process resume
        resume_content = await resume.read()
        resume_data = json.loads(resume_content)
        resume_keywords = resume_data.get("extracted_keywords", [])
        resume_string = " ".join(resume_keywords)

        # Read and process job description
        jd_content = await job_description.read()
        jd_data = json.loads(jd_content)
        jd_keywords = jd_data.get("extracted_keywords", [])
        jd_string = " ".join(jd_keywords)

        # Get similarity score using the more robust implementation
        result = get_similarity_score(resume_string, jd_string)
        
        # Format the result
        formatted_result = [{"text": r["text"], "score": float(r["score"])} for r in result]
        
        return {"similarity_score": formatted_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/score/batch")
async def get_similarity_score_batch_endpoint(resumes: List[UploadFile] = File(...), job_description: UploadFile = File(...)):
    try:
        # Read and process job description
        jd_content = await job_description.read()
        jd_data = json.loads(jd_content)
        jd_keywords = jd_data.get("extracted_keywords", [])
        jd_string = " ".join(jd_keywords)

        results = []
        for resume in resumes:
            # Read and process each resume
            resume_content = await resume.read()
            resume_data = json.loads(resume_content)
            resume_keywords = resume_data.get("extracted_keywords", [])
            resume_string = " ".join(resume_keywords)

            # Get similarity score
            result = get_similarity_score(resume_string, jd_string)
            
            # Format the result
            formatted_result = [{"text": r["text"], "score": float(r["score"])} for r in result]
            results.append({
                "resume_filename": resume.filename,
                "similarity_score": formatted_result
            })

        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 