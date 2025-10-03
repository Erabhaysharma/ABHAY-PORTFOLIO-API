from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, field_validator
from typing import List, Annotated
import re
import sqlite3
import json
import smtplib
import random

DB_NAME = "data.db"

# -------------------- Database helper --------------------
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_table(table_name):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    result = [dict(row) for row in rows]
    conn.close()
    # Convert JSON strings to Python objects for projects
    if table_name == "projects":
        for r in result:
            r["stack"] = json.loads(r["stack"])
    return result

def insert_update_table(table_name, data, pk=None):
    """Insert or update a row in table_name"""
    conn = get_db()
    cursor = conn.cursor()
    if table_name == "projects":
        data_to_insert = (data.id, data.title, data.description,
                          json.dumps(data.stack), data.code, data.image, data.snippet)
        if pk:  # update
            cursor.execute("""
                UPDATE projects SET title=?, description=?, stack=?, code=?, image=?, snippet=?
                WHERE id=?
            """, (*data_to_insert[1:], pk))
        else:
            cursor.execute("""
                INSERT INTO projects (id,title,description,stack,code,image,snippet)
                VALUES (?,?,?,?,?,?,?)
            """, data_to_insert)
    elif table_name == "skills":
        # for skills, store as JSON string
        cursor.execute("""
            INSERT OR REPLACE INTO skills (name, icon, skills)
            VALUES (?,?,?)
        """, (data.name, data.icon, json.dumps([s.dict() for s in data.skills])))
    elif table_name == "experience":
        if pk:  # update by role
            cursor.execute("""
                UPDATE experience SET company=?, type=?, duration=?
                WHERE role=?
            """, (data.company, data.type, data.duration, pk))
        else:
            cursor.execute("""
                INSERT INTO experience (role, company, type, duration)
                VALUES (?,?,?,?)
            """, (data.role, data.company, data.type, data.duration))
    elif table_name == "research":
        if pk:
            cursor.execute("""
                UPDATE research SET short_description=?, author=?, link=?
                WHERE title=?
            """, (data.short_description, data.author, data.link, pk))
        else:
            cursor.execute("""
                INSERT INTO research (title, short_description, author, link)
                VALUES (?,?,?,?)
            """, (data.title, data.short_description, data.author, data.link))
    conn.commit()
    conn.close()

def delete_from_table(table_name, pk_value, pk_field):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table_name} WHERE {pk_field}=?", (pk_value,))
    conn.commit()
    conn.close()

# -------------------- FastAPI App --------------------
app = FastAPI()

origins = ["https://abhay-portfolio-etuw.vercel.app"]  # add your frontend URL
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

# -------------------- Admin --------------------
def fetch_admin():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admin LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    else:
        return {"username": "", "password": ""}

admin_data = fetch_admin()

PasswordStr = Annotated[str, str]  # simplified

class LoginRequest(BaseModel):
    username: EmailStr
    password: PasswordStr

# -------------------- Endpoints --------------------
# Projects CRUD
@app.get("/projects", response_model=List[Project])
def get_projects():
    return fetch_table("projects")

@app.get("/projects/{project_id}", response_model=Project)
def get_project(project_id: str):
    projects = fetch_table("projects")
    for p in projects:
        if p["id"] == project_id:
            return p
    raise HTTPException(status_code=404, detail="Project not found")

@app.post("/projects", response_model=Project)
def create_project(project: Project):
    insert_update_table("projects", project)
    return project

@app.put("/projects/{project_id}", response_model=Project)
def update_project(project_id: str, updated: Project):
    insert_update_table("projects", updated, pk=project_id)
    return updated

@app.delete("/projects/{project_id}")
def delete_project(project_id: str):
    delete_from_table("projects", project_id, "id")
    return {"detail": "Project deleted"}

# Skills CRUD
@app.get("/skills")
def get_skills():
    rows = fetch_table("skills")
    categories = {}

    for r in rows:
        category = r["category"]
        if category not in categories:
            categories[category] = {
                "name": category,
                "icon": r["icon"],
                "skills": []
            }
        categories[category]["skills"].append({
            "name": r["name"],
            "percent": r["percent"]
        })

    return list(categories.values())



@app.post("/skills", response_model=SkillCategory)
def create_skill(skill: SkillCategory):
    insert_update_table("skills", skill)
    return skill

@app.put("/skills/{category_name}", response_model=SkillCategory)
def update_skill(category_name: str, updated: SkillCategory):
    insert_update_table("skills", updated, pk=category_name)
    return updated

@app.delete("/skills/{category_name}")
def delete_skill(category_name: str):
    delete_from_table("skills", category_name, "name")
    return {"detail": "Skill category deleted"}

# Experience CRUD
@app.get("/experience", response_model=List[ExperienceItem])
def get_experience():
    rows = fetch_table("experience")
    return [ExperienceItem(**r) for r in rows]

@app.post("/experience", response_model=ExperienceItem)
def create_experience(exp: ExperienceItem):
    insert_update_table("experience", exp)
    return exp

@app.put("/experience/{role}", response_model=ExperienceItem)
def update_experience(role: str, updated: ExperienceItem):
    insert_update_table("experience", updated, pk=role)
    return updated

@app.delete("/experience/{role}")
def delete_experience(role: str):
    delete_from_table("experience", role, "role")
    return {"detail": "Experience deleted"}

# Research CRUD
@app.get("/research", response_model=List[Research])
def get_research():
    rows = fetch_table("research")
    return [Research(**r) for r in rows]

@app.post("/research", response_model=Research)
def create_research(r: Research):
    insert_update_table("research", r)
    return r

@app.put("/research/{title}", response_model=Research)
def update_research(title: str, updated: Research):
    insert_update_table("research", updated, pk=title)
    return updated

@app.delete("/research/{title}")
def delete_research(title: str):
    delete_from_table("research", title, "title")
    return {"detail": "Research deleted"}

# Admin login & password update
@app.post("/login")
def login(req: LoginRequest):
    if req.username.strip() == admin_data["username"].strip() and req.password.strip() == admin_data["password"].strip():
        return {"status": "success", "message": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid username or password")

# Update admin password example
class UpdateCredentialsRequest(BaseModel):
    old_username: EmailStr
    old_password: str
    new_username: EmailStr
    new_password: str

@app.put("/update-admin-credential")
def update_admin(req: UpdateCredentialsRequest):
    global admin_data
    if req.old_username != admin_data["username"] or req.old_password != admin_data["password"]:
        raise HTTPException(status_code=401, detail="Old credentials incorrect")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE admin SET username=?, password=? WHERE username=?",
                   (req.new_username, req.new_password, req.old_username))
    conn.commit()
    conn.close()
    admin_data = {"username": req.new_username, "password": req.new_password}
    return {"status": "success", "message": "Admin credentials updated"}

#OTP VERIFICATION ENDPOINT

# In-memory OTP store
OTP_STORE = {}  # { email: otp }

# -------------------- Helper Function --------------------
def send_otp_email(to_email: str, otp: str):
    sender_email = "abhaysharma75547@gmail.com"
    sender_password = "riac vdwm ljfj iaew"  # use Gmail App password
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

# -------------------- Pydantic Models --------------------
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

# -------------------- Endpoints --------------------
@app.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
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
async def reset_password(req: ResetPasswordRequest):
    if req.email not in OTP_STORE or OTP_STORE[req.email] != req.otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    if req.new_password != req.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    # Update password in file
    with open("data/admin.json", "w", encoding="utf-8") as f:
        json.dump({"username": req.email, "password": req.new_password}, f, indent=2)

    global admin_data
    admin_data = {"username": req.email, "password": req.new_password}

    # cleanup OTP
    del OTP_STORE[req.email]

    return {"status": "success", "message": "Password reset successful"}
