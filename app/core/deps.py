from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import User

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security), db: Session = Depends(get_db)) -> User:
    token = credentials.credentials
    user = db.query(User).filter(User.token == token, User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token or inactive account"
        )
    return user

def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ["admin", "partner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation permitted for admins and partners only"
        )
    return current_user

def get_current_worker(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "worker":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation permitted for workers only"
        )
    return current_user