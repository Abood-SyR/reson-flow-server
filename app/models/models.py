import uuid
from sqlalchemy import Column, Float, String, Text, DateTime, ForeignKey, Integer, JSON, Boolean
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class Workshop(Base):
    __tablename__ = "workshops"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    floor = Column(String, nullable=True)
    subscription_tier = Column(String, default="economy")
    max_admins = Column(Integer, default=1)
    max_workers = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.utcnow)

class Department(Base):
    __tablename__ = "departments"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    workshop_id = Column(String(36), ForeignKey("workshops.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    key = Column(String(255), unique=True, index=True, nullable=False)
    response_code = Column(Integer, nullable=False)
    response_body = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    workshop_id = Column(String(36), ForeignKey("workshops.id"), index=True, nullable=False)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True, index=True)
    phone = Column(String, nullable=True)
    token = Column(String, unique=True, nullable=True, index=True)
    role = Column(String, default="worker")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Order(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workshop_id = Column(String(36), ForeignKey("workshops.id"), nullable=False)
    manager_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    worker_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=True)
    
    title = Column(String(255), nullable=False)
    client_name = Column(String(255), nullable=True)
    details = Column(Text, nullable=True)
    items = Column(JSON, nullable=True)
    images_paths = Column(Text, nullable=True)
    voice_notes_paths = Column(Text, nullable=True)
    status = Column(String(50), default="pending")
    priority = Column(String(20), default="normal")
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    archive_folder = Column(String(255), nullable=True)

class ShortageRequest(Base):
    __tablename__ = "shortage_requests"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    workshop_id = Column(String(36), ForeignKey("workshops.id"), index=True, nullable=False)
    worker_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    item_name = Column(String, nullable=False)
    quantity_needed = Column(String, nullable=True)
    status = Column(String, default="requested")
    created_at = Column(DateTime, default=datetime.utcnow)
    
class FinancialLedger(Base):
    __tablename__ = "financial_ledgers"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    workshop_id = Column(String(36), ForeignKey("workshops.id"), nullable=False, index=True)
    ledger_type = Column(String(50), nullable=False, default="customer")
    client_name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    total_amount = Column(Float, nullable=False, default=0.0)
    remaining_amount = Column(Float, nullable=False, default=0.0)
    currency = Column(String(50), nullable=False, default="SYP")
    exchange_rate = Column(Float, nullable=False, default=1.0)
    due_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(50), default="unpaid")
    created_at = Column(DateTime, default=datetime.utcnow)

    payments = relationship("LedgerPayment", back_populates="ledger", cascade="all, delete-orphan")

class LedgerPayment(Base):
    __tablename__ = "ledger_payments"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    ledger_id = Column(String(36), ForeignKey("financial_ledgers.id"), nullable=False, index=True)
    amount_paid = Column(Float, nullable=False)
    currency = Column(String(50), nullable=False, default="SYP")
    exchange_rate = Column(Float, nullable=False, default=1.0)
    payment_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)
    
    ledger = relationship("FinancialLedger", back_populates="payments")