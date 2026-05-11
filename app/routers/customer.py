from datetime import datetime, date, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import require_customer, get_current_user

router = APIRouter(prefix="/api/me", tags=["customer"])


# -------- Profile --------
@router.get("/profile", response_model=schemas.ProfileOut)
def get_profile(user: models.User = Depends(require_customer), db: Session = Depends(get_db)):
    profile = db.query(models.MemberProfile).filter_by(user_id=user.id).first()
    if not profile:
        profile = models.MemberProfile(user_id=user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.put("/profile", response_model=schemas.ProfileOut)
def update_profile(payload: schemas.ProfileIn, user: models.User = Depends(require_customer), db: Session = Depends(get_db)):
    profile = db.query(models.MemberProfile).filter_by(user_id=user.id).first()
    if not profile:
        profile = models.MemberProfile(user_id=user.id)
        db.add(profile)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(profile, k, v)
    db.commit()
    db.refresh(profile)
    return profile


# -------- Vitals --------
@router.get("/vitals", response_model=List[schemas.VitalOut])
def list_vitals(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(models.Vital).filter_by(user_id=user.id).order_by(desc(models.Vital.recorded_at)).all()


@router.post("/vitals", response_model=schemas.VitalOut)
def add_vital(payload: schemas.VitalIn, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    data = payload.model_dump(exclude_unset=True)
    # auto-compute BMI if both height & weight present
    profile = db.query(models.MemberProfile).filter_by(user_id=user.id).first()
    if "bmi" not in data and data.get("weight_kg") and profile and profile.height_cm:
        h_m = profile.height_cm / 100
        if h_m > 0:
            data["bmi"] = round(data["weight_kg"] / (h_m * h_m), 1)
    v = models.Vital(user_id=user.id, **data)
    db.add(v)
    db.commit()
    db.refresh(v)
    _maybe_award(db, user, "vitals")
    return v


# -------- Workouts --------
@router.get("/workouts", response_model=List[schemas.WorkoutOut])
def list_workouts(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(models.Workout).filter_by(user_id=user.id).order_by(desc(models.Workout.date), desc(models.Workout.id)).limit(200).all()


@router.post("/workouts", response_model=schemas.WorkoutOut)
def add_workout(payload: schemas.WorkoutIn, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    data = payload.model_dump(exclude_unset=True)
    if not data.get("date"):
        data["date"] = date.today()
    w = models.Workout(user_id=user.id, **data)
    db.add(w)
    db.commit()
    db.refresh(w)
    _maybe_award(db, user, "workout")
    return w


@router.delete("/workouts/{workout_id}")
def delete_workout(workout_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    w = db.query(models.Workout).filter_by(id=workout_id, user_id=user.id).first()
    if not w:
        raise HTTPException(404, "Not found")
    db.delete(w)
    db.commit()
    return {"ok": True}


# -------- Attendance --------
@router.post("/attendance/check-in", response_model=schemas.AttendanceOut)
def check_in(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    today_start = datetime.combine(date.today(), datetime.min.time())
    existing = db.query(models.Attendance).filter(
        models.Attendance.user_id == user.id,
        models.Attendance.check_in_at >= today_start,
        models.Attendance.check_out_at.is_(None),
    ).first()
    if existing:
        return existing
    a = models.Attendance(user_id=user.id, check_in_at=datetime.utcnow())
    db.add(a)
    db.commit()
    db.refresh(a)
    _maybe_award(db, user, "checkin")
    return a


@router.post("/attendance/check-out", response_model=schemas.AttendanceOut)
def check_out(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    a = db.query(models.Attendance).filter(
        models.Attendance.user_id == user.id,
        models.Attendance.check_out_at.is_(None),
    ).order_by(desc(models.Attendance.check_in_at)).first()
    if not a:
        raise HTTPException(400, "No open check-in found")
    a.check_out_at = datetime.utcnow()
    db.commit()
    db.refresh(a)
    return a


@router.get("/attendance", response_model=List[schemas.AttendanceOut])
def my_attendance(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(models.Attendance).filter_by(user_id=user.id).order_by(desc(models.Attendance.check_in_at)).limit(60).all()


# -------- Fees (read only for customer) --------
@router.get("/fees", response_model=List[schemas.FeeOut])
def my_fees(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    fees = db.query(models.Fee).filter_by(user_id=user.id).order_by(desc(models.Fee.due_date)).all()
    today = date.today()
    for f in fees:
        if f.status == models.FeeStatus.pending and f.due_date < today:
            f.status = models.FeeStatus.overdue
            f.late_fee = max(50, (today - f.due_date).days * 10)
    db.commit()
    return fees


# -------- Achievements --------
@router.get("/achievements", response_model=List[schemas.AchievementOut])
def my_achievements(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(models.Achievement).filter_by(user_id=user.id).order_by(desc(models.Achievement.earned_at)).all()


# -------- Notifications --------
@router.get("/notifications", response_model=List[schemas.NotificationOut])
def my_notifications(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(models.Notification).filter_by(user_id=user.id).order_by(desc(models.Notification.created_at)).limit(30).all()


@router.post("/notifications/{notif_id}/read")
def mark_read(notif_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    n = db.query(models.Notification).filter_by(id=notif_id, user_id=user.id).first()
    if not n:
        raise HTTPException(404, "Not found")
    n.is_read = True
    db.commit()
    return {"ok": True}


# -------- Personal stats --------
@router.get("/stats")
def my_stats(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    workouts_total = db.query(models.Workout).filter_by(user_id=user.id).count()
    workouts_week = db.query(models.Workout).filter(
        models.Workout.user_id == user.id, models.Workout.date >= week_start
    ).count()
    attendance_month = db.query(models.Attendance).filter(
        models.Attendance.user_id == user.id, models.Attendance.check_in_at >= datetime.combine(month_start, datetime.min.time())
    ).count()

    # streak: consecutive days with attendance ending today or yesterday
    days = db.query(models.Attendance.check_in_at).filter_by(user_id=user.id).order_by(desc(models.Attendance.check_in_at)).limit(60).all()
    seen_days = sorted({d[0].date() for d in days}, reverse=True)
    streak = 0
    cursor = today
    if seen_days and seen_days[0] in (today, today - timedelta(days=1)):
        cursor = seen_days[0]
        for d in seen_days:
            if d == cursor:
                streak += 1
                cursor -= timedelta(days=1)

    latest_vital = db.query(models.Vital).filter_by(user_id=user.id).order_by(desc(models.Vital.recorded_at)).first()

    return {
        "workouts_total": workouts_total,
        "workouts_this_week": workouts_week,
        "attendance_this_month": attendance_month,
        "current_streak": streak,
        "latest_weight_kg": latest_vital.weight_kg if latest_vital else None,
        "latest_bmi": latest_vital.bmi if latest_vital else None,
    }


def _maybe_award(db: Session, user: models.User, kind: str):
    """Trivial achievement engine."""
    rules = {
        "workout": [(1, "First Workout Logged!", "🏋️"), (10, "10 Workouts Strong", "💪"), (50, "Half Century Club", "🔥")],
        "checkin": [(1, "First Check-in!", "✅"), (7, "Week Warrior", "📅"), (30, "Month of Iron", "🏆")],
        "vitals": [(1, "Tracking Started", "📊"), (10, "Data-Driven Athlete", "📈")],
    }
    if kind not in rules:
        return
    if kind == "workout":
        count = db.query(models.Workout).filter_by(user_id=user.id).count()
    elif kind == "checkin":
        count = db.query(models.Attendance).filter_by(user_id=user.id).count()
    else:
        count = db.query(models.Vital).filter_by(user_id=user.id).count()
    for threshold, title, icon in rules[kind]:
        if count == threshold:
            existing = db.query(models.Achievement).filter_by(user_id=user.id, title=title).first()
            if not existing:
                db.add(models.Achievement(user_id=user.id, title=title, badge_icon=icon, description=f"Earned for hitting {threshold} {kind}s"))
                db.add(models.Notification(user_id=user.id, title=f"Achievement unlocked: {title}", message=f"{icon} {title}", type="success"))
                db.commit()
