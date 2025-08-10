# 🧪 Unit Testing Guide - ZeroWasteAI API

## 📋 Overview

This guide provides a comprehensive approach to unit testing for the ZeroWasteAI API, following industry best practices and designed for thesis-level documentation and validation.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Install test dependencies
pip install -r requirements-test.txt
```

### 2. Validate Setup
```bash
# Validate test infrastructure
python validate_unit_tests.py
```

### 3. Run Tests
```bash
# Run all unit tests with coverage
python run_unit_tests.py

# Run specific test module
python run_unit_tests.py --module models

# Run with HTML coverage report
python run_unit_tests.py --html

# Run in parallel
python run_unit_tests.py --parallel 4
```

---

## 📁 Test Structure

```
test/
├── unit/                           # Unit tests (85%+ coverage target)
│   ├── domain/
│   │   ├── models/                 # Domain model tests
│   │   │   ├── test_user_model.py
│   │   │   ├── test_recipe_model.py
│   │   │   ├── test_inventory_model.py
│   │   │   └── test_ingredient_model.py
│   │   └── services/               # Domain service tests
│   ├── application/
│   │   ├── use_cases/             # Use case tests
│   │   │   ├── auth/
│   │   │   ├── recipes/
│   │   │   │   └── test_save_recipe_use_case.py
│   │   │   ├── inventory/
│   │   │   ├── planning/
│   │   │   └── recognition/
│   │   └── services/              # Application service tests
│   └── infrastructure/
│       ├── auth/
│       │   └── test_jwt_service.py
│       ├── db/                    # Repository tests
│       └── ai/                    # AI service tests
├── integration/                   # Integration tests
├── functional/                    # Functional tests
└── conftest.py                   # Shared test configuration
```

---

## 🎯 Test Categories & Examples

### 1. Domain Model Tests

**Purpose**: Validate business entities and their behavior
**Coverage Target**: 90%+

```python
# Example: test/unit/domain/models/test_user_model.py
class TestUserModel:
    def test_user_creation_with_required_fields(self):
        # Arrange
        uid = "test-uid-123"
        email = "test@example.com"
        
        # Act
        user = User(uid=uid, email=email)
        
        # Assert
        assert user.uid == uid
        assert user.email == email
```

**Key Test Scenarios**:
- ✅ Object creation with valid data
- ✅ Validation of required fields
- ✅ Business rule enforcement
- ✅ Edge cases and boundary conditions
- ✅ String representation and equality

### 2. Use Case Tests

**Purpose**: Validate business logic and orchestration
**Coverage Target**: 85%+

```python
# Example: test/unit/application/use_cases/recipes/test_save_recipe_use_case.py
class TestSaveRecipeUseCase:
    @pytest.fixture
    def mock_recipe_repository(self):
        return Mock()
    
    def test_execute_saves_recipe_successfully(self, use_case, mock_repository):
        # Test successful recipe saving with all validations
        pass
```

**Key Test Scenarios**:
- ✅ Successful execution paths
- ✅ Input validation
- ✅ Business rule enforcement
- ✅ Error handling and exceptions
- ✅ Repository interactions
- ✅ External service mocking

### 3. Service Tests

**Purpose**: Validate infrastructure services and integrations
**Coverage Target**: 80%+

```python
# Example: test/unit/infrastructure/auth/test_jwt_service.py
class TestJWTService:
    def test_create_tokens_success(self, jwt_service, mock_repository):
        # Test token creation with security features
        pass
```

**Key Test Scenarios**:
- ✅ Service initialization
- ✅ External API interactions (mocked)
- ✅ Error handling and retries
- ✅ Security validations
- ✅ Performance considerations

---

## 🛠️ Testing Tools & Utilities

### Core Framework
- **pytest**: Main testing framework
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking utilities
- **pytest-xdist**: Parallel execution

### Mocking Strategy
```python
# Repository mocking
@pytest.fixture
def mock_recipe_repository(self):
    return Mock()

# External service mocking  
@patch('src.infrastructure.auth.jwt_service.create_access_token')
def test_with_external_service_mock(mock_create_token):
    mock_create_token.return_value = "mocked_token"
    # Test implementation
```

### Test Data Management
```python
# Using fixtures for test data
@pytest.fixture
def valid_recipe_data(self):
    return {
        "title": "Test Recipe",
        "duration": "30 minutes",
        "difficulty": "Easy",
        # ... more fields
    }

# Parametrized testing
@pytest.mark.parametrize("uid,email", [
    ("uid1", "email1@test.com"),
    ("uid2", "email2@test.com"),
])
def test_multiple_scenarios(uid, email):
    # Test implementation
```

---

## 📊 Coverage Requirements

### Coverage Targets by Layer
| Layer | Target | Rationale |
|-------|--------|-----------|
| Domain Models | 90%+ | Core business logic |
| Use Cases | 85%+ | Business orchestration |
| Services | 80%+ | Infrastructure complexity |
| Controllers | 70%+ | Integration layer |

### Coverage Configuration
```ini
# pytest.ini
[coverage:run]
source = src/
omit = 
    */venv/*
    */migrations/*
    */test/*
    */__init__.py

[coverage:report]
fail_under = 85
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
```

### Coverage Commands
```bash
# Run with coverage
python run_unit_tests.py --coverage

# Generate HTML report
python run_unit_tests.py --html

# Generate XML for CI/CD
python run_unit_tests.py --xml

# View coverage in terminal
pytest --cov=src --cov-report=term-missing
```

---

## ✅ Best Practices

### 1. Test Naming Convention
```python
# Pattern: test_[method]_[scenario]_[expected_result]
def test_create_user_with_valid_data_should_succeed(self):
    pass

def test_create_user_with_invalid_email_should_raise_exception(self):
    pass
```

### 2. AAA Pattern (Arrange-Act-Assert)
```python
def test_example(self):
    # Arrange: Set up test data and mocks
    user_data = {"uid": "123", "email": "test@example.com"}
    
    # Act: Execute the operation being tested
    result = create_user(user_data)
    
    # Assert: Verify the expected outcome
    assert result.uid == "123"
    assert result.email == "test@example.com"
```

### 3. Mock External Dependencies
```python
# Mock external services, databases, APIs
@patch('src.infrastructure.ai.gemini_adapter_service.GeminiService')
def test_ai_service_integration(mock_gemini):
    mock_gemini.return_value.generate_recipe.return_value = expected_recipe
    # Test implementation
```

### 4. Test Edge Cases
```python
# Test boundary conditions
def test_inventory_with_zero_quantity(self):
    pass

def test_recipe_with_empty_ingredients_list(self):
    pass

def test_user_with_maximum_length_email(self):
    pass
```

### 5. Use Fixtures for Common Setup
```python
@pytest.fixture
def authenticated_user(self):
    return User(uid="test-user", email="test@example.com")

@pytest.fixture
def mock_database_session(self):
    with patch('src.infrastructure.db.base.db') as mock_db:
        yield mock_db
```

---

## 🔧 Configuration Files

### pytest.ini
```ini
[tool:pytest]
testpaths = test
addopts = 
    --strict-markers
    --cov=src
    --cov-report=term-missing
    --cov-fail-under=85
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
```

### requirements-test.txt
```txt
pytest==8.3.5
pytest-cov==4.0.0
pytest-mock==3.11.1
pytest-xdist==3.3.1
pytest-flask==1.2.0
coverage==7.8.0
factory-boy==3.3.0
faker==19.6.2
```

---

## 🚀 Running Tests

### Basic Commands
```bash
# Run all unit tests
python run_unit_tests.py

# Run specific test file
python run_unit_tests.py --file test/unit/domain/models/test_user_model.py

# Run tests for specific module
python run_unit_tests.py --module recipes

# Run with verbose output
python run_unit_tests.py --verbose

# Run in parallel (faster)
python run_unit_tests.py --parallel 4
```

### Advanced Commands
```bash
# Run only failed tests from last run
pytest --lf

# Run tests that match expression
pytest -k "test_user"

# Run with specific markers
pytest -m "not slow"

# Generate detailed coverage report
pytest --cov=src --cov-report=html --cov-report=term

# Profile test performance
pytest --durations=10
```

---

## 📈 Metrics & Reporting

### Key Metrics to Track
1. **Code Coverage**: Line, branch, function coverage
2. **Test Count**: Number of tests per module
3. **Test Execution Time**: Performance monitoring
4. **Test Success Rate**: Pass/fail ratios
5. **Bug Detection**: Issues found through testing

### Sample Coverage Report
```
Name                                    Stmts   Miss  Cover   Missing
-------------------------------------------------------------------
src/domain/models/user.py                  15      2    87%   45-46
src/domain/models/recipe.py                52      8    85%   23, 67-74
src/application/use_cases/recipes/save.py  25      3    88%   89-91
-------------------------------------------------------------------
TOTAL                                     387     45    88%
```

### HTML Coverage Reports
- Generated in `htmlcov/index.html`
- Interactive line-by-line coverage
- Missing line highlighting
- Module coverage breakdown

---

## 🎯 For Thesis Documentation

### Include in Your Thesis:
1. **Testing Strategy**: Methodology and approach
2. **Coverage Metrics**: Before/after comparison
3. **Test Case Examples**: Representative test cases
4. **Bug Discovery**: Issues found through testing
5. **Quality Improvement**: Code quality metrics

### Sample Thesis Sections:
```markdown
## Testing Methodology
The testing approach follows the Test Pyramid strategy:
- Unit Tests (85%+ coverage): 150+ test cases
- Integration Tests: 25+ test cases  
- Functional Tests: 15+ test cases

## Quality Metrics
- Code Coverage: 88% (target: 85%)
- Test Success Rate: 98%
- Bug Detection: 23 issues found and fixed
- Performance: Average test execution < 2 minutes
```

---

## 🐛 Troubleshooting

### Common Issues

**Import Errors**:
```bash
# Fix Python path issues
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or use pytest with proper path
pytest --rootdir=.
```

**Coverage Not Working**:
```bash
# Install coverage plugin
pip install pytest-cov

# Run with explicit coverage
pytest --cov=src --cov-report=term-missing
```

**Slow Tests**:
```bash
# Run in parallel
pytest -n 4

# Identify slow tests
pytest --durations=10
```

**Mock Issues**:
```bash
# Install pytest-mock
pip install pytest-mock

# Use proper patching
@patch('full.module.path.to.function')
```

---

## 📚 Next Steps

1. **Run Validation**: `python validate_unit_tests.py`
2. **Install Dependencies**: `pip install -r requirements-test.txt`
3. **Run Tests**: `python run_unit_tests.py`
4. **Check Coverage**: `python run_unit_tests.py --html`
5. **Expand Tests**: Add more test cases based on your specific needs
6. **Integrate CI/CD**: Add to your deployment pipeline

---

**🎓 This testing framework is designed to meet thesis-level requirements with enterprise-grade testing practices and comprehensive coverage reporting.**