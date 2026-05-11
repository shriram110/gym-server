from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Date, ForeignKey, Boolean, Text, Enum
)
from sqlalchemy.orm import relationship
import enum

from .database import Base


class UserRole(str, enum.Enum):
    customer = "customer"
    admin = "admin"


class FeeStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    overdue = "overdue"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(120), nullable=False)
    phone = Column(String(20))
    role = Column(Enum(UserRole), default=UserRole.customer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("MemberProfile", back_populates="user", uselist=False, cascade="all, delete")
    vitals = relationship("Vital", back_populates="user", cascade="all, delete")
    workouts = relationship("Workout", back_populates="user", cascade="all, delete")
    attendance = relationship("Attendance", back_populates="user", cascade="all, delete")
    fees = relationship("Fee", back_populates="user", cascade="all, delete")
    achievements = relationship("Achievement", back_populates="user", cascade="all, delete")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete")


class Package(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    duration_months = Column(Integer, nullable=False)
    description = Column(Text)
    features = Column(Text)  # comma separated
    color = Column(String(20), default="indigo")


class MemberProfile(Base):
    __tablename__ = "member_profiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    dob = Column(Date)
    gender = Column(String(20))
    height_cm = Column(Float)
    weight_kg = Column(Float)
    blood_group = Column(String(10))
    emergency_contact = Column(String(100))
    goals = Column(Text)
    package_id = Column(Integer, ForeignKey("packages.id"))
    joined_date = Column(Date, default=date.today)
    fee_due_date = Column(Date)

    user = relationship("User", back_populates="profile")
    package = relationship("Package")


class Vital(Base):
    __tablename__ = "vitals"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    weight_kg = Column(Float)
    body_fat_pct = Column(Float)
    muscle_mass_kg = Column(Float)
    bmi = Column(Float)
    resting_hr = Column(Integer)
    blood_pressure = Column(String(20))
    waist_cm = Column(Float)
    chest_cm = Column(Float)

    user = relationship("User", back_populates="vitals")


class Workout(Base):
    __tablename__ = "workouts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, default=date.today)
    exercise = Column(String(100), nullable=False)
    sets = Column(Integer, default=0)
    reps = Column(Integer, default=0)
    weight_kg = Column(Float, default=0)
    notes = Column(Text)
    duration_min = Column(Integer)

    user = relationship("User", back_populates="workouts")


class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    check_in_at = Column(DateTime, default=datetime.utcnow)
    check_out_at = Column(DateTime)

    user = relationship("User", back_populates="attendance")


class Fee(Base):
    __tablename__ = "fees"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    due_date = Column(Date, nullable=False)
    paid_at = Column(DateTime)
    status = Column(Enum(FeeStatus), default=FeeStatus.pending, nullable=False)
    late_fee = Column(Float, default=0)
    note = Column(String(255))

    user = relationship("User", back_populates="fees")


class Achievement(Base):
    __tablename__ = "achievements"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(120), nullable=False)
    description = Column(Text)
    badge_icon = Column(String(50))  # emoji or icon name
    earned_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="achievements")


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(40), default="info")  # info | warn | success | fee
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")


class Enquiry(Base):
    __tablename__ = "enquiries"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20))
    message = Column(Text)
    status = Column(String(20), default="new")  # new | contacted | closed
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(10), nullable=False)  # user | bot
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chat_messages")


class ClassSchedule(Base):
    __tablename__ = "class_schedules"
    id = Column(Integer, primary_key=True)
    title = Column(String(120), nullable=False)
    coach = Column(String(100))
    starts_at = Column(DateTime, nullable=False)
    duration_min = Column(Integer, default=60)
    capacity = Column(Integer, default=20)
    description = Column(Text)
