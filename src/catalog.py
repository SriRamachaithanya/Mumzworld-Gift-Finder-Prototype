from __future__ import annotations

import json
from pathlib import Path

from src.models import Product


def load_catalog() -> list[Product]:
    data_path = Path(__file__).resolve().parent.parent / "data" / "products.json"
    with data_path.open("r", encoding="utf-8") as file:
        raw_products = json.load(file)
    return [Product.model_validate(item) for item in raw_products]
