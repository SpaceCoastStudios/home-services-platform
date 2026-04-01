"""Technician CRUD endpoints — scoped by business_id."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.technician import Technician
from app.models.admin_user import AdminUser
from app.schemas.technician import TechnicianCreate, TechnicianUpdate, TechnicianResponse
from app.utils.auth import get_current_user, get_business_id_for_user

router = APIRouter(prefix="/api/technicians", tags=["technicians"])


@router.get("", response_model=list[TechnicianResponse])
def list_technicians(
    active_only: bool = True,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = get_business_id_for_user(current_user, business_id)
    query = db.query(Technician).filter(Technician.business_id == bid)
    if active_only:
        query = query.filter(Technician.is_active == True)
    return query.order_by(Technician.name).all()


@router.post("", response_model=TechnicianResponse, status_code=201)
def create_technician(
    body: TechnicianCreate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = get_business_id_for_user(current_user, business_id)
    technician = Technician(**body.model_dump(), business_id=bid)
    db.add(technician)
    db.commit()
    db.refresh(technician)
    return technician


@router.put("/{technician_id}", response_model=TechnicianResponse)
def update_technician(
    technician_id: int,
    body: TechnicianUpdate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = get_business_id_for_user(current_user, business_id)
    tech = (
        db.query(Technician)
        .filter(Technician.id == technician_id, Technician.business_id == bid)
        .first()
    )
    if not tech:
        raise HTTPException(status_code=404, detail="Technician not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(tech, field, value)

    db.commit()
    db.refresh(tech)
    return tech
