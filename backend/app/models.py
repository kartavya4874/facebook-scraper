from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.relationship import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String)
    user_tier = Column(String, default="free")  # free, premium
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    jobs = relationship("Job", back_populates="owner")

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    group_urls = Column(JSON)  # List of Facebook group URLs
    status = Column(String, default="created")  # created, running, paused, completed, failed
    config = Column(JSON)  # Scraping configuration
    total_posts = Column(Integer, default=0)
    last_run = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    owner = relationship("User", back_populates="jobs")
    posts = relationship("Post", back_populates="job")
    logs = relationship("JobLog", back_populates="job")

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    post_id = Column(String, unique=True, index=True)
    group_name = Column(String)
    author_name = Column(String)
    author_url = Column(String)
    content = Column(Text)
    timestamp = Column(DateTime)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    post_url = Column(String)
    media_urls = Column(JSON)
    scraped_at = Column(DateTime, server_default=func.now())
    
    job = relationship("Job", back_populates="posts")

class JobLog(Base):
    __tablename__ = "job_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    level = Column(String)  # INFO, WARNING, ERROR
    message = Column(Text)
    timestamp = Column(DateTime, server_default=func.now())
    
    job = relationship("Job", back_populates="logs")

