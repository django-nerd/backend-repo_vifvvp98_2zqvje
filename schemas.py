"""
Database Schemas for Paris Dental

Each Pydantic model represents a MongoDB collection.
Collection name is the lowercase class name (e.g., AppointmentRequest -> "appointmentrequest").
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

class AppointmentRequest(BaseModel):
    full_name: str = Field(..., description="Patient full name")
    email: Optional[EmailStr] = Field(None, description="Email address")
    phone: str = Field(..., description="Contact phone number")
    preferred_date: Optional[str] = Field(None, description="Preferred date (string)")
    preferred_time: Optional[str] = Field(None, description="Preferred time (string)")
    service_type: Optional[str] = Field(None, description="Requested service type")
    message: Optional[str] = Field(None, description="Additional notes")
    source: Optional[str] = Field("website", description="Lead source identifier")

class Testimonial(BaseModel):
    name: str = Field(..., description="Patient name or initials")
    quote: str = Field(..., description="Testimonial text")
    rating: int = Field(5, ge=1, le=5, description="Star rating 1-5")
    photo_url: Optional[str] = Field(None, description="Photo URL if permitted")
    featured: bool = Field(True, description="Feature on homepage")

class Post(BaseModel):
    title: str
    slug: str
    excerpt: Optional[str] = None
    content: str
    author: Optional[str] = "Paris Dental"
    tags: List[str] = []
    published_at: Optional[datetime] = None
    status: str = Field("published", description="draft|published")

class Service(BaseModel):
    name: str
    category: str = Field(..., description="General, Cosmetic, Restorative, Periodontal, Technology")
    description: str
    highlights: List[str] = []
    icon: Optional[str] = None
    slug: Optional[str] = None

class TeamMember(BaseModel):
    name: str
    role: str
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    credentials: Optional[str] = None
