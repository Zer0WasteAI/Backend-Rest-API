from datetime import datetime, timedelta, timezone

from flask import Flask

from src.infrastructure.db.base import db
from src.infrastructure.db.models.image_reference_orm import ImageReferenceORM
from src.infrastructure.db.models.ingredient_batch_orm import IngredientBatchORM
from src.domain.models.ingredient_batch import StorageLocation, LabelType, BatchState


def test_db_create_and_persist_minimal_models(app: Flask):
    # Ensure sqlalchemy uses in-memory sqlite (set in conftest)
    assert app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite")

    with app.app_context():
        db.create_all()

        # Persist an ImageReferenceORM
        img = ImageReferenceORM(
            uid="img-uid-1",
            name="tomato",
            image_path="/images/tomato.jpg",
            image_type="food"
        )
        db.session.add(img)

        # Persist an IngredientBatchORM
        batch = IngredientBatchORM(
            id="batch-uid-1",
            ingredient_uid="ingredient-1",
            qty=1.5,
            unit="kg",
            storage_location=StorageLocation.FRIDGE,
            label_type=LabelType.USE_BY,
            expiry_date=datetime.now(timezone.utc) + timedelta(days=3),
            state=BatchState.AVAILABLE,
            sealed=True,
            user_uid="user-uid-1",
        )
        db.session.add(batch)

        db.session.commit()

        # Query back
        found_img = ImageReferenceORM.query.filter_by(name="tomato").first()
        assert found_img is not None
        assert found_img.image_type == "food"

        found_batch = IngredientBatchORM.query.filter_by(id="batch-uid-1").first()
        assert found_batch is not None
        assert float(found_batch.qty) == 1.5
        assert found_batch.storage_location == StorageLocation.FRIDGE

