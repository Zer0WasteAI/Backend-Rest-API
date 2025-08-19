import importlib
import os
from pathlib import Path
from flask import Flask

from src.infrastructure.db.base import db


def test_import_all_orm_models_and_create_tables(app: Flask):
    models_dir = Path("src/infrastructure/db/models")
    for py in models_dir.glob("*.py"):
        if py.name == "__init__.py":
            continue
        module_path = "src.infrastructure.db.models." + py.stem
        importlib.import_module(module_path)

    with app.app_context():
        db.create_all()
        # ensure some expected tables are registered
        tables = set(db.metadata.tables.keys())
        assert any("recipe" in t for t in tables)
        assert any("ingredient" in t for t in tables)
        assert any("user" in t for t in tables)

