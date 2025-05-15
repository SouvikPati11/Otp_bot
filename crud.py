from sqlalchemy.orm import Session
from . import models
from .models import User, Order, OrderStatus
from datetime import datetime, timedelta, timezone

def get_user(db: Session, telegram_id: int):
    return db.query(User).filter(User.telegram_id == telegram_id).first()

def create_user(db: Session, telegram_id: int, username: str = None, first_name: str = None, initial_balance: float = 0.0):
    db_user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        balance=initial_balance
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_or_create_user(db: Session, telegram_id: int, username: str = None, first_name: str = None):
    user = get_user(db, telegram_id)
    if not user:
        user = create_user(db, telegram_id, username, first_name)
    # Update username/first_name if they changed
    if username and user.username != username:
        user.username = username
    if first_name and user.first_name != first_name:
        user.first_name = first_name
    if db.is_modified(user):
        db.commit()
        db.refresh(user)
    return user

def update_user_balance(db: Session, user_id: int, amount_change: float):
    user = get_user(db, user_id) # Here user_id is telegram_id
    if user:
        user.balance += amount_change
        db.commit()
        db.refresh(user)
        return user
    return None

def create_order(db: Session, user_telegram_id: int, service_code: str, country_code: str, price: float, fivesim_order_id: int, phone_number: str, order_duration_minutes: int = 15):
    order = Order(
        user_id=user_telegram_id,
        fivesim_order_id=fivesim_order_id,
        service_code=service_code,
        country_code=country_code,
        phone_number=phone_number,
        price=price,
        status=OrderStatus.WAITING_OTP,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=order_duration_minutes)
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

def get_order_by_internal_id(db: Session, order_id: int):
    return db.query(Order).filter(Order.id == order_id).first()

def get_order_by_fivesim_id(db: Session, fivesim_order_id: int):
    return db.query(Order).filter(Order.fivesim_order_id == fivesim_order_id).first()

def update_order_status(db: Session, order_id: int, status: OrderStatus, otp_code: str = None):
    order = get_order_by_internal_id(db, order_id) # Assuming order_id is internal app ID
    if order:
        order.status = status
        if otp_code:
            order.otp_code = otp_code
        db.commit()
        db.refresh(order)
        return order
    return None

def get_user_orders(db: Session, user_telegram_id: int, limit: int = 10):
    return db.query(Order).filter(Order.user_id == user_telegram_id).order_by(Order.created_at.desc()).limit(limit).all()