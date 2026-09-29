import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    Enum, ForeignKey, Numeric, Text
)
from sqlalchemy.orm import relationship
from app.db.session import Base


def utcnow() -> datetime:
    # Kolonlar TIMESTAMP WITHOUT TIME ZONE olduğu için naive UTC saklanır
    return datetime.now(timezone.utc).replace(tzinfo=None)


class RoleEnum(str, enum.Enum):
    ADMIN = "ADMIN"
    YETKILI = "YETKILI"
    USER = "USER"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    full_name = Column(String(128), nullable=True)
    password_hash = Column(String(256), nullable=False)
    branch_name = Column(String(64), nullable=False)          # "Şube A" veya "Şube B"
    role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.USER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)

    recipes = relationship("Recipe", back_populates="creator")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False, unique=True)
    # NULL = Herkes görebilir; "Şube A" / "Şube B" = sadece o şube
    allowed_branch = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=utcnow)

    raw_materials = relationship("RawMaterial", back_populates="category")


class RawMaterial(Base):
    __tablename__ = "raw_materials"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    hex_code = Column(String(7), nullable=True)               # Renk kodu (sadece pigmentler için)
    price_per_kg = Column(Numeric(12, 4), nullable=False)     # KG başına fiyat (₺)
    # NULL = Herkes görebilir; "Şube A" / "Şube B" = sadece o şube
    allowed_branch = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=utcnow)

    category = relationship("Category", back_populates="raw_materials")
    recipe_items = relationship("RecipeItem", back_populates="raw_material")

    @property
    def category_name(self):
        # Async oturumda lazy-load tetiklememek için sadece yüklü ilişkiyi okur
        cat = self.__dict__.get("category")
        return cat.name if cat else None


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(256), nullable=False)
    contact_info = Column(Text, nullable=True)                # Telefon, e-posta vb.
    branch_name = Column(String(64), nullable=False)          # Müşterinin kayıtlı olduğu şube
    created_at = Column(DateTime, default=utcnow)

    recipes = relationship("Recipe", back_populates="customer")


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    custom_paint_code = Column(String(64), nullable=False)    # Örn: OTO-1234
    target_hex_code = Column(String(7), nullable=True)        # Hesaplanan renk kodu
    total_weight_gr = Column(Numeric(12, 2), nullable=True)   # Toplam ağırlık (gram)
    total_cost = Column(Numeric(12, 4), nullable=True)        # Toplam maliyet (₺)
    cost_per_kg = Column(Numeric(12, 4), nullable=True)       # KG başına birim maliyet (₺)
    margin_percentage = Column(Numeric(5, 2), nullable=True)  # Kâr marjı (%)
    final_selling_price = Column(Numeric(12, 4), nullable=True)  # Nihai satış fiyatı (₺)
    notes = Column(Text, nullable=True)
    branch_name = Column(String(64), nullable=False)          # Reçetenin ait olduğu şube
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=utcnow)

    customer = relationship("Customer", back_populates="recipes")
    creator = relationship("User", back_populates="recipes")
    items = relationship("RecipeItem", back_populates="recipe", cascade="all, delete-orphan")


class RecipeItem(Base):
    __tablename__ = "recipe_items"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    raw_material_id = Column(Integer, ForeignKey("raw_materials.id"), nullable=False)
    weight_gr = Column(Numeric(10, 2), nullable=False)         # Kullanılan miktar (gram)
    # Kaydedildiği andaki anlık fiyat (fiyat sonradan değişse dahi kayıt korunur)
    unit_price_at_time = Column(Numeric(12, 4), nullable=False)
    line_cost = Column(Numeric(12, 4), nullable=False)         # weight_gr * (unit_price / 1000)

    recipe = relationship("Recipe", back_populates="items")
    raw_material = relationship("RawMaterial", back_populates="recipe_items")
