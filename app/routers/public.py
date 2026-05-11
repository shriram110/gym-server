from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import asc

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/public", tags=["public"])


@router.get("/packages", response_model=List[schemas.PackageOut])
def list_packages(db: Session = Depends(get_db)):
    return db.query(models.Package).order_by(asc(models.Package.price)).all()


@router.get("/classes", response_model=List[schemas.ClassScheduleOut])
def list_classes(db: Session = Depends(get_db)):
    return db.query(models.ClassSchedule).order_by(asc(models.ClassSchedule.starts_at)).all()


@router.post("/enquiries", response_model=schemas.EnquiryOut)
def create_enquiry(payload: schemas.EnquiryIn, db: Session = Depends(get_db)):
    e = models.Enquiry(**payload.model_dump())
    db.add(e)
    db.commit()
    db.refresh(e)
    return e
