"""
Demo verilerini veritabanına ekleyen seed scripti.
Çalıştırmak için: python seed.py (backend/ klasöründe)
"""
import asyncio
from decimal import Decimal
from app.db.session import async_session, engine, Base
from app.models.models import User, Category, RawMaterial, Customer, Recipe, RecipeItem, RoleEnum
from app.core.security import get_password_hash
from app.services.paint_service import calculate_line_cost, calculate_cost_per_kg, mix_colors


async def seed():
    # Tabloları oluştur
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # ── KULLANICILAR ──────────────────────────────────────────────
        users = [
            User(username="admin",    full_name="Sistem Yöneticisi", password_hash=get_password_hash("admin123"),   branch_name="Şube A", role=RoleEnum.ADMIN),
            User(username="yetkili_a",full_name="Ahmet Yılmaz",      password_hash=get_password_hash("yetkili123"), branch_name="Şube A", role=RoleEnum.YETKILI),
            User(username="yetkili_b",full_name="Fatma Kaya",        password_hash=get_password_hash("yetkili123"), branch_name="Şube B", role=RoleEnum.YETKILI),
            User(username="usta_a",   full_name="Mehmet Demir",      password_hash=get_password_hash("usta123"),    branch_name="Şube A", role=RoleEnum.USER),
            User(username="usta_b",   full_name="Ayşe Çelik",        password_hash=get_password_hash("usta123"),    branch_name="Şube B", role=RoleEnum.USER),
        ]
        db.add_all(users)
        await db.flush()

        # ── KATEGORİLER ───────────────────────────────────────────────
        categories = [
            Category(name="Pigmentler",       allowed_branch=None),     # Herkes
            Category(name="Tinerlер",         allowed_branch=None),     # Herkes
            Category(name="Sertleştiriciler", allowed_branch=None),     # Herkes
            Category(name="Özel Katkılar A",  allowed_branch="Şube A"), # Sadece A
            Category(name="Özel Katkılar B",  allowed_branch="Şube B"), # Sadece B
        ]
        db.add_all(categories)
        await db.flush()

        pig_cat = categories[0]
        tin_cat = categories[1]
        ser_cat = categories[2]

        # ── HAMMADDELEr ───────────────────────────────────────────────
        raw_materials = [
            # Pigmentler (hex_code var → renk hesabına katılır)
            RawMaterial(name="Titanyum Beyaz",   category_id=pig_cat.id, hex_code="#FFFFFF", price_per_kg=Decimal("180.00"), allowed_branch=None),
            RawMaterial(name="Karbon Siyah",     category_id=pig_cat.id, hex_code="#1A1A1A", price_per_kg=Decimal("220.00"), allowed_branch=None),
            RawMaterial(name="Krom Sarı",        category_id=pig_cat.id, hex_code="#FFD700", price_per_kg=Decimal("350.00"), allowed_branch=None),
            RawMaterial(name="Demir Oksit Kırmızı", category_id=pig_cat.id, hex_code="#B22222", price_per_kg=Decimal("280.00"), allowed_branch=None),
            RawMaterial(name="Ftalo Mavi",       category_id=pig_cat.id, hex_code="#003399", price_per_kg=Decimal("420.00"), allowed_branch=None),
            # Tinerler (hex_code yok → renk hesabına katılmaz)
            RawMaterial(name="Aseton Tiner",     category_id=tin_cat.id, hex_code=None, price_per_kg=Decimal("85.00"),  allowed_branch=None),
            RawMaterial(name="Selülozik Tiner",  category_id=tin_cat.id, hex_code=None, price_per_kg=Decimal("95.00"),  allowed_branch=None),
            # Sertleştiriciler
            RawMaterial(name="Poliüretan Sertleştirici", category_id=ser_cat.id, hex_code=None, price_per_kg=Decimal("310.00"), allowed_branch=None),
        ]
        db.add_all(raw_materials)
        await db.flush()

        titanium  = raw_materials[0]
        karbon    = raw_materials[1]
        krom_sari = raw_materials[2]
        demir_k   = raw_materials[3]
        ftalo     = raw_materials[4]
        aseton    = raw_materials[5]
        sert      = raw_materials[7]

        # ── MÜŞTERİLER ───────────────────────────────────────────────
        customers_a = [
            Customer(company_name="Güneş Otomotiv A.Ş.",    contact_info="0312 111 22 33", branch_name="Şube A"),
            Customer(company_name="Yıldız Karoser Sanayi",  contact_info="0312 444 55 66", branch_name="Şube A"),
            Customer(company_name="Akar Makina Ltd.",        contact_info="0312 777 88 99", branch_name="Şube A"),
        ]
        customers_b = [
            Customer(company_name="Doğu Metal Yapı A.Ş.",   contact_info="0422 111 22 33", branch_name="Şube B"),
            Customer(company_name="Batı Endüstri Grubu",     contact_info="0422 444 55 66", branch_name="Şube B"),
        ]
        db.add_all(customers_a + customers_b)
        await db.flush()

        gun_oto  = customers_a[0]
        yil_kar  = customers_a[1]
        dogu_met = customers_b[0]

        user_a = users[3]  # usta_a
        user_b = users[4]  # usta_b

        # ── REÇETELER ────────────────────────────────────────────────
        def make_items(ingredients):
            """ingredients: [(RawMaterial, weight_gr), ...]"""
            items = []
            total_cost = Decimal("0")
            total_weight = Decimal("0")
            pigments = []
            for mat, wgr in ingredients:
                price = mat.price_per_kg
                lc = calculate_line_cost(wgr, price)
                total_cost += lc
                total_weight += Decimal(wgr)
                if mat.hex_code:
                    pigments.append({"hex_code": mat.hex_code, "weight_gr": wgr})
                items.append({"mat": mat, "wgr": wgr, "price": price, "lc": lc})
            cost_pk = calculate_cost_per_kg(total_cost, total_weight)
            hex_mix = mix_colors(pigments)
            return items, total_cost, total_weight, cost_pk, hex_mix

        # Reçete 1 — Gri Boya
        r1_ingr = [(titanium, 600), (karbon, 50), (aseton, 150), (sert, 100)]
        r1_items, r1_cost, r1_weight, r1_cpk, r1_hex = make_items(r1_ingr)
        r1 = Recipe(
            customer_id=gun_oto.id, custom_paint_code="OTO-GRI-001", target_hex_code=r1_hex,
            total_weight_gr=Decimal(str(r1_weight)), total_cost=Decimal(str(round(r1_cost,4))),
            cost_per_kg=Decimal(str(r1_cpk)), margin_percentage=Decimal("25"),
            final_selling_price=Decimal(str(round(r1_cost * Decimal("1.25"), 4))),
            branch_name="Şube A", created_by=user_a.id
        )
        db.add(r1); await db.flush()
        for d in r1_items:
            db.add(RecipeItem(recipe_id=r1.id, raw_material_id=d["mat"].id, weight_gr=Decimal(str(d["wgr"])),
                              unit_price_at_time=Decimal(str(d["price"])), line_cost=Decimal(str(d["lc"]))))

        # Reçete 2 — Sarı Boya
        r2_ingr = [(krom_sari, 500), (titanium, 200), (aseton, 200), (sert, 100)]
        r2_items, r2_cost, r2_weight, r2_cpk, r2_hex = make_items(r2_ingr)
        r2 = Recipe(
            customer_id=yil_kar.id, custom_paint_code="IND-SARI-002", target_hex_code=r2_hex,
            total_weight_gr=Decimal(str(r2_weight)), total_cost=Decimal(str(round(r2_cost,4))),
            cost_per_kg=Decimal(str(r2_cpk)), margin_percentage=Decimal("30"),
            final_selling_price=Decimal(str(round(r2_cost * Decimal("1.30"), 4))),
            branch_name="Şube A", created_by=user_a.id
        )
        db.add(r2); await db.flush()
        for d in r2_items:
            db.add(RecipeItem(recipe_id=r2.id, raw_material_id=d["mat"].id, weight_gr=Decimal(str(d["wgr"])),
                              unit_price_at_time=Decimal(str(d["price"])), line_cost=Decimal(str(d["lc"]))))

        # Reçete 3 — Lacivert Boya
        r3_ingr = [(ftalo, 400), (karbon, 100), (titanium, 100), (aseton, 200), (sert, 100)]
        r3_items, r3_cost, r3_weight, r3_cpk, r3_hex = make_items(r3_ingr)
        r3 = Recipe(
            customer_id=gun_oto.id, custom_paint_code="OTO-LAC-003", target_hex_code=r3_hex,
            total_weight_gr=Decimal(str(r3_weight)), total_cost=Decimal(str(round(r3_cost,4))),
            cost_per_kg=Decimal(str(r3_cpk)), margin_percentage=Decimal("20"),
            final_selling_price=Decimal(str(round(r3_cost * Decimal("1.20"), 4))),
            branch_name="Şube A", created_by=user_a.id
        )
        db.add(r3); await db.flush()
        for d in r3_items:
            db.add(RecipeItem(recipe_id=r3.id, raw_material_id=d["mat"].id, weight_gr=Decimal(str(d["wgr"])),
                              unit_price_at_time=Decimal(str(d["price"])), line_cost=Decimal(str(d["lc"]))))

        # Reçete 4 — Şube B için Kırmızı
        r4_ingr = [(demir_k, 600), (titanium, 100), (aseton, 200), (sert, 100)]
        r4_items, r4_cost, r4_weight, r4_cpk, r4_hex = make_items(r4_ingr)
        r4 = Recipe(
            customer_id=dogu_met.id, custom_paint_code="MET-KIRMIZI-001", target_hex_code=r4_hex,
            total_weight_gr=Decimal(str(r4_weight)), total_cost=Decimal(str(round(r4_cost,4))),
            cost_per_kg=Decimal(str(r4_cpk)), margin_percentage=Decimal("25"),
            final_selling_price=Decimal(str(round(r4_cost * Decimal("1.25"), 4))),
            branch_name="Şube B", created_by=user_b.id
        )
        db.add(r4); await db.flush()
        for d in r4_items:
            db.add(RecipeItem(recipe_id=r4.id, raw_material_id=d["mat"].id, weight_gr=Decimal(str(d["wgr"])),
                              unit_price_at_time=Decimal(str(d["price"])), line_cost=Decimal(str(d["lc"]))))

        # Reçete 5 — Şube B için Beyaz
        r5_ingr = [(titanium, 800), (aseton, 150), (sert, 50)]
        r5_items, r5_cost, r5_weight, r5_cpk, r5_hex = make_items(r5_ingr)
        r5 = Recipe(
            customer_id=dogu_met.id, custom_paint_code="MET-BEYAZ-002", target_hex_code=r5_hex,
            total_weight_gr=Decimal(str(r5_weight)), total_cost=Decimal(str(round(r5_cost,4))),
            cost_per_kg=Decimal(str(r5_cpk)), margin_percentage=Decimal("20"),
            final_selling_price=Decimal(str(round(r5_cost * Decimal("1.20"), 4))),
            branch_name="Şube B", created_by=user_b.id
        )
        db.add(r5); await db.flush()
        for d in r5_items:
            db.add(RecipeItem(recipe_id=r5.id, raw_material_id=d["mat"].id, weight_gr=Decimal(str(d["wgr"])),
                              unit_price_at_time=Decimal(str(d["price"])), line_cost=Decimal(str(d["lc"]))))

        await db.commit()
        print("✅ Seed tamamlandı!")
        print("   Kullanıcılar:")
        print("   admin       / admin123    (ADMIN - Şube A)")
        print("   yetkili_a   / yetkili123  (YETKİLİ - Şube A)")
        print("   yetkili_b   / yetkili123  (YETKİLİ - Şube B)")
        print("   usta_a      / usta123     (USER - Şube A)")
        print("   usta_b      / usta123     (USER - Şube B)")


if __name__ == "__main__":
    asyncio.run(seed())
