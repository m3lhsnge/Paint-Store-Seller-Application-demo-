from decimal import Decimal

import pytest

from app.services.paint_service import (
    calculate_line_cost,
    calculate_cost_per_kg,
    mix_colors,
)


class TestCalculateLineCost:
    def test_basic(self):
        # 500 g × 200 ₺/KG = 100 ₺
        assert calculate_line_cost(500, Decimal("200")) == Decimal("100.0000")

    def test_float_inputs(self):
        assert calculate_line_cost(100.5, 85.0) == Decimal("8.5425")

    def test_rounding_half_up(self):
        # 1 g × 0.15 ₺/KG = 0.00015 → 0.0002'ye yuvarlanır
        assert calculate_line_cost(1, Decimal("0.15")) == Decimal("0.0002")

    def test_zero_weight(self):
        assert calculate_line_cost(0, Decimal("200")) == Decimal("0.0000")

    def test_no_float_precision_drift(self):
        # 0.1 + 0.2 tarzı float hataları oluşmamalı
        assert calculate_line_cost("100", "330.30") == Decimal("33.0300")


class TestCalculateCostPerKg:
    def test_basic(self):
        # 100 ₺ / 500 g → 200 ₺/KG
        assert calculate_cost_per_kg(Decimal("100"), Decimal("500")) == Decimal("200.0000")

    def test_zero_weight_returns_zero(self):
        assert calculate_cost_per_kg(Decimal("100"), 0) == Decimal("0")

    def test_negative_weight_returns_zero(self):
        assert calculate_cost_per_kg(Decimal("100"), -5) == Decimal("0")


class TestMixColors:
    def test_empty_returns_none(self):
        assert mix_colors([]) is None

    def test_no_pigments_returns_none(self):
        assert mix_colors([{"hex_code": None, "weight_gr": 100}]) is None

    def test_single_pigment_preserved(self):
        result = mix_colors([{"hex_code": "#FF0000", "weight_gr": 100}])
        assert result == "#FF0000"

    def test_equal_black_white_mix(self):
        result = mix_colors([
            {"hex_code": "#FFFFFF", "weight_gr": 100},
            {"hex_code": "#000000", "weight_gr": 100},
        ])
        # Karesel ortalama: sqrt(255² / 2) ≈ 180
        assert result == "#B4B4B4"

    def test_invalid_hex_skipped(self):
        result = mix_colors([
            {"hex_code": "kırmızı", "weight_gr": 100},
            {"hex_code": "#FF0000", "weight_gr": 100},
        ])
        assert result == "#FF0000"

    def test_all_invalid_returns_none(self):
        assert mix_colors([{"hex_code": "#GGGGGG", "weight_gr": 100}]) is None

    def test_zero_weight_pigment_ignored(self):
        result = mix_colors([
            {"hex_code": "#FFFFFF", "weight_gr": 0},
            {"hex_code": "#FF0000", "weight_gr": 100},
        ])
        assert result == "#FF0000"

    def test_output_format(self):
        result = mix_colors([
            {"hex_code": "#ff8800", "weight_gr": 30},
            {"hex_code": "#0088ff", "weight_gr": 70},
        ])
        assert result is not None
        assert len(result) == 7
        assert result.startswith("#")
        int(result[1:], 16)  # geçerli hex olmalı
