from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from .database import db

class OrderStatus(enum.Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT" # Should not happen if we pre-check balance
    WAITING_OTP = "WAITING_OTP"
    OTP_RECEIVED = "OTP_RECEIVED"
    COMPLETED = "COMPLETED" # After OTP is used/confirmed (could be same as OTP_RECEIVED)
    TIMEOUT_NO_OTP = "TIMEOUT_NO_OTP"
    CANCELED_BY_USER = "CANCELED_BY_USER"
    REFUNDED = "REFUNDED"
    ERROR = "ERROR"

class User(db.Model):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True) # Our internal ID
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    balance = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    orders = relationship("Order", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, balance={self.balance})>"

class Order(db.Model):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True) # Our internal ID
    user_id = Column(Integer, ForeignKey("users.telegram_id"), nullable=False)
    fivesim_order_id = Column(Integer, unique=True, nullable=True, index=True) # 5sim's order ID
    service_code = Column(String, nullable=False) # e.g., "instagram", "telegram"
    country_code = Column(String, nullable=False) # e.g., "india", "russia"
    phone_number = Column(String, nullable=True)
    otp_code = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    status = Column(SQLAlchemyEnum(OrderStatus), default=OrderStatus.PENDING_PAYMENT, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=True) # When the 5sim order/number expires

    user = relationship("User", back_populates="orders")

    def __repr__(self):
        return f"<Order(id={self.id}, service={self.service_code}, status={self.status})>"