from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class WorkshopCreate(BaseModel):
    name: str
    address: Optional[str] = None
    floor: Optional[str] = None
    subscription_tier: Optional[str] = "economy"
    max_admins: Optional[int] = 1
    max_workers: Optional[int] = 5

class WorkshopResponse(BaseModel):
    id: str
    name: str
    address: Optional[str] = None
    floor: Optional[str] = None
    subscription_tier: str
    max_admins: int
    max_workers: int
    created_at: datetime

    class Config:
        from_attributes = True

class AdminCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None

class DepartmentCreate(BaseModel):
    name: str

class DepartmentResponse(BaseModel):
    id: str
    workshop_id: str
    name: str
    created_at: datetime

    class Config:
        from_attributes = True

class WorkerCreate(BaseModel):
    name: str
    department_id: Optional[Any] = None
    phone: Optional[str] = None

    @field_validator('department_id', mode='before')
    def parse_department_id(cls, v):
        if v is not None:
            return str(v)
        return v

class UserResponse(BaseModel):
    id: str
    workshop_id: str
    department_id: Optional[str] = None
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    token: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    title: str
    client_name: Optional[str] = None
    details: Optional[str] = None
    items: Optional[List[Dict[str, Any]]] = None  
    department_id: Optional[Any] = None
    worker_id: Optional[Any] = None
    priority: Optional[str] = "normal"
    images: Optional[List[str]] = []
    voice_notes: Optional[List[str]] = []

    @field_validator('department_id', 'worker_id', mode='before')
    def parse_ids(cls, v):
        if v is not None:
            return str(v)
        return v

class OrderResponse(BaseModel):
    id: str
    workshop_id: str
    manager_id: str
    worker_id: Optional[str] = None
    department_id: Optional[str] = None
    title: str
    client_name: Optional[str] = None
    details: Optional[str] = None
    items: Optional[List[Dict[str, Any]]] = None
    images_paths: Optional[str] = None
    voice_notes_paths: Optional[str] = None
    status: str
    priority: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ShortageCreate(BaseModel):
    item_name: str
    quantity_needed: Optional[str] = None

class ShortageResponse(BaseModel):
    id: str
    workshop_id: str
    worker_id: str
    item_name: str
    quantity_needed: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
        
class LedgerCreate(BaseModel):
    ledger_type: str = "customer"
    client_name: str
    phone: Optional[str] = None
    total_amount: float
    currency: str = "SYP"
    exchange_rate: float = 1.0
    due_date: Optional[datetime] = None
    notes: Optional[str] = None

class LedgerPaymentCreate(BaseModel):
    amount_paid: float
    currency: str = "SYP"
    exchange_rate: float = 1.0
    notes: Optional[str] = None

class LedgerPaymentResponse(BaseModel):
    id: str
    ledger_id: str
    amount_paid: float
    currency: str
    exchange_rate: float
    payment_date: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True

class LedgerResponse(BaseModel):
    id: str
    workshop_id: str
    ledger_type: str
    client_name: str
    phone: Optional[str] = None
    total_amount: float
    remaining_amount: float
    currency: str
    exchange_rate: float
    due_date: Optional[datetime] = None
    notes: Optional[str] = None
    status: str
    created_at: datetime
    payments: List[LedgerPaymentResponse] = []

    class Config:
        from_attributes = True