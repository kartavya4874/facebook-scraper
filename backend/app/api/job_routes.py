from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from ..database import get_db
from ..auth import get_current_user
from ..models import User, Job, JobLog
from ..tasks import scrape_facebook_group

router = APIRouter(prefix="/jobs", tags=["jobs"])

class JobCreate(BaseModel):
    name: str
    group_urls: List[str]
    config: Optional[dict] = {}

class JobResponse(BaseModel):
    id: int
    name: str
    group_urls: List[str]
    status: str
    config: dict
    total_posts: int
    created_at: datetime
    updated_at: datetime
    last_run: Optional[datetime]

class JobLogResponse(BaseModel):
    id: int
    level: str
    message: str
    timestamp: datetime

@router.get("/", response_model=List[JobResponse])
def get_jobs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    jobs = db.query(Job).filter(Job.user_id == current_user.id).all()
    return jobs

@router.post("/", response_model=JobResponse)
def create_job(job: JobCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check user limits
    if current_user.user_tier == "free":
        existing_jobs = db.query(Job).filter(Job.user_id == current_user.id).count()
        if existing_jobs >= 5:
            raise HTTPException(status_code=400, detail="Free users limited to 5 jobs")
        
        if len(job.group_urls) > 3:
            raise HTTPException(status_code=400, detail="Free users limited to 3 groups per job")
    
    db_job = Job(
        user_id=current_user.id,
        name=job.name,
        group_urls=job.group_urls,
        config=job.config
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    
    return db_job

@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.post("/{job_id}/start")
def start_job(job_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status == "running":
        raise HTTPException(status_code=400, detail="Job is already running")
    
    # Start the scraping task
    scrape_facebook_group.delay(job_id)
    
    job.status = "running"
    db.commit()
    
    return {"message": "Job started successfully"}

@router.post("/{job_id}/stop")
def stop_job(job_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job.status = "paused"
    db.commit()
    
    return {"message": "Job stopped successfully"}

@router.delete("/{job_id}")
def delete_job(job_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    db.delete(job)
    db.commit()
    
    return {"message": "Job deleted successfully"}

@router.get("/{job_id}/logs", response_model=List[JobLogResponse])
def get_job_logs(job_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    logs = db.query(JobLog).filter(JobLog.job_id == job_id).order_by(JobLog.timestamp.desc()).limit(100).all()
    return logs
