from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.models import Customer, Recipe, RoleEnum, User
from app.schemas.schemas import CustomerCreate, CustomerOut
from app.api.deps import get_current_user, require_role

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("", response_model=list[CustomerOut])
async def list_customers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int | None = Query(default=None, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """Sadece kullanıcının şubesine ait müşterileri listeler."""
    query = (
        select(Customer).where(Customer.branch_name == current_user.branch_name)
        .order_by(Customer.company_name)
        .offset(offset)
    )
    if limit is not None:
        query = query.limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=CustomerOut)
async def create_customer(
    payload: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    customer = Customer(**payload.model_dump(), branch_name=current_user.branch_name)
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


@router.get("/{customer_id}", response_model=CustomerOut)
async def get_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.branch_name == current_user.branch_name
        )
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    return customer


@router.put("/{customer_id}", response_model=CustomerOut)
async def update_customer(
    customer_id: int,
    payload: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.YETKILI))
):
    result = await db.execute(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.branch_name == current_user.branch_name
        )
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    for k, v in payload.model_dump().items():
        setattr(customer, k, v)
    await db.commit()
    await db.refresh(customer)
    return customer


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.ADMIN))
):
    result = await db.execute(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.branch_name == current_user.branch_name
        )
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    used = await db.execute(
        select(Recipe.id).where(Recipe.customer_id == customer_id).limit(1)
    )
    if used.first():
        raise HTTPException(
            status_code=409,
            detail="Bu firmaya bağlı reçeteler var, önce reçeteleri silin veya taşıyın"
        )
    await db.delete(customer)
    await db.commit()
    return {"detail": "Silindi"}
