"""Customer CRUD endpoints — scoped by business_id."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.customer import Customer
from app.models.admin_user import AdminUser
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from app.utils.auth import get_current_user, get_business_id_for_user

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("", response_model=list[CustomerResponse])
def list_customers(
    search: Optional[str] = Query(None, description="Search by name, phone, or email"),
    business_id: Optional[int] = Query(None, description="Business ID (platform admin only)"),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = get_business_id_for_user(current_user, business_id)
    query = db.query(Customer).filter(Customer.business_id == bid)
    if search:
        like = f"%{search}%"
        query = query.filter(
            (Customer.first_name.ilike(like))
            | (Customer.last_name.ilike(like))
            | (Customer.phone.ilike(like))
            | (Customer.email.ilike(like))
        )
    return query.order_by(Customer.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: int,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = get_business_id_for_user(current_user, business_id)
    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id, Customer.business_id == bid)
        .first()
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.post("", response_model=CustomerResponse, status_code=201)
def create_customer(
    body: CustomerCreate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = get_business_id_for_user(current_user, business_id)

    # Phone uniqueness check scoped to this business
    existing = (
        db.query(Customer)
        .filter(Customer.phone == body.phone, Customer.business_id == bid)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Customer with this phone already exists")

    customer = Customer(**body.model_dump(), business_id=bid)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: int,
    body: CustomerUpdate,
    business_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bid = get_business_id_for_user(current_user, business_id)
    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id, Customer.business_id == bid)
        .first()
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(customer, field, value)

    db.commit()
    db.refresh(customer)
    return customer
