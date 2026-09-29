from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.models.models import Recipe, RecipeItem, RawMaterial, Customer, User, RoleEnum
from app.schemas.schemas import (
    RecipeCreate, RecipeOut, RecipeItemOut,
    SimulateRequest, SimulateResponse, SimulateItemResult
)
from app.api.deps import get_current_user, require_role
from app.services.paint_service import calculate_line_cost, calculate_cost_per_kg, mix_colors

router = APIRouter(prefix="/recipes", tags=["Recipes"])

# Tek sorguda reçete + kalemler + malzemeler + müşteri + oluşturan kullanıcı
RECIPE_LOAD_OPTIONS = (
    selectinload(Recipe.items).selectinload(RecipeItem.raw_material),
    selectinload(Recipe.customer),
    selectinload(Recipe.creator),
)


def _build_recipe_out(recipe: Recipe) -> RecipeOut:
    """Eager-load edilmiş Recipe ORM nesnesini RecipeOut şemasına dönüştürür."""
    items_out = [
        RecipeItemOut(
            id=item.id,
            raw_material_id=item.raw_material_id,
            raw_material_name=item.raw_material.name if item.raw_material else "?",
            hex_code=item.raw_material.hex_code if item.raw_material else None,
            weight_gr=float(item.weight_gr),
            unit_price_at_time=float(item.unit_price_at_time),
            line_cost=float(item.line_cost),
        )
        for item in recipe.items
    ]

    creator = recipe.creator
    return RecipeOut(
        id=recipe.id,
        customer_id=recipe.customer_id,
        customer_name=recipe.customer.company_name if recipe.customer else None,
        custom_paint_code=recipe.custom_paint_code,
        target_hex_code=recipe.target_hex_code,
        total_weight_gr=float(recipe.total_weight_gr) if recipe.total_weight_gr is not None else None,
        total_cost=float(recipe.total_cost) if recipe.total_cost is not None else None,
        cost_per_kg=float(recipe.cost_per_kg) if recipe.cost_per_kg is not None else None,
        margin_percentage=float(recipe.margin_percentage) if recipe.margin_percentage is not None else None,
        final_selling_price=float(recipe.final_selling_price) if recipe.final_selling_price is not None else None,
        notes=recipe.notes,
        branch_name=recipe.branch_name,
        created_by_name=(creator.full_name or creator.username) if creator else "?",
        created_at=recipe.created_at,
        items=items_out,
    )


async def _get_visible_materials(
    db: AsyncSession, material_ids: list[int], current_user: User
) -> dict[int, RawMaterial]:
    """Şube görünürlüğüne uyan malzemeleri getirir; erişilemeyen ID'de 404 fırlatır."""
    unique_ids = list(set(material_ids))
    result = await db.execute(
        select(RawMaterial).where(
            RawMaterial.id.in_(unique_ids),
            or_(
                RawMaterial.allowed_branch == None,
                RawMaterial.allowed_branch == current_user.branch_name,
            ),
        )
    )
    materials = {m.id: m for m in result.scalars().all()}
    for mid in unique_ids:
        if mid not in materials:
            raise HTTPException(status_code=404, detail=f"Malzeme bulunamadı: ID={mid}")
    return materials


@router.post("/simulate", response_model=SimulateResponse)
async def simulate(
    payload: SimulateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Kaydetmeden anlık maliyet ve renk hesaplama."""
    materials = await _get_visible_materials(
        db, [i.raw_material_id for i in payload.items], current_user
    )

    result_items = []
    total_cost = Decimal("0")
    total_weight = Decimal("0")
    pigments = []

    for inp in payload.items:
        mat = materials[inp.raw_material_id]
        line = calculate_line_cost(inp.weight_gr, mat.price_per_kg)
        total_cost += line
        total_weight += Decimal(str(inp.weight_gr))

        result_items.append(SimulateItemResult(
            raw_material_id=mat.id,
            name=mat.name,
            hex_code=mat.hex_code,
            weight_gr=inp.weight_gr,
            price_per_kg=float(mat.price_per_kg),
            line_cost=float(line),
        ))

        if mat.hex_code:
            pigments.append({"hex_code": mat.hex_code, "weight_gr": inp.weight_gr})

    cost_per_kg = calculate_cost_per_kg(total_cost, total_weight)
    mixed_hex = mix_colors(pigments)

    return SimulateResponse(
        items=result_items,
        total_weight_gr=float(total_weight.quantize(Decimal("0.01"))),
        total_cost=float(total_cost),
        cost_per_kg=float(cost_per_kg),
        mixed_hex_code=mixed_hex,
    )


@router.get("", response_model=list[RecipeOut])
async def list_recipes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int | None = Query(default=None, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """Kullanıcının şubesine ait tüm reçeteleri listeler."""
    query = (
        select(Recipe)
        .options(*RECIPE_LOAD_OPTIONS)
        .where(Recipe.branch_name == current_user.branch_name)
        .order_by(Recipe.created_at.desc())
        .offset(offset)
    )
    if limit is not None:
        query = query.limit(limit)
    result = await db.execute(query)
    return [_build_recipe_out(r) for r in result.scalars().all()]


@router.get("/customer/{customer_id}", response_model=list[RecipeOut])
async def list_recipes_by_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Belirli bir müşteriye ait reçeteleri listeler."""
    result = await db.execute(
        select(Recipe)
        .options(*RECIPE_LOAD_OPTIONS)
        .where(
            Recipe.customer_id == customer_id,
            Recipe.branch_name == current_user.branch_name
        )
        .order_by(Recipe.created_at.desc())
    )
    return [_build_recipe_out(r) for r in result.scalars().all()]


@router.get("/{recipe_id}", response_model=RecipeOut)
async def get_recipe(
    recipe_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Recipe)
        .options(*RECIPE_LOAD_OPTIONS)
        .where(
            Recipe.id == recipe_id,
            Recipe.branch_name == current_user.branch_name
        )
    )
    recipe = result.scalar_one_or_none()
    if not recipe:
        raise HTTPException(status_code=404, detail="Reçete bulunamadı")
    return _build_recipe_out(recipe)


@router.post("", response_model=RecipeOut)
async def create_recipe(
    payload: RecipeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Yeni reçete oluşturur (Tüm hesaplamalar burada yapılır — Zero Trust)."""
    if payload.customer_id is not None:
        cust_result = await db.execute(
            select(Customer).where(
                Customer.id == payload.customer_id,
                Customer.branch_name == current_user.branch_name
            )
        )
        if not cust_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Müşteri bulunamadı")

    materials = await _get_visible_materials(
        db, [i.raw_material_id for i in payload.items], current_user
    )

    total_cost = Decimal("0")
    total_weight = Decimal("0")
    pigments = []
    items_to_create = []

    for inp in payload.items:
        mat = materials[inp.raw_material_id]
        weight = Decimal(str(inp.weight_gr))
        line = calculate_line_cost(weight, mat.price_per_kg)
        total_cost += line
        total_weight += weight

        if mat.hex_code:
            pigments.append({"hex_code": mat.hex_code, "weight_gr": inp.weight_gr})

        items_to_create.append({
            "raw_material_id": mat.id,
            "weight_gr": weight.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "unit_price_at_time": mat.price_per_kg,
            "line_cost": line,
        })

    cost_per_kg = calculate_cost_per_kg(total_cost, total_weight)
    mixed_hex = mix_colors(pigments)

    margin = None
    final_price = None
    if payload.margin_percentage is not None:
        margin = Decimal(str(payload.margin_percentage)).quantize(Decimal("0.01"))
        final_price = (total_cost * (Decimal("100") + margin) / Decimal("100")).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )

    recipe = Recipe(
        customer_id=payload.customer_id,  # None olabilir
        custom_paint_code=payload.custom_paint_code,
        target_hex_code=mixed_hex,
        total_weight_gr=total_weight.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        total_cost=total_cost,
        cost_per_kg=cost_per_kg,
        margin_percentage=margin,
        final_selling_price=final_price,
        notes=payload.notes,
        branch_name=current_user.branch_name,
        created_by=current_user.id,
    )
    db.add(recipe)
    await db.flush()  # recipe.id'yi almak için

    for item_data in items_to_create:
        db.add(RecipeItem(recipe_id=recipe.id, **item_data))

    await db.commit()

    result = await db.execute(
        select(Recipe).options(*RECIPE_LOAD_OPTIONS).where(Recipe.id == recipe.id)
    )
    return _build_recipe_out(result.scalar_one())


@router.delete("/{recipe_id}")
async def delete_recipe(
    recipe_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.YETKILI))
):
    result = await db.execute(
        select(Recipe).where(
            Recipe.id == recipe_id,
            Recipe.branch_name == current_user.branch_name
        )
    )
    recipe = result.scalar_one_or_none()
    if not recipe:
        raise HTTPException(status_code=404, detail="Reçete bulunamadı")
    await db.delete(recipe)
    await db.commit()
    return {"detail": "Silindi"}
