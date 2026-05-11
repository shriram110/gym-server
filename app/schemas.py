from datetime import datetime, date as DateT
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict


# ---------- Auth ----------
class RegisterIn(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone: Optional[str] = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str
    phone: Optional[str] = None
    role: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------- Packages ----------
class PackageOut(BaseModel):
    id: int
    name: str
    price: float
    duration_months: int
    description: Optional[str] = None
    features: Optional[str] = None
    color: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# ---------- Profile ----------
class ProfileIn(BaseModel):
    dob: Optional[DateT] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    blood_group: Optional[str] = None
    emergency_contact: Optional[str] = None
    goals: Optional[str] = None
    package_id: Optional[int] = None


class ProfileOut(ProfileIn):
    id: int
    user_id: int
    joined_date: Optional[DateT] = None
    fee_due_date: Optional[DateT] = None
    package: Optional[PackageOut] = None
    model_config = ConfigDict(from_attributes=True)


# ---------- Vitals ----------
class VitalIn(BaseModel):
    weight_kg: Optional[float] = None
    body_fat_pct: Optional[float] = None
    muscle_mass_kg: Optional[float] = None
    bmi: Optional[float] = None
    resting_hr: Optional[int] = None
    blood_pressure: Optional[str] = None
    waist_cm: Optional[float] = None
    chest_cm: Optional[float] = None


class VitalOut(VitalIn):
    id: int
    recorded_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------- Workouts ----------
class WorkoutIn(BaseModel):
    exercise: str
    sets: int = 0
    reps: int = 0
    weight_kg: float = 0
    notes: Optional[str] = None
    duration_min: Optional[int] = None
    date: Optional[DateT] = None


class WorkoutOut(WorkoutIn):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ---------- Attendance ----------
class AttendanceOut(BaseModel):
    id: int
    user_id: int
    check_in_at: datetime
    check_out_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ---------- Fees ----------
class FeeIn(BaseModel):
    user_id: int
    amount: float
    due_date: DateT
    note: Optional[str] = None


class FeeOut(BaseModel):
    id: int
    user_id: int
    amount: float
    due_date: DateT
    paid_at: Optional[datetime] = None
    status: str
    late_fee: float
    note: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# ---------- Achievements ----------
class AchievementOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    badge_icon: Optional[str] = None
    earned_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------- Notifications ----------
class NotificationOut(BaseModel):
    id: int
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------- Enquiries ----------
class EnquiryIn(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    message: Optional[str] = None


class EnquiryOut(EnquiryIn):
    id: int
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------- Chat ----------
class ChatIn(BaseModel):
    message: str


# ---------- Admin: Members ----------
class MemberSummary(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: Optional[str] = None
    role: str
    joined_date: Optional[DateT] = None
    package_name: Optional[str] = None
    fee_status: Optional[str] = None
    last_attendance: Optional[datetime] = None


class ClassScheduleOut(BaseModel):
    id: int
    title: str
    coach: Optional[str] = None
    starts_at: datetime
    duration_min: int
    capacity: int
    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# Allow forward refs
TokenOut.model_rebuild()
