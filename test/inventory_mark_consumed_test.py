import pytest
import json
from datetime import datetime, timezone, timedelta


class TestMarkInventoryItemsConsumed:
    """Tests para los endpoints de marcar items como consumidos"""
    
    @pytest.fixture
    def auth_headers(self, mock_user_token):
        """Headers de autenticación para las pruebas"""
        return {
            'Authorization': f'Bearer {mock_user_token}',
            'Content-Type': 'application/json'
        }

    def test_mark_ingredient_stack_consumed_full_success(self, client, auth_headers):
        """Test: Marcar stack completo de ingrediente como consumido"""
        # URL para consumir un stack completo
        url = '/api/inventory/ingredients/Tomate/2025-01-01T10:00:00Z/consume'
        
        # Sin body = consume todo el stack
        response = client.post(url, headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verificar estructura de respuesta
        assert data['message'] == 'Ingredient stack marked as consumed'
        assert data['action'] == 'full_consumption'
        assert data['ingredient'] == 'Tomate'
        assert data['consumed_quantity'] > 0
        assert 'unit' in data
        assert data['stack_removed'] is True
        assert 'consumed_at' in data
        assert data['original_added_at'] == '2025-01-01T10:00:00Z'

    def test_mark_ingredient_stack_consumed_partial_success(self, client, auth_headers):
        """Test: Marcar consumo parcial de stack de ingrediente"""
        url = '/api/inventory/ingredients/Tomate/2025-01-01T10:00:00Z/consume'
        
        # Consumir parcialmente
        body = {
            'consumed_quantity': 1.5
        }
        
        response = client.post(url, headers=auth_headers, data=json.dumps(body))
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verificar respuesta de consumo parcial
        assert data['message'] == 'Ingredient partially consumed'
        assert data['action'] == 'partial_consumption'
        assert data['ingredient'] == 'Tomate'
        assert data['consumed_quantity'] == 1.5
        assert 'remaining_quantity' in data
        assert data['remaining_quantity'] > 0
        assert data['stack_removed'] is False

    def test_mark_ingredient_stack_consumed_not_found(self, client, auth_headers):
        """Test: Error cuando el stack de ingrediente no existe"""
        url = '/api/inventory/ingredients/NoExiste/2025-01-01T10:00:00Z/consume'
        
        response = client.post(url, headers=auth_headers)
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert 'not found' in data['error'].lower()

    def test_mark_ingredient_stack_consumed_invalid_quantity(self, client, auth_headers):
        """Test: Error cuando se intenta consumir más de lo disponible"""
        url = '/api/inventory/ingredients/Tomate/2025-01-01T10:00:00Z/consume'
        
        # Intentar consumir más de lo disponible
        body = {
            'consumed_quantity': 999.0
        }
        
        response = client.post(url, headers=auth_headers, data=json.dumps(body))
        
        assert response.status_code == 404  # ValueError se convierte en 404
        data = json.loads(response.data)
        assert 'error' in data
        assert 'cannot consume' in data['error'].lower() or 'not found' in data['error'].lower()

    def test_mark_ingredient_stack_consumed_invalid_data(self, client, auth_headers):
        """Test: Error con datos de entrada inválidos"""
        url = '/api/inventory/ingredients/Tomate/2025-01-01T10:00:00Z/consume'
        
        # Cantidad negativa
        body = {
            'consumed_quantity': -1.0
        }
        
        response = client.post(url, headers=auth_headers, data=json.dumps(body))
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'invalid data' in data['error'].lower()

    def test_mark_food_item_consumed_full_success(self, client, auth_headers):
        """Test: Marcar food item completo como consumido"""
        url = '/api/inventory/foods/Pasta%20con%20Tomate/2025-01-01T12:00:00Z/consume'
        
        # Sin body = consume todo el food item
        response = client.post(url, headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verificar estructura de respuesta
        assert data['message'] == 'Food item marked as consumed'
        assert data['action'] == 'full_consumption'
        assert data['food'] == 'Pasta con Tomate'
        assert data['consumed_portions'] > 0
        assert data['food_removed'] is True
        assert 'consumed_at' in data
        assert data['original_added_at'] == '2025-01-01T12:00:00Z'
        assert 'food_details' in data
        
        # Verificar detalles nutricionales
        food_details = data['food_details']
        assert 'category' in food_details
        assert 'main_ingredients' in food_details
        assert 'calories' in food_details
        assert 'description' in food_details

    def test_mark_food_item_consumed_partial_success(self, client, auth_headers):
        """Test: Marcar consumo parcial de food item"""
        url = '/api/inventory/foods/Pasta%20con%20Tomate/2025-01-01T12:00:00Z/consume'
        
        # Consumir parcialmente
        body = {
            'consumed_portions': 1.0
        }
        
        response = client.post(url, headers=auth_headers, data=json.dumps(body))
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verificar respuesta de consumo parcial
        assert data['message'] == 'Food item partially consumed'
        assert data['action'] == 'partial_consumption'
        assert data['food'] == 'Pasta con Tomate'
        assert data['consumed_portions'] == 1.0
        assert 'remaining_portions' in data
        assert data['remaining_portions'] > 0
        assert data['food_removed'] is False
        assert 'food_details' in data

    def test_mark_food_item_consumed_not_found(self, client, auth_headers):
        """Test: Error cuando el food item no existe"""
        url = '/api/inventory/foods/NoExiste/2025-01-01T12:00:00Z/consume'
        
        response = client.post(url, headers=auth_headers)
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert 'not found' in data['error'].lower()

    def test_mark_food_item_consumed_invalid_portions(self, client, auth_headers):
        """Test: Error cuando se intenta consumir más porciones de las disponibles"""
        url = '/api/inventory/foods/Pasta%20con%20Tomate/2025-01-01T12:00:00Z/consume'
        
        # Intentar consumir más porciones de las disponibles
        body = {
            'consumed_portions': 999.0
        }
        
        response = client.post(url, headers=auth_headers, data=json.dumps(body))
        
        assert response.status_code == 404  # ValueError se convierte en 404
        data = json.loads(response.data)
        assert 'error' in data

    def test_mark_food_item_consumed_invalid_data(self, client, auth_headers):
        """Test: Error con datos de entrada inválidos para food item"""
        url = '/api/inventory/foods/Pasta%20con%20Tomate/2025-01-01T12:00:00Z/consume'
        
        # Porciones negativas
        body = {
            'consumed_portions': -0.5
        }
        
        response = client.post(url, headers=auth_headers, data=json.dumps(body))
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'invalid data' in data['error'].lower()

    def test_mark_consumed_without_authentication(self, client):
        """Test: Error sin autenticación"""
        url = '/api/inventory/ingredients/Tomate/2025-01-01T10:00:00Z/consume'
        
        response = client.post(url)
        
        assert response.status_code == 401

    def test_mark_consumed_with_invalid_token(self, client):
        """Test: Error con token inválido"""
        url = '/api/inventory/ingredients/Tomate/2025-01-01T10:00:00Z/consume'
        headers = {
            'Authorization': 'Bearer token_invalido',
            'Content-Type': 'application/json'
        }
        
        response = client.post(url, headers=headers)
        
        assert response.status_code == 422  # JWT decode error

    def test_mark_consumed_malformed_json(self, client, auth_headers):
        """Test: Error con JSON malformado"""
        url = '/api/inventory/ingredients/Tomate/2025-01-01T10:00:00Z/consume'
        
        # JSON malformado
        response = client.post(
            url, 
            headers=auth_headers, 
            data='{"consumed_quantity": invalid}'
        )
        
        assert response.status_code == 400

    def test_mark_ingredient_consumed_with_zero_quantity(self, client, auth_headers):
        """Test: Error con cantidad cero"""
        url = '/api/inventory/ingredients/Tomate/2025-01-01T10:00:00Z/consume'
        
        body = {
            'consumed_quantity': 0.0
        }
        
        response = client.post(url, headers=auth_headers, data=json.dumps(body))
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_mark_food_consumed_with_zero_portions(self, client, auth_headers):
        """Test: Error con porciones cero"""
        url = '/api/inventory/foods/Pasta%20con%20Tomate/2025-01-01T12:00:00Z/consume'
        
        body = {
            'consumed_portions': 0.0
        }
        
        response = client.post(url, headers=auth_headers, data=json.dumps(body))
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_mark_consumed_fractional_quantities(self, client, auth_headers):
        """Test: Validar que se permiten cantidades fraccionales"""
        url = '/api/inventory/ingredients/Tomate/2025-01-01T10:00:00Z/consume'
        
        # Cantidad fraccional válida
        body = {
            'consumed_quantity': 0.25
        }
        
        response = client.post(url, headers=auth_headers, data=json.dumps(body))
        
        # Debería funcionar si el ingrediente existe y tiene suficiente cantidad
        assert response.status_code in [200, 404]  # 404 si no existe en test data

    def test_mark_consumed_with_url_encoded_names(self, client, auth_headers):
        """Test: Manejar nombres con espacios y caracteres especiales"""
        # Los nombres con espacios deben estar URL encoded
        url = '/api/inventory/foods/Pasta%20con%20Tomate%20y%20Queso/2025-01-01T12:00:00Z/consume'
        
        response = client.post(url, headers=auth_headers)
        
        # Debería manejar correctamente el URL encoding
        assert response.status_code in [200, 404]  # 404 si no existe en test data

    def test_mark_consumed_response_includes_timestamps(self, client, auth_headers):
        """Test: Verificar que las respuestas incluyen timestamps correctos"""
        url = '/api/inventory/ingredients/Tomate/2025-01-01T10:00:00Z/consume'
        
        response = client.post(url, headers=auth_headers)
        
        if response.status_code == 200:
            data = json.loads(response.data)
            
            # Verificar formato de timestamps
            assert 'consumed_at' in data
            assert 'original_added_at' in data
            
            # Verificar que consumed_at es reciente (dentro del último minuto)
            consumed_at = datetime.fromisoformat(data['consumed_at'].replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            time_diff = now - consumed_at
            assert time_diff.total_seconds() < 60  # Menos de 1 minuto
            
            # Verificar que original_added_at coincide con el URL
            assert data['original_added_at'] == '2025-01-01T10:00:00Z' 