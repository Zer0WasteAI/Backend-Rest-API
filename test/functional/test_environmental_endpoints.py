import pytest


def test_calculate_from_title_returns_200(client, auth_header, monkeypatch):
    # Monkeypatch the use case factory to return a fake use case
    from src.interface.controllers import environmental_savings_controller as ctrl

    class FakeUseCase:
        def execute(self, user_uid, recipe_title):
            return {"recipe_title": recipe_title, "environmental_impact": {"co2_reduction_kg": 1.0}}

    monkeypatch.setattr(ctrl, "make_estimate_savings_by_title_use_case", lambda: FakeUseCase())

    rv = client.post(
        "/api/environmental_savings/calculate/from-title",
        json={"title": "Tortilla"},
        headers=auth_header,
    )
    assert rv.status_code == 200
    data = rv.get_json()
    assert data.get("recipe_title") == "Tortilla"
    assert "environmental_impact" in data


def test_environmental_summary_returns_200(client, auth_header, monkeypatch):
    from src.interface.controllers import environmental_savings_controller as ctrl

    class FakeSumUseCase:
        def execute(self, user_uid):
            return {"summary": {"total_co2_saved": 5.5, "user_uid": user_uid}}

    monkeypatch.setattr(ctrl, "make_sum_environmental_calculations_by_user", lambda: FakeSumUseCase())

    rv = client.get(
        "/api/environmental_savings/summary",
        headers=auth_header,
    )
    assert rv.status_code == 200
    data = rv.get_json()
    assert "summary" in data or "user_environmental_summary" in data

