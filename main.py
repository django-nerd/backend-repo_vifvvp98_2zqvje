import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

from database import create_document, get_documents, db
from schemas import AppointmentRequest, Testimonial, Post, Service

app = FastAPI(title="Paris Dental API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Utility: seed basic content
# -----------------------------
SEED_RUN_FLAG = "__seed_paris_dental__"

def ensure_seed_data():
    if db is None:
        return
    # Use a marker collection to avoid reseeding every time
    if db.meta.find_one({"key": SEED_RUN_FLAG}):
        return

    # Seed testimonials
    if db.testimonial.count_documents({}) == 0:
        samples: List[Testimonial] = [
            Testimonial(name="A.M.", quote="Best Temecula dentist experience I've ever had.", rating=5, featured=True),
            Testimonial(name="J.S.", quote="Beautiful office, gentle care, and amazing results!", rating=5, featured=True),
            Testimonial(name="K.R.", quote="They made me feel at ease from the moment I walked in.", rating=5, featured=False),
        ]
        for t in samples:
            create_document("testimonial", t)

    # Seed services
    if db.service.count_documents({}) == 0:
        services: List[Service] = [
            Service(name="General Dentistry", category="General", description="Cleanings, exams, and preventive care for the whole family.", highlights=["Gentle cleanings", "Digital X-rays", "Comprehensive exams"], icon="Tooth", slug="general-dentistry"),
            Service(name="Cosmetic Dentistry", category="Cosmetic", description="Veneers, whitening, and smile design for confident smiles.", highlights=["Porcelain veneers", "Professional whitening", "Bonding"], icon="Sparkles", slug="cosmetic-dentistry"),
            Service(name="Dental Implants", category="Restorative", description="Modern implant solutions to replace missing teeth.", highlights=["Single and full-arch", "3D guided planning", "Natural aesthetics"], icon="Pillar", slug="dental-implants"),
            Service(name="Periodontal Care", category="Periodontal", description="Laser-assisted therapy and maintenance for healthy gums.", highlights=["Laser therapy", "Deep cleaning", "Periodontal maintenance"], icon="HeartPulse", slug="periodontal-care"),
            Service(name="Dental Technology", category="Technology", description="State-of-the-art tech for precision and comfort.", highlights=["CAD/CAM same-day", "3D CBCT imaging", "Intraoral scanning"], icon="Cpu", slug="dental-technology"),
        ]
        for s in services:
            create_document("service", s)

    # Seed a welcome post
    if db.post.count_documents({}) == 0:
        post = Post(
            title="Welcome to Paris Dental – Modern Dental Care in Temecula",
            slug="welcome-paris-dental",
            excerpt="Discover patient-first care powered by advanced technology in Temecula.",
            content="We are thrilled to welcome you to our modern practice led by Dr. Noorullah Azim. Our team focuses on comfort, precision, and beautiful results.",
            author="Paris Dental",
            tags=["Temecula dentist", "cosmetic dentistry"],
            published_at=datetime.utcnow(),
            status="published",
        )
        create_document("post", post)

    db.meta.insert_one({"key": SEED_RUN_FLAG, "created_at": datetime.utcnow()})


@app.on_event("startup")
async def startup_event():
    try:
        ensure_seed_data()
    except Exception:
        # Seeding is best-effort; ignore errors in ephemeral envs
        pass


# -----------------------------
# Basic routes
# -----------------------------
@app.get("/")
def read_root():
    return {"message": "Paris Dental API running", "status": "ok"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from Paris Dental backend!"}


# -----------------------------
# Health / DB test
# -----------------------------
@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = os.getenv("DATABASE_NAME") or "❌ Not Set"
            response["connection_status"] = "Connected"
            try:
                response["collections"] = db.list_collection_names()
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


# -----------------------------
# Appointment Requests
# -----------------------------
class AppointmentResponse(BaseModel):
    id: str
    success: bool

@app.post("/api/appointment", response_model=AppointmentResponse)
def create_appointment(request: AppointmentRequest):
    try:
        inserted_id = create_document("appointmentrequest", request)
        return {"id": inserted_id, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# Content Endpoints (read-only for site)
# -----------------------------
@app.get("/api/testimonials", response_model=List[Testimonial])
def get_testimonials(featured: Optional[bool] = None):
    try:
        filt = {}
        if featured is not None:
            filt["featured"] = featured
        docs = get_documents("testimonial", filt)
        for d in docs:
            d.pop("_id", None)
        return docs  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/services", response_model=List[Service])
def get_services(category: Optional[str] = None):
    try:
        filt = {"category": category} if category else {}
        docs = get_documents("service", filt)
        for d in docs:
            d.pop("_id", None)
        return docs  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/posts", response_model=List[Post])
def get_posts(tag: Optional[str] = None):
    try:
        filt = {"tags": {"$in": [tag]}} if tag else {}
        docs = get_documents("post", filt)
        for d in docs:
            d.pop("_id", None)
        return docs  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# Schema endpoint for admin tooling
# -----------------------------
@app.get("/schema")
def get_schema():
    return {
        "collections": [
            "appointmentrequest",
            "testimonial",
            "post",
            "service",
        ],
        "models": {
            "AppointmentRequest": AppointmentRequest.model_json_schema(),
            "Testimonial": Testimonial.model_json_schema(),
            "Post": Post.model_json_schema(),
            "Service": Service.model_json_schema(),
        },
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
