import json
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.limiter import limiter
from app.models.models import Order, User, IdempotencyKey
from app.services.cloudinary_service import upload_to_cloudinary

router = APIRouter(prefix="/orders", tags=["Orders Management"])

ARCHIVE_DIR = "storage/archive"

def check_idempotency(db: Session, key: str):
    if not key:
        return None
    existing = db.query(IdempotencyKey).filter(IdempotencyKey.key == key).first()
    if existing:
        return existing.response_body
    return None

def save_idempotency(db: Session, key: str, status_code: int, response_body: dict):
    if key:
        record = IdempotencyKey(
            key=key,
            response_code=status_code,
            response_body=response_body
        )
        db.add(record)
        db.commit()

@router.post("/", response_model=dict)
@limiter.limit("20/minute")
def create_order(
    request: Request,
    title: str = Form(...),
    client_name: Optional[str] = Form(None),
    details: Optional[str] = Form(None),
    items: Optional[str] = Form(None),
    department_id: Optional[str] = Form(None),
    worker_id: Optional[str] = Form(None),
    priority: str = Form("normal"),
    images: Optional[List[UploadFile]] = File(None),
    voice_notes: Optional[List[UploadFile]] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["admin", "partner"]:
        raise HTTPException(status_code=403, detail="Only admins can create orders")

    idempotency_key = request.headers.get("X-Idempotency-Key")
    cached_response = check_idempotency(db, idempotency_key)
    if cached_response:
        return cached_response

    if images and len(images) > 0 and images[0].filename != "":
        if len(images) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 images allowed")
    else:
        images = None

    if voice_notes and len(voice_notes) > 0 and voice_notes[0].filename != "":
        if len(voice_notes) > 5:
            raise HTTPException(status_code=400, detail="Maximum 5 voice notes allowed")
    else:
        voice_notes = None

    parsed_items = None
    if items:
        try:
            parsed_items = json.loads(items)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format for items")

    # رفع الصور إلى Cloudinary بدلاً من التخزين المحلي
    saved_images = []
    if images:
        for img in images:
            url = upload_to_cloudinary(img, folder="reson_orders/images")
            if url:
                saved_images.append(url)

    # رفع المقاطع الصوتية إلى Cloudinary
    saved_voices = []
    if voice_notes:
        for voice in voice_notes:
            url = upload_to_cloudinary(voice, folder="reson_orders/voices")
            if url:
                saved_voices.append(url)

    new_order = Order(
        workshop_id=current_user.workshop_id,
        manager_id=current_user.id,
        worker_id=worker_id,
        department_id=department_id,
        title=title,
        client_name=client_name,
        details=details,
        items=parsed_items,
        images_paths=",".join(saved_images) if saved_images else None,
        voice_notes_paths=",".join(saved_voices) if saved_voices else None,
        status="pending",
        priority=priority
    )
    
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    response_data = {"message": "Order created successfully", "order_id": new_order.id}
    save_idempotency(db, idempotency_key, 200, response_data)

    return response_data

@router.get("/", response_model=List[dict])
def get_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Order).filter(Order.workshop_id == current_user.workshop_id)
    
    if current_user.role == "worker":
        query = query.filter(
            (Order.worker_id == current_user.id) | 
            (Order.department_id == current_user.department_id)
        )
    
    orders = query.all()
    result = []
    for o in orders:
        result.append({
            "id": o.id,
            "title": o.title,
            "client_name": o.client_name,
            "details": o.details,
            "items": o.items,
            "department_id": o.department_id,
            "worker_id": o.worker_id,
            "status": o.status,
            "priority": o.priority,
            "images": o.images_paths.split(",") if o.images_paths else [],
            "voice_notes": o.voice_notes_paths.split(",") if o.voice_notes_paths else [],
            "created_at": o.created_at
        })
    return result

@router.patch("/{order_id}/item-status", response_model=dict)
@limiter.limit("30/minute")
def update_item_status(
    request: Request,
    order_id: str,
    item_index: int,
    item_status: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    idempotency_key = request.headers.get("X-Idempotency-Key")
    cached_response = check_idempotency(db, idempotency_key)
    if cached_response:
        return cached_response

    order = db.query(Order).filter(Order.id == order_id, Order.workshop_id == current_user.workshop_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if not order.items or not isinstance(order.items, list) or item_index >= len(order.items):
        raise HTTPException(status_code=400, detail="Invalid item index")

    items = list(order.items)
    target_item = dict(items[item_index])
    
    target_item["status"] = item_status
    now_str = datetime.utcnow().isoformat()

    if item_status == "in_progress" and "started_at" not in target_item:
        target_item["started_at"] = now_str
    elif item_status == "completed":
        target_item["completed_at"] = now_str

    items[item_index] = target_item
    order.items = items

    all_completed = all(item.get("status") == "completed" for item in items if isinstance(item, dict))
    if all_completed:
        order.status = "completed"
        order.completed_at = datetime.utcnow()
    elif any(item.get("status") == "in_progress" for item in items if isinstance(item, dict)):
        order.status = "in_progress"

    db.commit()

    response_data = {"message": "Item status updated successfully", "order_status": order.status}
    save_idempotency(db, idempotency_key, 200, response_data)

    return response_data

@router.put("/{order_id}", response_model=dict)
def update_order(
    order_id: str,
    title: Optional[str] = Form(None),
    client_name: Optional[str] = Form(None),
    details: Optional[str] = Form(None),
    items: Optional[str] = Form(None),
    status_val: Optional[str] = Form(None),
    priority: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["admin", "partner"]:
        raise HTTPException(status_code=403, detail="Workers are not allowed to modify order details")

    order = db.query(Order).filter(Order.id == order_id, Order.workshop_id == current_user.workshop_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if title: order.title = title
    if client_name is not None: order.client_name = client_name
    if details: order.details = details
    if items:
        try:
            order.items = json.loads(items)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format for items")
    if priority: order.priority = priority
    
    if status_val:
        order.status = status_val
        if status_val == "completed":
            order.completed_at = datetime.utcnow()

    db.commit()
    return {"message": "Order updated successfully"}

@router.delete("/{order_id}")
def delete_order(order_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in ["admin", "partner"]:
        raise HTTPException(status_code=403, detail="Workers are not allowed to delete orders")

    order = db.query(Order).filter(Order.id == order_id, Order.workshop_id == current_user.workshop_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    db.delete(order)
    db.commit()
    return {"message": "Order deleted successfully"}