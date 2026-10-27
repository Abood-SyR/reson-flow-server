from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.deps import get_current_admin, get_current_user
from app.core.limiter import limiter
from app.models.models import Department, User
from app.schemas.schemas import DepartmentCreate, DepartmentResponse

router = APIRouter(prefix="/departments", tags=["Departments Management"])

@router.post("/", response_model=DepartmentResponse)
@limiter.limit("20/minute")
def create_department(request: Request, dept_data: DepartmentCreate, current_admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    existing = db.query(Department).filter(
        Department.workshop_id == current_admin.workshop_id,
        Department.name == dept_data.name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Department name already exists in this workshop")

    new_dept = Department(
        workshop_id=current_admin.workshop_id,
        name=dept_data.name
    )
    db.add(new_dept)
    db.commit()
    db.refresh(new_dept)
    return new_dept

@router.get("/", response_model=List[DepartmentResponse])
def get_departments(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    departments = db.query(Department).filter(Department.workshop_id == current_user.workshop_id).all()
    return departments

@router.put("/{department_id}", response_model=DepartmentResponse)
@limiter.limit("30/minute")
def update_department(request: Request, department_id: int, dept_data: DepartmentCreate, current_admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    dept = db.query(Department).filter(
        Department.id == department_id,
        Department.workshop_id == current_admin.workshop_id
    ).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    dept.name = dept_data.name
    db.commit()
    db.refresh(dept)
    return dept

@router.delete("/{department_id}")
@limiter.limit("20/minute")
def delete_department(request: Request, department_id: int, current_admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    dept = db.query(Department).filter(
        Department.id == department_id,
        Department.workshop_id == current_admin.workshop_id
    ).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    db.delete(dept)
    db.commit()
    return {"message": "Department deleted successfully"}