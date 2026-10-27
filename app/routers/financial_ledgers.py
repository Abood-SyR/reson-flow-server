from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.models import User, FinancialLedger, LedgerPayment
from app.schemas.schemas import LedgerCreate, LedgerResponse, LedgerPaymentCreate, LedgerPaymentResponse

router = APIRouter(prefix="/financial-ledgers", tags=["Financial Ledgers"])

@router.post("/", response_model=LedgerResponse)
def create_ledger(data: LedgerCreate, current_admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    new_ledger = FinancialLedger(
        workshop_id=current_admin.workshop_id,
        ledger_type=data.ledger_type,
        client_name=data.client_name,
        phone=data.phone,
        total_amount=data.total_amount,
        remaining_amount=data.total_amount,
        currency=data.currency,
        exchange_rate=data.exchange_rate,
        due_date=data.due_date,
        notes=data.notes,
        status="unpaid"
    )
    db.add(new_ledger)
    db.commit()
    db.refresh(new_ledger)
    return new_ledger

@router.get("/", response_model=List[LedgerResponse])
def get_ledgers(ledger_type: Optional[str] = None, current_admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    query = db.query(FinancialLedger).filter(FinancialLedger.workshop_id == current_admin.workshop_id)
    if ledger_type:
        query = query.filter(FinancialLedger.ledger_type == ledger_type)
    return query.all()

@router.post("/{ledger_id}/pay", response_model=LedgerResponse)
def pay_ledger(ledger_id: str, data: LedgerPaymentCreate, current_admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    ledger = db.query(FinancialLedger).filter(FinancialLedger.id == ledger_id, FinancialLedger.workshop_id == current_admin.workshop_id).first()
    if not ledger:
        raise HTTPException(status_code=404, detail="Record not found")

    if data.amount_paid <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    if data.amount_paid > ledger.remaining_amount:
        raise HTTPException(status_code=400, detail="Amount exceeds remaining balance")

    new_payment = LedgerPayment(
        ledger_id=ledger.id,
        amount_paid=data.amount_paid,
        currency=data.currency,
        exchange_rate=data.exchange_rate,
        notes=data.notes
    )
    db.add(new_payment)

    ledger.remaining_amount -= data.amount_paid
    if ledger.remaining_amount <= 0:
        ledger.remaining_amount = 0.0
        ledger.status = "paid"
    else:
        ledger.status = "partial"

    db.commit()
    db.refresh(ledger)
    return ledger

@router.put("/{ledger_id}", response_model=LedgerResponse)
def update_ledger(ledger_id: str, data: LedgerCreate, current_admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    ledger = db.query(FinancialLedger).filter(FinancialLedger.id == ledger_id, FinancialLedger.workshop_id == current_admin.workshop_id).first()
    if not ledger:
        raise HTTPException(status_code=404, detail="Record not found")

    ledger.ledger_type = data.ledger_type
    ledger.client_name = data.client_name
    ledger.phone = data.phone
    ledger.currency = data.currency
    ledger.exchange_rate = data.exchange_rate
    ledger.due_date = data.due_date
    ledger.notes = data.notes

    diff = data.total_amount - ledger.total_amount
    ledger.total_amount = data.total_amount
    ledger.remaining_amount += diff
    if ledger.remaining_amount < 0:
        ledger.remaining_amount = 0.0

    db.commit()
    db.refresh(ledger)
    return ledger

@router.delete("/{ledger_id}")
def delete_ledger(ledger_id: str, current_admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    ledger = db.query(FinancialLedger).filter(FinancialLedger.id == ledger_id, FinancialLedger.workshop_id == current_admin.workshop_id).first()
    if not ledger:
        raise HTTPException(status_code=404, detail="Record not found")

    db.delete(ledger)
    db.commit()
    return {"message": "Deleted successfully"}