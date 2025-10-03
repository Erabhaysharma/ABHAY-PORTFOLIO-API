from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, field_validator
from typing import List, Annotated
import re
import json
import smtplib
import random
import os
from sqlalchemy import create_engine, Column, String, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# -------------------- Database --------------------
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("❌ DATABASE_URL environment variable not set")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# -------------------- Models --------------------
class ProjectDB(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    stack = Column(JSON)
    code = Column(String)
    image = Column(String)
    snippet = Column(String)

class SkillDB(Base):
    __tablename__ = "skills"
    name = Column(String, primary_key=True, index=True)
    icon = Column(String)
    skills = Column(JSON)

class ExperienceDB(Base):
    __tablename__ = "experience"
    role = Column(String, primary_key=True, index=True)
    company = Column(String)
    type = Column(String)
    duration = Column(String)

class ResearchDB(Base):
    __tablename__ = "research"
    title = Column(String, primary_key=True, index=True)
    short_description = Column(String)
    author = Column(String)
    link = Column(String)

class AdminDB(Base):
    __tablename__ = "admin"
    username = Column(String, primary_key=True, index=True)
    password = Column(String)

Base.metadata.create_all(bind=engine)

# -------------------- FastAPI --------------------
app = FastAPI()

origins = ["https://abhay-portfolio-etuw.vercel.app/"]  # frontend URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------- Pydantic Models --------------------
class Project(BaseModel):
    id: str
    title: str
    description: str
    stack: List[str]
    code: str
    image: str
    snippet: str

class SkillItem(BaseModel):
    name: str
    percent: int

class SkillCategory(BaseModel):
    name: str
    icon: str
    skills: List[SkillItem]

class Research(BaseModel):
    title: str
    short_description: str
    author: str
    link: str

class ExperienceItem(BaseModel):
    role: str
    company: str
    type: str
    duration: str

PasswordStr = Annotated[str, str]  # simplified

class LoginRequest(BaseModel):
    username: EmailStr
    password: PasswordStr

# -------------------- CRUD Helpers --------------------
def fetch_admin(db: Session):
    admin = db.query(AdminDB).first()
    if admin:
        return {"username": admin.username, "password": admin.password}
    return {"username": "", "password": ""}

# -------------------- Admin --------------------
def get_admin_data(db: Session = Depends(get_db)):
    return fetch_admin(db)

# -------------------- CRUD Endpoints --------------------
# Projects
@app.get("/projects", response_model=List[Project])
def get_projects(db: Session = Depends(get_db)):
    projects = db.query(ProjectDB).all()
    return [Project(**{
        "id": p.id,
        "title": p.title,
        "description": p.description,
        "stack": p.stack,
        "code": p.code,
        "image": p.image,
        "snippet": p.snippet
    }) for p in projects]

@app.post("/projects", response_model=Project)
def create_project(project: Project, db: Session = Depends(get_db)):
    db_project = ProjectDB(**project.dict())
    db.add(db_project)
    db.commit()
    return project

@app.put("/projects/{project_id}", response_model=Project)
def update_project(project_id: str, updated: Project, db: Session = Depends(get_db)):
    proj = db.query(ProjectDB).filter(ProjectDB.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    for key, value in updated.dict().items():
        setattr(proj, key, value)
    db.commit()
    return updated

@app.delete("/projects/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    proj = db.query(ProjectDB).filter(ProjectDB.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(proj)
    db.commit()
    return {"detail": "Project deleted"}

# Skills
@app.get("/skills", response_model=List[SkillCategory])
def get_skills(db: Session = Depends(get_db)):
    skills = db.query(SkillDB).all()
    return [SkillCategory(**{"name": s.name, "icon": s.icon, "skills": s.skills}) for s in skills]

@app.post("/skills", response_model=SkillCategory)
def create_skill(skill: SkillCategory, db: Session = Depends(get_db)):
    db_skill = SkillDB(name=skill.name, icon=skill.icon, skills=[s.dict() for s in skill.skills])
    db.add(db_skill)
    db.commit()
    return skill

@app.put("/skills/{name}", response_model=SkillCategory)
def update_skill(name: str, updated: SkillCategory, db: Session = Depends(get_db)):
    s = db.query(SkillDB).filter(SkillDB.name == name).first()
    if not s:
        raise HTTPException(status_code=404, detail="Skill not found")
    s.icon = updated.icon
    s.skills = [x.dict() for x in updated.skills]
    db.commit()
    return updated

@app.delete("/skills/{name}")
def delete_skill(name: str, db: Session = Depends(get_db)):
    s = db.query(SkillDB).filter(SkillDB.name == name).first()
    if not s:
        raise HTTPException(status_code=404, detail="Skill not found")
    db.delete(s)
    db.commit()
    return {"detail": "Skill deleted"}

# Experience
@app.get("/experience", response_model=List[ExperienceItem])
def get_experience(db: Session = Depends(get_db)):
    exps = db.query(ExperienceDB).all()
    return [ExperienceItem(**{
        "role": e.role,
        "company": e.company,
        "type": e.type,
        "duration": e.duration
    }) for e in exps]

@app.post("/experience", response_model=ExperienceItem)
def create_experience(exp: ExperienceItem, db: Session = Depends(get_db)):
    db_exp = ExperienceDB(**exp.dict())
    db.add(db_exp)
    db.commit()
    return exp

@app.put("/experience/{role}", response_model=ExperienceItem)
def update_experience(role: str, updated: ExperienceItem, db: Session = Depends(get_db)):
    e = db.query(ExperienceDB).filter(ExperienceDB.role == role).first()
    if not e:
        raise HTTPException(status_code=404, detail="Experience not found")
    for key, value in updated.dict().items():
        setattr(e, key, value)
    db.commit()
    return updated

@app.delete("/experience/{role}")
def delete_experience(role: str, db: Session = Depends(get_db)):
    e = db.query(ExperienceDB).filter(ExperienceDB.role == role).first()
    if not e:
        raise HTTPException(status_code=404, detail="Experience not found")
    db.delete(e)
    db.commit()
    return {"detail": "Experience deleted"}

# Research
@app.get("/research", response_model=List[Research])
def get_research(db: Session = Depends(get_db)):
    res = db.query(ResearchDB).all()
    return [Research(**{
        "title": r.title,
        "short_description": r.short_description,
        "author": r.author,
        "link": r.link
    }) for r in res]

@app.post("/research", response_model=Research)
def create_research(r: Research, db: Session = Depends(get_db)):
    db_r = ResearchDB(**r.dict())
    db.add(db_r)
    db.commit()
    return r

@app.put("/research/{title}", response_model=Research)
def update_research(title: str, updated: Research, db: Session = Depends(get_db)):
    r = db.query(ResearchDB).filter(ResearchDB.title == title).first()
    if not r:
        raise HTTPException(status_code=404, detail="Research not found")
    for key, value in updated.dict().items():
        setattr(r, key, value)
    db.commit()
    return updated

@app.delete("/research/{title}")
def delete_research(title: str, db: Session = Depends(get_db)):
    r = db.query(ResearchDB).filter(ResearchDB.title == title).first()
    if not r:
        raise HTTPException(status_code=404, detail="Research not found")
    db.delete(r)
    db.commit()
    return {"detail": "Research deleted"}

# -------------------- Admin --------------------
@app.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    admin = fetch_admin(db)
    if req.username.strip() == admin["username"].strip() and req.password.strip() == admin["password"].strip():
        return {"status": "success", "message": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid username or password")

# Update Admin
class UpdateCredentialsRequest(BaseModel):
    old_username: EmailStr
    old_password: str
    new_username: EmailStr
    new_password: str

@app.put("/update-admin-credential")
def update_admin(req: UpdateCredentialsRequest, db: Session = Depends(get_db)):
    admin = db.query(AdminDB).filter(AdminDB.username == req.old_username).first()
    if not admin or req.old_password != admin.password:
        raise HTTPException(status_code=401, detail="Old credentials incorrect")
    admin.username = req.new_username
    admin.password = req.new_password
    db.commit()
    return {"status": "success", "message": "Admin credentials updated"}

# -------------------- OTP --------------------
OTP_STORE = {}

def send_otp_email(to_email: str, otp: str):
    sender_email = "abhaysharma75547@gmail.com"
    sender_password = "riac vdwm ljfj iaew"  # Gmail app password
    subject = "Your OTP for Password Reset"
    body = f"Your OTP is {otp}. It will expire in 5 minutes."
    message = f"Subject: {subject}\n\n{body}"

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, message)
    except Exception as e:
        print("❌ Email error:", e)
        raise HTTPException(status_code=500, detail="Failed to send OTP")

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str
    confirm_password: str

    @field_validator("new_password", mode="after")
    @classmethod
    def validate_new_password(cls, v: str):
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least 1 uppercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least 1 number")
        if not re.search(r"[@$!%*?&]", v):
            raise ValueError("Password must contain at least 1 special character")
        return v

@app.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    admin = fetch_admin(db)
    if req.email != admin["username"]:
        raise HTTPException(status_code=404, detail="Email not registered")
    otp = str(random.randint(100000, 999999))
    OTP_STORE[req.email] = otp
    send_otp_email(req.email, otp)
    return {"status": "success", "message": "OTP sent to email"}

@app.post("/verify-otp")
async def verify_otp(req: VerifyOtpRequest):
    if req.email not in OTP_STORE or OTP_STORE[req.email] != req.otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    return {"status": "success", "message": "OTP verified"}

@app.post("/reset-password")
async def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    if req.email not in OTP_STORE or OTP_STORE[req.email] != req.otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    if req.new_password != req.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    admin = db.query(AdminDB).filter(AdminDB.username == req.email).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    admin.password = req.new_password
    db.commit()
    del OTP_STORE[req.email]
    return {"status": "success", "message": "Password reset successful"}
