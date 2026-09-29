import math
import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Union

HEX_RE = re.compile(r"^#?[0-9a-fA-F]{6}$")

Number = Union[Decimal, float, int, str]

_CENT4 = Decimal("0.0001")


def _to_decimal(value: Number) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def calculate_line_cost(weight_gr: Number, price_per_kg: Number) -> Decimal:
    """
    Tek bir malzeme için satır maliyeti hesaplar.
    Formül: weight_gr * (price_per_kg / 1000)
    """
    weight = _to_decimal(weight_gr)
    price = _to_decimal(price_per_kg)
    return (weight * price / 1000).quantize(_CENT4, rounding=ROUND_HALF_UP)


def calculate_cost_per_kg(total_cost: Number, total_weight_gr: Number) -> Decimal:
    """
    Elde edilen karışımın KG başına birim maliyetini hesaplar.
    Formül: total_cost / (total_weight_gr / 1000)
    """
    cost = _to_decimal(total_cost)
    weight = _to_decimal(total_weight_gr)
    if weight <= 0:
        return Decimal("0")
    return (cost * 1000 / weight).quantize(_CENT4, rounding=ROUND_HALF_UP)


def mix_colors(pigments: list[dict]) -> Optional[str]:
    """
    Pigment listesinden Ağırlıklı Karesel Ortalama (Quadratic Weighted Average)
    ile karışık renk kodu üretir.

    Her pigment dict: {"hex_code": "#RRGGBB", "weight_gr": float}
    Geçersiz hex kodları hesaba katılmaz.
    """
    valid = [
        p for p in pigments
        if p.get("hex_code") and HEX_RE.match(p["hex_code"]) and float(p["weight_gr"]) > 0
    ]
    if not valid:
        return None

    total_weight = sum(float(p["weight_gr"]) for p in valid)
    if total_weight == 0:
        return None

    r_sq, g_sq, b_sq = 0.0, 0.0, 0.0

    for p in valid:
        hex_code = p["hex_code"].lstrip("#")
        r = int(hex_code[0:2], 16)
        g = int(hex_code[2:4], 16)
        b = int(hex_code[4:6], 16)
        w = float(p["weight_gr"])

        r_sq += w * (r ** 2)
        g_sq += w * (g ** 2)
        b_sq += w * (b ** 2)

    r_mix = int(math.sqrt(r_sq / total_weight))
    g_mix = int(math.sqrt(g_sq / total_weight))
    b_mix = int(math.sqrt(b_sq / total_weight))

    # 0-255 aralığında tut
    r_mix = max(0, min(255, r_mix))
    g_mix = max(0, min(255, g_mix))
    b_mix = max(0, min(255, b_mix))

    return f"#{r_mix:02X}{g_mix:02X}{b_mix:02X}"
