"""Service type CRUD endpoints — scoped by business_id."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.service_type import ServiceType
from app.models.admin_user import AdminUser
from app.schemas.service_type import ServiceTypeCreate, ServiceTypeUpdate, ServiceTypeResponse
from app.utils.auth import get_current_user, get_business_id_for_user

router = APIRouter(prefix="/api/services", tags=["services"])


@router.get("", response_model=list[ServiceTypeResponse])
def list_services(
    active_only: bool = True,
    business_id: int = Query(..., description="Business ID — required to scope results"),
    db: Session = Depends(get_db),
):
    """
    Public endpoint — list available services for a business.
    The business_id query param is required to identify the tenant.
    """
    query = db.query(ServiceType).filter(ServiceType.business_id == business_id)
    if active_only:
        query = query.filter(ServiceType.is_active == True)
    return query.order_by(ServiceType.category, ServiceType.name).all()


@router.post("", response_model=ServiceTypeResponse, status_code=201)
def create_service(
    body: ServiceTypeCreate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = get_business_id_for_user(current_user, business_id)
    service = ServiceType(**body.model_dump(), business_id=bid)
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


@router.put("/{service_id}", response_model=ServiceTypeResponse)
def update_service(
    service_id: int,
    body: ServiceTypeUpdate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = get_business_id_for_user(current_user, business_id)
    service = (
        db.query(ServiceType)
        .filter(ServiceType.id == service_id, ServiceType.business_id == bid)
        .first()
    )
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(service, field, value)

    db.commit()
    db.refresh(service)
    return service


@router.delete("/{service_id}", status_code=204)
def delete_service(
    service_id: int,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    """Soft-delete: sets is_active = False."""
    bid = get_business_id_for_user(current_user, business_id)
    service = (
        db.query(ServiceType)
        .filter(ServiceType.id == service_id, ServiceType.business_id == bid)
        .first()
    )
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    service.is_active = False
    db.commit()
