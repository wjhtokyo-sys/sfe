from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, issue_token
from app.core.database import get_db
from app.models.entities import User
from app.schemas.auth import LoginIn

router = APIRouter(prefix='/auth', tags=['Auth'])


@router.post('/customer-login')
def customer_login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username, User.password == payload.password).first()
    if not user or user.role != 'customer':
        raise HTTPException(401, 'invalid customer credentials')
    token = issue_token(db, user)
    return {'token': token, 'role': user.role, 'username': user.username}


@router.post('/admin-login')
def admin_login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username, User.password == payload.password).first()
    if not user or user.role not in ['admin', 'super_admin']:
        raise HTTPException(401, 'invalid admin credentials')
    token = issue_token(db, user)
    return {'token': token, 'role': user.role, 'username': user.username}


@router.get('/me')
def me(user=Depends(get_current_user)):
    return user
