from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.models.models import RawMaterial, Category, RecipeItem, RoleEnum, User
from app.schemas.schemas import RawMaterialCreate, RawMaterialOut, CategoryCreate, CategoryOut
from app.api.deps import get_current_user, require_role

router = APIRouter(prefix="/materials", tags=["Materials"])


async def _get_category(db: AsyncSession, category_id: int) -> Category:
    result = await db.execute(select(Category).where(Category.id == category_id))
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=400, detail=f"Kategori bulunamadı: ID={category_id}")
    return cat


async def _load_material(db: AsyncSession, material_id: int) -> RawMaterial | None:
    result = await db.execute(
        select(RawMaterial)
        .options(selectinload(RawMaterial.category))
        .where(RawMaterial.id == material_id)
    )
    return result.scalar_one_or_none()


# --- KATEGORİLER ---

@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Kullanıcının şubesine göre görünür kategorileri getirir."""
    result = await db.execute(
        select(Category).where(
            or_(Category.allowed_branch == None, Category.allowed_branch == current_user.branch_name)
        ).order_by(Category.name)
    )
    return result.scalars().all()


@router.post("/categories", response_model=CategoryOut)
async def create_category(
    payload: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.YETKILI))
):
    existing = await db.execute(select(Category).where(Category.name == payload.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Bu isimde bir kategori zaten var")
    cat = Category(**payload.model_dump())
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


# --- HAMMADDELEr ---

@router.get("", response_model=list[RawMaterialOut])
async def list_materials(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int | None = Query(default=None, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """Kullanıcının şubesine göre görünür hammaddeleri getirir."""
    query = (
        select(RawMaterial)
        .options(selectinload(RawMaterial.category))
        .where(
            or_(RawMaterial.allowed_branch == None, RawMaterial.allowed_branch == current_user.branch_name)
        )
        .order_by(RawMaterial.name)
        .offset(offset)
    )
    if limit is not None:
        query = query.limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=RawMaterialOut)
async def create_material(
    payload: RawMaterialCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.YETKILI))
):
    await _get_category(db, payload.category_id)
    mat = RawMaterial(**payload.model_dump())
    db.add(mat)
    await db.commit()
    return await _load_material(db, mat.id)


@router.put("/{material_id}", response_model=RawMaterialOut)
async def update_material(
    material_id: int,
    payload: RawMaterialCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.YETKILI))
):
    mat = await _load_material(db, material_id)
    if not mat:
        raise HTTPException(status_code=404, detail="Malzeme bulunamadı")
    await _get_category(db, payload.category_id)
    for k, v in payload.model_dump().items():
        setattr(mat, k, v)
    await db.commit()
    return await _load_material(db, material_id)


@router.delete("/{material_id}")
async def delete_material(
    material_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.ADMIN))
):
    result = await db.execute(select(RawMaterial).where(RawMaterial.id == material_id))
    mat = result.scalar_one_or_none()
    if not mat:
        raise HTTPException(status_code=404, detail="Malzeme bulunamadı")
    used = await db.execute(
        select(RecipeItem.id).where(RecipeItem.raw_material_id == material_id).limit(1)
    )
    if used.first():
        raise HTTPException(
            status_code=409,
            detail="Bu malzeme kayıtlı reçetelerde kullanılıyor, silinemez"
        )
    await db.delete(mat)
    await db.commit()
    return {"detail": "Silindi"}
