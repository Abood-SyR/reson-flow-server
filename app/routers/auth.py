from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_db
from app.core.security import generate_worker_token
from app.core.deps import get_current_admin
from app.core.limiter import limiter
from app.models.models import Workshop, User
from app.schemas.schemas import WorkshopCreate, WorkshopResponse, WorkerCreate, AdminCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["Auth & Management"])

class WorkerUpdate(BaseModel):
    name: Optional[str] = None
    department_id: Optional[int] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None

@router.post("/workshop", response_model=WorkshopResponse)
@limiter.limit("5/minute")
def create_workshop(request: Request, workshop_data: WorkshopCreate, db: Session = Depends(get_db)):
    new_workshop = Workshop(
        name=workshop_data.name,
        address=workshop_data.address,
        floor=workshop_data.floor,
        subscription_tier=workshop_data.subscription_tier,
        max_admins=workshop_data.max_admins,
        max_workers=workshop_data.max_workers
    )
    db.add(new_workshop)
    db.commit()
    db.refresh(new_workshop)
    return new_workshop

@router.post("/register/admin", response_model=UserResponse)
@limiter.limit("5/minute")
def register_admin(request: Request, admin_data: AdminCreate, workshop_id: str, db: Session = Depends(get_db)):
    workshop = db.query(Workshop).filter(Workshop.id == workshop_id).first()
    if not workshop:
        raise HTTPException(status_code=404, detail="Workshop not found")

    existing_admin = db.query(User).filter(User.workshop_id == workshop_id, User.role == "admin").first()
    if existing_admin:
        raise HTTPException(status_code=400, detail="Admin already exists for this workshop")

    token = generate_worker_token()
    
    new_admin = User(
        workshop_id=workshop_id,
        name=admin_data.name,
        phone=admin_data.phone,
        email=admin_data.email,
        token=token,
        role="admin",
        is_active=True
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    return new_admin

@router.post("/worker", response_model=UserResponse)
def create_worker(worker_data: WorkerCreate, workshop_id: str, current_admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    if current_admin.workshop_id != workshop_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    token = generate_worker_token()
    
    new_worker = User(
        workshop_id=workshop_id,
        name=worker_data.name,
        phone=worker_data.phone,
        token=token,
        role="worker",
        department_id=worker_data.department_id,
        is_active=True
    )
    db.add(new_worker)
    db.commit()
    db.refresh(new_worker)
    return new_worker

@router.get("/workers", response_model=List[UserResponse])
def get_workshop_workers(current_admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    workers = db.query(User).filter(User.workshop_id == current_admin.workshop_id, User.role == "worker").all()
    return workers

@router.put("/workers/{worker_id}", response_model=UserResponse)
def update_worker(worker_id: int, worker_update: WorkerUpdate, current_admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    worker = db.query(User).filter(User.id == worker_id, User.workshop_id == current_admin.workshop_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    if worker_update.name is not None:
        worker.name = worker_update.name
    if worker_update.department_id is not None:
        worker.department_id = worker_update.department_id
    if worker_update.phone is not None:
        worker.phone = worker_update.phone
    if worker_update.is_active is not None:
        worker.is_active = worker_update.is_active

    db.commit()
    db.refresh(worker)
    return worker

@router.patch("/workers/{worker_id}/session", response_model=UserResponse)
def toggle_worker_session(worker_id: int, is_active: bool, current_admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    worker = db.query(User).filter(User.id == worker_id, User.workshop_id == current_admin.workshop_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    worker.is_active = is_active
    db.commit()
    db.refresh(worker)
    return worker

@router.get("/workers/{worker_id}/barcode")
def get_worker_barcode(worker_id: int, current_admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    worker = db.query(User).filter(User.id == worker_id, User.workshop_id == current_admin.workshop_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    return {
        "worker_id": worker.id,
        "name": worker.name,
        "department_id": worker.department_id,
        "barcode_token": worker.token
    }

@router.delete("/workers/{worker_id}")
def delete_worker_session(worker_id: int, current_admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    worker = db.query(User).filter(User.id == worker_id, User.workshop_id == current_admin.workshop_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    db.delete(worker)
    db.commit()
    return {"message": "Worker session deleted successfully"}

@router.post("/login/worker", response_model=UserResponse)
@limiter.limit("10/minute")
def worker_login(request: Request, token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.token == token, User.is_active == True, User.role == "worker").first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token or inactive account")
    return user

@router.post("/login/admin", response_model=UserResponse)
@limiter.limit("10/minute")
def admin_login(request: Request, token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.token == token, User.is_active == True, User.role == "admin").first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token or inactive admin account")
    return user