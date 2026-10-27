from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import ShortageRequest, User
from app.schemas.schemas import ShortageCreate, ShortageResponse

router = APIRouter(prefix="/inventory", tags=["Inventory & Shortages"])

@router.post("/shortages", response_model=ShortageResponse)
def create_shortage_request(shortage: ShortageCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "worker":
        raise HTTPException(status_code=403, detail="Only workers can request shortages")

    new_request = ShortageRequest(
        workshop_id=current_user.workshop_id,
        worker_id=current_user.id,
        item_name=shortage.item_name,
        quantity_needed=shortage.quantity_needed,
        status="requested"
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return new_request

@router.get("/shortages", response_model=List[ShortageResponse])
def get_shortage_requests(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(ShortageRequest).filter(ShortageRequest.workshop_id == current_user.workshop_id)
    
    if current_user.role == "worker":
        query = query.filter(ShortageRequest.worker_id == current_user.id)
        
    return query.all()

@router.patch("/shortages/{request_id}", response_model=ShortageResponse)
def update_shortage_status(request_id: int, status_val: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in ["admin", "partner"]:
        raise HTTPException(status_code=403, detail="Only admins can update shortage status")

    req = db.query(ShortageRequest).filter(ShortageRequest.id == request_id, ShortageRequest.workshop_id == current_user.workshop_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Shortage request not found")
    
    req.status = status_val
    db.commit()
    db.refresh(req)
    return req