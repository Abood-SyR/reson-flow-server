from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.models import IdempotencyKey

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