import secrets
from dataclasses import dataclass
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.entities import AuthToken, User


@dataclass
class CurrentUser:
    id: int
    username: str
    role: str
    customer_id: int | None


def issue_token(db: Session, user: User) -> str:
    token = secrets.token_urlsafe(32)
    rec = AuthToken(token=token, user_id=user.id)
    db.add(rec)
    db.commit()
    return token


def get_current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> CurrentUser:
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(401, 'missing token')
    token = authorization.replace('Bearer ', '', 1)
    tk = db.query(AuthToken).filter(AuthToken.token == token).first()
    if not tk:
        raise HTTPException(401, 'invalid token')
    user = db.get(User, tk.user_id)
    if not user:
        raise HTTPException(401, 'user not found')
    return CurrentUser(id=user.id, username=user.username, role=user.role, customer_id=user.customer_id)


def require_roles(*roles: str):
    def checker(user: CurrentUser = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(403, 'forbidden')
        return user

    return checker
