from datetime import datetime, date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import require_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/members", response_model=List[schemas.MemberSummary])
def list_members(
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    qry = db.query(models.User).filter(models.User.role == models.UserRole.customer)
    if q:
        like = f"%{q}%"
        qry = qry.filter((models.User.name.ilike(like)) | (models.User.email.ilike(like)))
    users = qry.order_by(desc(models.User.created_at)).limit(200).all()

    out = []
    for u in users:
        profile = u.profile
        latest_att = db.query(models.Attendance).filter_by(user_id=u.id).order_by(desc(models.Attendance.check_in_at)).first()
        last_fee = db.query(models.Fee).filter_by(user_id=u.id).order_by(desc(models.Fee.due_date)).first()
        out.append(schemas.MemberSummary(
            id=u.id,
            name=u.name,
            email=u.email,
            phone=u.phone,
            role=u.role.value,
            joined_date=profile.joined_date if profile else None,
            package_name=profile.package.name if profile and profile.package else None,
            fee_status=last_fee.status.value if last_fee else None,
            last_attendance=latest_att.check_in_at if latest_att else None,
        ))
    return out


@router.get("/members/{user_id}")
def member_detail(user_id: int, db: Session = Depends(get_db), _: models.User = Depends(require_admin)):
    u = db.query(models.User).filter_by(id=user_id).first()
    if not u:
        raise HTTPException(404, "Not found")
    profile = u.profile
    return {
        "user": schemas.UserOut.model_validate(u).model_dump(),
        "profile": schemas.ProfileOut.model_validate(profile).model_dump() if profile else None,
        "vitals": [schemas.VitalOut.model_validate(v).model_dump() for v in
                   db.query(models.Vital).filter_by(user_id=u.id).order_by(desc(models.Vital.recorded_at)).limit(20)],
        "workouts": [schemas.WorkoutOut.model_validate(w).model_dump() for w in
                     db.query(models.Workout).filter_by(user_id=u.id).order_by(desc(models.Workout.date)).limit(20)],
        "attendance": [schemas.AttendanceOut.model_validate(a).model_dump() for a in
                       db.query(models.Attendance).filter_by(user_id=u.id).order_by(desc(models.Attendance.check_in_at)).limit(20)],
        "fees": [schemas.FeeOut.model_validate(f).model_dump() for f in
                 db.query(models.Fee).filter_by(user_id=u.id).order_by(desc(models.Fee.due_date)).limit(20)],
    }


# -------- Fees management --------
@router.post("/fees", response_model=schemas.FeeOut)
def create_fee(payload: schemas.FeeIn, db: Session = Depends(get_db), _: models.User = Depends(require_admin)):
    fee = models.Fee(**payload.model_dump())
    db.add(fee)
    # Notify member
    db.add(models.Notification(
        user_id=payload.user_id,
        title="New fee added",
        message=f"₹{payload.amount} due by {payload.due_date.isoformat()}",
        type="fee",
    ))
    db.commit()
    db.refresh(fee)
    return fee


@router.post("/fees/{fee_id}/mark-paid", response_model=schemas.FeeOut)
def mark_paid(fee_id: int, db: Session = Depends(get_db), _: models.User = Depends(require_admin)):
    f = db.query(models.Fee).filter_by(id=fee_id).first()
    if not f:
        raise HTTPException(404, "Not found")
    f.status = models.FeeStatus.paid
    f.paid_at = datetime.utcnow()
    db.add(models.Notification(
        user_id=f.user_id,
        title="Payment received",
        message=f"Thank you! ₹{f.amount} has been marked paid.",
        type="success",
    ))
    db.commit()
    db.refresh(f)
    return f


@router.get("/fees/overdue", response_model=List[schemas.FeeOut])
def overdue_fees(db: Session = Depends(get_db), _: models.User = Depends(require_admin)):
    today = date.today()
    fees = db.query(models.Fee).filter(
        models.Fee.status != models.FeeStatus.paid,
        models.Fee.due_date < today,
    ).order_by(models.Fee.due_date).all()
    for f in fees:
        f.status = models.FeeStatus.overdue
        f.late_fee = max(50, (today - f.due_date).days * 10)
    db.commit()
    return fees


# -------- Notifications: broadcast --------
@router.post("/broadcast")
def broadcast(title: str, message: str, db: Session = Depends(get_db), _: models.User = Depends(require_admin)):
    members = db.query(models.User).filter(models.User.role == models.UserRole.customer).all()
    for u in members:
        db.add(models.Notification(user_id=u.id, title=title, message=message, type="info"))
    db.commit()
    return {"ok": True, "count": len(members)}


# -------- Achievements: award manually --------
@router.post("/members/{user_id}/award")
def award(user_id: int, title: str, description: Optional[str] = None, badge_icon: str = "🏅",
          db: Session = Depends(get_db), _: models.User = Depends(require_admin)):
    u = db.query(models.User).filter_by(id=user_id).first()
    if not u:
        raise HTTPException(404, "Not found")
    a = models.Achievement(user_id=user_id, title=title, description=description, badge_icon=badge_icon)
    db.add(a)
    db.add(models.Notification(user_id=user_id, title=f"Achievement: {title}", message=f"{badge_icon} {title}", type="success"))
    db.commit()
    return {"ok": True}


# -------- Analytics dashboard --------
@router.get("/analytics")
def analytics(db: Session = Depends(get_db), _: models.User = Depends(require_admin)):
    today = date.today()
    month_start = today.replace(day=1)
    today_start = datetime.combine(today, datetime.min.time())

    total_members = db.query(models.User).filter(models.User.role == models.UserRole.customer).count()
    new_this_month = db.query(models.User).filter(
        models.User.role == models.UserRole.customer,
        models.User.created_at >= datetime.combine(month_start, datetime.min.time()),
    ).count()

    checkins_today = db.query(models.Attendance).filter(models.Attendance.check_in_at >= today_start).count()
    checkins_month = db.query(models.Attendance).filter(
        models.Attendance.check_in_at >= datetime.combine(month_start, datetime.min.time())
    ).count()

    pending_fees = db.query(func.coalesce(func.sum(models.Fee.amount), 0)).filter(
        models.Fee.status != models.FeeStatus.paid
    ).scalar() or 0
    paid_this_month = db.query(func.coalesce(func.sum(models.Fee.amount), 0)).filter(
        models.Fee.status == models.FeeStatus.paid,
        models.Fee.paid_at >= datetime.combine(month_start, datetime.min.time()),
    ).scalar() or 0
    overdue_count = db.query(models.Fee).filter(
        models.Fee.status != models.FeeStatus.paid,
        models.Fee.due_date < today,
    ).count()

    # Daily check-in trend (last 14 days)
    trend = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        d_start = datetime.combine(d, datetime.min.time())
        d_end = d_start + timedelta(days=1)
        c = db.query(models.Attendance).filter(
            models.Attendance.check_in_at >= d_start,
            models.Attendance.check_in_at < d_end,
        ).count()
        trend.append({"date": d.isoformat(), "checkins": c})

    # Top performers (by workouts in last 30 days)
    cutoff = today - timedelta(days=30)
    top = (
        db.query(models.User.name, func.count(models.Workout.id).label("workouts"))
        .join(models.Workout, models.Workout.user_id == models.User.id)
        .filter(models.Workout.date >= cutoff)
        .group_by(models.User.id, models.User.name)
        .order_by(desc("workouts"))
        .limit(5)
        .all()
    )

    # Package distribution
    pkg_dist = (
        db.query(models.Package.name, func.count(models.MemberProfile.id))
        .outerjoin(models.MemberProfile, models.MemberProfile.package_id == models.Package.id)
        .group_by(models.Package.name)
        .all()
    )

    return {
        "total_members": total_members,
        "new_this_month": new_this_month,
        "checkins_today": checkins_today,
        "checkins_month": checkins_month,
        "pending_fees": float(pending_fees),
        "paid_this_month": float(paid_this_month),
        "overdue_count": overdue_count,
        "checkin_trend": trend,
        "top_performers": [{"name": n, "workouts": w} for n, w in top],
        "package_distribution": [{"package": n or "None", "count": c} for n, c in pkg_dist],
    }


# -------- Enquiries management --------
@router.get("/enquiries", response_model=List[schemas.EnquiryOut])
def list_enquiries(db: Session = Depends(get_db), _: models.User = Depends(require_admin)):
    return db.query(models.Enquiry).order_by(desc(models.Enquiry.created_at)).limit(100).all()


@router.post("/enquiries/{eid}/status")
def update_enquiry(eid: int, status: str, db: Session = Depends(get_db), _: models.User = Depends(require_admin)):
    e = db.query(models.Enquiry).filter_by(id=eid).first()
    if not e:
        raise HTTPException(404, "Not found")
    e.status = status
    db.commit()
    return {"ok": True}
