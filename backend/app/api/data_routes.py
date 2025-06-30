from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import pandas as pd
import json
import io
from ..database import get_db
from ..auth import get_current_user
from ..models import User, Job, Post

router = APIRouter(prefix="/data", tags=["data"])

class PostResponse(BaseModel):
    id: int
    post_id: str
    group_name: str
    author_name: str
    content: str
    timestamp: datetime
    likes: int
    comments: int
    shares: int
    scraped_at: datetime

@router.get("/jobs/{job_id}/posts", response_model=List[PostResponse])
def get_job_posts(
    job_id: int, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000)
):
    # Verify job ownership
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    posts = db.query(Post).filter(Post.job_id == job_id).offset(skip).limit(limit).all()
    return posts

@router.get("/jobs/{job_id}/export/{format}")
def export_job_data(
    job_id: int, 
    format: str,
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # Verify job ownership
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get all posts for the job
    posts = db.query(Post).filter(Post.job_id == job_id).all()
    
    if not posts:
        raise HTTPException(status_code=404, detail="No data found for this job")
    
    # Convert to DataFrame
    posts_data = []
    for post in posts:
        posts_data.append({
            'post_id': post.post_id,
            'group_name': post.group_name,
            'author_name': post.author_name,
            'author_url': post.author_url,
            'content': post.content,
            'timestamp': post.timestamp,
            'likes': post.likes,
            'comments': post.comments,
            'shares': post.shares,
            'post_url': post.post_url,
            'scraped_at': post.scraped_at
        })
    
    df = pd.DataFrame(posts_data)
    
    if format.lower() == 'csv':
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type='text/csv',
            headers={"Content-Disposition": f"attachment; filename=job_{job_id}_data.csv"}
        )
    
    elif format.lower() == 'json':
        output = df.to_json(orient='records', date_format='iso')
        
        return StreamingResponse(
            io.BytesIO(output.encode()),
            media_type='application/json',
            headers={"Content-Disposition": f"attachment; filename=job_{job_id}_data.json"}
        )
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported format. Use 'csv' or 'json'")

@router.get("/stats")
def get_user_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    total_jobs = db.query(Job).filter(Job.user_id == current_user.id).count()
    total_posts = db.query(Post).join(Job).filter(Job.user_id == current_user.id).count()
    active_jobs = db.query(Job).filter(Job.user_id == current_user.id, Job.status == "running").count()
    
    return {
        "total_jobs": total_jobs,
        "total_posts": total_posts,
        "active_jobs": active_jobs,
        "user_tier": current_user.user_tier
    }

