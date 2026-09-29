from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.models import RoleEnum

HEX_PATTERN = r"^#[0-9a-fA-F]{6}$"


# --- AUTH ---
class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    branch_name: str
    full_name: Optional[str] = None


class SwitchBranchRequest(BaseModel):
    branch_name: str = Field(min_length=1, max_length=64)


# --- USER ---
class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    full_name: Optional[str] = None
    password: str = Field(min_length=6)
    branch_name: str = Field(min_length=1, max_length=64)
    role: RoleEnum = RoleEnum.USER


class UserOut(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    branch_name: str
    role: RoleEnum
    is_active: bool

    class Config:
        from_attributes = True


# --- CATEGORY ---
class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    allowed_branch: Optional[str] = None   # None = Herkes


class CategoryOut(BaseModel):
    id: int
    name: str
    allowed_branch: Optional[str] = None

    class Config:
        from_attributes = True


# --- RAW MATERIAL ---
class RawMaterialCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    category_id: int
    hex_code: Optional[str] = Field(default=None, pattern=HEX_PATTERN)
    price_per_kg: float = Field(ge=0)
    allowed_branch: Optional[str] = None   # None = Herkes


class RawMaterialOut(BaseModel):
    id: int
    name: str
    category_id: int
    category_name: Optional[str] = None
    hex_code: Optional[str] = None
    price_per_kg: float
    allowed_branch: Optional[str] = None

    class Config:
        from_attributes = True


# --- CUSTOMER ---
class CustomerCreate(BaseModel):
    company_name: str = Field(min_length=1, max_length=256)
    contact_info: Optional[str] = None


class CustomerOut(BaseModel):
    id: int
    company_name: str
    contact_info: Optional[str] = None
    branch_name: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- RECIPE ---
class RecipeItemInput(BaseModel):
    raw_material_id: int
    weight_gr: float = Field(gt=0)          # Frontend sadece bunu gönderiyor


class RecipeCreate(BaseModel):
    customer_id: Optional[int] = None
    custom_paint_code: str = Field(min_length=1, max_length=64)
    notes: Optional[str] = None
    margin_percentage: Optional[float] = Field(default=None, ge=0, le=999)
    items: list[RecipeItemInput] = Field(min_length=1)


class RecipeItemOut(BaseModel):
    id: int
    raw_material_id: int
    raw_material_name: str
    hex_code: Optional[str] = None
    weight_gr: float
    unit_price_at_time: float
    line_cost: float

    class Config:
        from_attributes = True


class RecipeOut(BaseModel):
    id: int
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    custom_paint_code: str
    target_hex_code: Optional[str] = None
    total_weight_gr: Optional[float] = None
    total_cost: Optional[float] = None
    cost_per_kg: Optional[float] = None
    margin_percentage: Optional[float] = None
    final_selling_price: Optional[float] = None
    notes: Optional[str] = None
    branch_name: str
    created_by_name: str
    created_at: datetime
    items: list[RecipeItemOut] = []

    class Config:
        from_attributes = True


# --- SİMÜLASYON (Kaydetmeden hesaplama) ---
class SimulateRequest(BaseModel):
    items: list[RecipeItemInput] = Field(min_length=1)


class SimulateItemResult(BaseModel):
    raw_material_id: int
    name: str
    hex_code: Optional[str] = None
    weight_gr: float
    price_per_kg: float
    line_cost: float


class SimulateResponse(BaseModel):
    items: list[SimulateItemResult]
    total_weight_gr: float
    total_cost: float
    cost_per_kg: float
    mixed_hex_code: Optional[str] = None
