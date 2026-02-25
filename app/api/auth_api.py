from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, issue_token
from app.core.database import get_db
from app.models.entities import Customer, User
from app.schemas.auth import LoginIn

router = APIRouter(prefix='/auth', tags=['Auth'])


@router.post('/customer-login')
def customer_login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username, User.password == payload.password).first()
    if not user or user.role != 'customer' or not user.is_active:
        raise HTTPException(401, '客户账号不可用或密码错误')
    token = issue_token(db, user)
    return {'token': token, 'role': user.role, 'username': user.username}


@router.post('/admin-login')
def admin_login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username, User.password == payload.password).first()
    if not user or user.role not in ['admin', 'super_admin'] or not user.is_active:
        raise HTTPException(401, '管理员账号不可用或密码错误')
    token = issue_token(db, user)
    return {'token': token, 'role': user.role, 'username': user.username}


@router.get('/me')
def me(user=Depends(get_current_user), db: Session = Depends(get_db)):
    data = {
        'id': user.id,
        'username': user.username,
        'role': user.role,
        'is_active': user.is_active,
        'customer_id': user.customer_id,
    }
    if user.customer_id:
        c = db.get(Customer, user.customer_id)
        data['customer_name'] = c.name if c else None
    else:
        data['customer_name'] = None
    return data
