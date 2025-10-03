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
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# -------------------- Database --------------------
DATABASE_URL = os.getenv("DATABASE_URL")  # Render Postgres URL

engine = create_engine(DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# -------------------- Models --------------------
class ProjectModel(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    stack = Column(JSON)
    code = Column(String)
    image = Column(String)
    snippet = Column(String)

class SkillModel(Base):
    __tablename__ = "skills"
    name = Column(String, primary_key=True)
    icon = Column(String)
    skills = Column(JSON)  # list of skill items

class ExperienceModel(Base):
    __tablename__ = "experience"
    role = Column(String, primary_key=True)
    company = Column(String)
    type = Column(String)
    duration = Column(String)

class ResearchModel(Base):
    __tablename__ = "research"
    title = Column(String, primary_key=True)
    short_description = Column(String)
    author = Column(String)
    link = Column(String)

class AdminModel(Base):
    __tablename__ = "admin"
    username = Column(String, primary_key=True)
    password = Column(String)

# Create tables if not exist
Base.metadata.create_all(bind=engine)

# -------------------- Dependency --------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------- FastAPI App --------------------
app = FastAPI()

origins = ["https://abhay-portfolio-etuw.vercel.app/"]  # frontend URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

PasswordStr = Annotated[str, str]

class LoginRequest(BaseModel):
    username: EmailStr
    password: PasswordStr

class UpdateCredentialsRequest(BaseModel):
    old_username: EmailStr
    old_password: str
    new_username: EmailStr
    new_password: str

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

# -------------------- Admin Data --------------------
def fetch_admin(db: Session):
    admin = db.query(AdminModel).first()
    if admin:
        return {"username": admin.username, "password": admin.password}
    return {"username": "", "password": ""}

# -------------------- Helper Functions --------------------
def send_otp_email(to_email: str, otp: str):
    sender_email = "abhaysharma75547@gmail.com"
    sender_password = "riac vdwm ljfj iaew"  # Gmail App password
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

OTP_STORE = {}

# -------------------- CRUD Endpoints --------------------
# Projects
@app.get("/projects", response_model=List[Project])
def get_projects(db: Session = Depends(get_db)):
    return db.query(ProjectModel).all()

@app.get("/projects/{project_id}", response_model=Project)
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@app.post("/projects", response_model=Project)
def create_project(project: Project, db: Session = Depends(get_db)):
    new_project = ProjectModel(**project.dict())
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project

@app.put("/projects/{project_id}", response_model=Project)
def update_project(project_id: str, updated: Project, db: Session = Depends(get_db)):
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    for k, v in updated.dict().items():
        setattr(project, k, v)
    db.commit()
    db.refresh(project)
    return project

@app.delete("/projects/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if project:
        db.delete(project)
        db.commit()
    return {"detail": "Project deleted"}

# -------------------- Skills, Experience, Research, Admin CRUD --------------------
# You can follow same pattern: query db with SQLAlchemy, add/commit, update attributes, delete

# Example for Admin login
@app.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    admin_data = fetch_admin(db)
    if req.username.strip() == admin_data["username"].strip() and req.password.strip() == admin_data["password"].strip():
        return {"status": "success", "message": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid username or password")

# Example for updating admin credentials
@app.put("/update-admin-credential")
def update_admin(req: UpdateCredentialsRequest, db: Session = Depends(get_db)):
    admin = db.query(AdminModel).first()
    if not admin or req.old_username != admin.username or req.old_password != admin.password:
        raise HTTPException(status_code=401, detail="Old credentials incorrect")
    admin.username = req.new_username
    admin.password = req.new_password
    db.commit()
    return {"status": "success", "message": "Admin credentials updated"}

# OTP Endpoints
@app.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    admin_data = fetch_admin(db)
    if req.email != admin_data["username"]:
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
    admin = db.query(AdminModel).first()
    if req.email not in OTP_STORE or OTP_STORE[req.email] != req.otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    if req.new_password != req.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    admin.username = req.email
    admin.password = req.new_password
    db.commit()
    del OTP_STORE[req.email]
    return {"status": "success", "message": "Password reset successful"}
