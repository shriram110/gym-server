"""Seed the DB with packages, an admin user, sample customer, and class schedule."""
from datetime import datetime, date, timedelta
import random

from .database import SessionLocal, engine, Base
from . import models
from .auth import hash_password


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Packages
        if db.query(models.Package).count() == 0:
            db.add_all([
                models.Package(name="Basic", price=999, duration_months=1, color="slate",
                               description="Access to gym floor + 1 free trainer session",
                               features="Gym floor access,Locker,1 trainer session,Open Mon-Sat"),
                models.Package(name="Pro", price=2499, duration_months=3, color="indigo",
                               description="Everything in Basic + group classes + diet plan",
                               features="All Basic features,Group classes (Yoga/Zumba/HIIT),Personalized diet plan,Steam room"),
                models.Package(name="Elite", price=6999, duration_months=12, color="amber",
                               description="Annual membership with personal trainer",
                               features="All Pro features,Personal trainer 2x/week,Body composition analysis monthly,Priority booking,Free supplements starter kit"),
            ])

        # Admin
        if not db.query(models.User).filter_by(email="admin@musclemania.com").first():
            admin = models.User(
                email="admin@musclemania.com",
                name="Muscle Mania Admin",
                phone="9999999999",
                role=models.UserRole.admin,
                password_hash=hash_password("admin123"),
            )
            db.add(admin)

        # Sample customers
        sample_customers = [
            ("alex@example.com", "Alex Carter", "alex123"),
            ("priya@example.com", "Priya Sharma", "priya123"),
            ("ryan@example.com", "Ryan Walsh", "ryan123"),
        ]
        db.commit()
        pro_pkg = db.query(models.Package).filter_by(name="Pro").first()
        for email, name, pwd in sample_customers:
            if db.query(models.User).filter_by(email=email).first():
                continue
            u = models.User(email=email, name=name, role=models.UserRole.customer,
                            password_hash=hash_password(pwd), phone=f"98765{random.randint(10000, 99999)}")
            db.add(u)
            db.flush()
            db.add(models.MemberProfile(
                user_id=u.id,
                dob=date(1995, random.randint(1, 12), random.randint(1, 28)),
                gender=random.choice(["Male", "Female"]),
                height_cm=random.randint(155, 185),
                weight_kg=random.randint(55, 90),
                blood_group=random.choice(["A+", "B+", "O+", "AB+"]),
                emergency_contact="9999000000",
                goals=random.choice(["Build muscle", "Lose fat", "Improve endurance", "General fitness"]),
                package_id=pro_pkg.id if pro_pkg else None,
                joined_date=date.today() - timedelta(days=random.randint(10, 200)),
                fee_due_date=date.today() + timedelta(days=random.randint(-5, 25)),
            ))
            # Vitals — last 6 weeks
            base_w = random.randint(60, 85)
            for i in range(6, 0, -1):
                rec = datetime.utcnow() - timedelta(days=i * 7)
                w = base_w - i * 0.3 + random.uniform(-0.5, 0.5)
                db.add(models.Vital(
                    user_id=u.id, recorded_at=rec, weight_kg=round(w, 1),
                    body_fat_pct=round(20 - i * 0.2 + random.uniform(-0.5, 0.5), 1),
                    muscle_mass_kg=round(w * 0.4, 1),
                    bmi=round(w / (1.7 * 1.7), 1),
                    resting_hr=random.randint(60, 75),
                    blood_pressure=f"{random.randint(110, 125)}/{random.randint(70, 82)}",
                ))
            # Workouts
            exercises = ["Bench Press", "Squat", "Deadlift", "Pull-up", "OHP", "Row", "Lunges"]
            for i in range(20):
                db.add(models.Workout(
                    user_id=u.id,
                    date=date.today() - timedelta(days=random.randint(0, 30)),
                    exercise=random.choice(exercises),
                    sets=random.randint(3, 5),
                    reps=random.randint(6, 12),
                    weight_kg=random.randint(20, 100),
                    duration_min=random.randint(30, 75),
                ))
            # Attendance — last 30 days
            for i in range(20):
                d = datetime.utcnow() - timedelta(days=i, hours=random.randint(0, 8))
                db.add(models.Attendance(
                    user_id=u.id,
                    check_in_at=d,
                    check_out_at=d + timedelta(minutes=random.randint(45, 90)),
                ))
            # Fees
            db.add(models.Fee(
                user_id=u.id, amount=2499, due_date=date.today() + timedelta(days=random.randint(-3, 20)),
                status=random.choice([models.FeeStatus.pending, models.FeeStatus.paid]),
                note="Pro membership monthly"
            ))
            # Achievements
            db.add(models.Achievement(user_id=u.id, title="First Workout Logged!", badge_icon="🏋️"))
            db.add(models.Achievement(user_id=u.id, title="Week Warrior", badge_icon="📅"))
            # Notifications
            db.add(models.Notification(user_id=u.id, title="Welcome to Muscle Mania!",
                                       message="Your fitness journey starts now.", type="success"))

        # Enquiries
        if db.query(models.Enquiry).count() == 0:
            db.add_all([
                models.Enquiry(name="Sneha Iyer", email="sneha@example.com", phone="9876543210",
                               message="Interested in Pro plan, do you offer student discount?"),
                models.Enquiry(name="Mark D'Souza", email="mark@example.com",
                               message="What are your timings on Sundays?"),
            ])

        # Class schedule
        if db.query(models.ClassSchedule).count() == 0:
            now = datetime.utcnow().replace(hour=7, minute=0, second=0, microsecond=0)
            db.add_all([
                models.ClassSchedule(title="Morning Yoga", coach="Maya Rao", starts_at=now + timedelta(days=1), duration_min=60, capacity=15,
                                     description="Slow-flow yoga to start your day."),
                models.ClassSchedule(title="HIIT Burn", coach="Coach Vikram", starts_at=now + timedelta(days=2, hours=12), duration_min=45, capacity=20,
                                     description="High-intensity intervals — bring a towel."),
                models.ClassSchedule(title="Zumba Friday", coach="Lina M.", starts_at=now + timedelta(days=4, hours=11), duration_min=60, capacity=25,
                                     description="Latin-inspired dance fitness."),
            ])

        db.commit()
        print("Seed completed.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
