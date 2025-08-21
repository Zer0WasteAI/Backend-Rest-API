import json
import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"
CTRL_DIR = SRC_DIR / "interface" / "controllers"
MAIN_FILE = SRC_DIR / "main.py"


def parse_blueprint_prefixes(main_py: Path):
    text = main_py.read_text(encoding="utf-8", errors="ignore")
    # Matches: application.register_blueprint(auth_bp, url_prefix='/api/auth')
    pattern = re.compile(r"register_blueprint\((\w+),\s*url_prefix=['\"]([^'\"]+)['\"]\)")
    mapping = {}
    for m in pattern.finditer(text):
        bp_var, prefix = m.groups()
        mapping[bp_var] = prefix
    return mapping


def find_routes(controller_path: Path, bp_vars):
    text = controller_path.read_text(encoding="utf-8", errors="ignore")
    routes = []
    # Pattern like: @inventory_bp.route("/path", methods=["GET","POST"]) or methods=['GET']
    route_re = re.compile(
        r"@(?P<bp>\w+?)\.route\(\s*['\"](?P<path>[^'\"]*)['\"]\s*,\s*methods\s*=\s*\[(?P<methods>[^\]]+)\]\s*\)",
        re.MULTILINE,
    )
    for m in route_re.finditer(text):
        bp = m.group("bp")
        if bp not in bp_vars:
            continue
        route_path = m.group("path")
        methods_raw = m.group("methods")
        methods = [mm.strip().strip("'\"") for mm in methods_raw.split(",") if mm.strip()]
        routes.append({"bp": bp, "path": route_path, "methods": methods})
    return routes


def build_postman_items(group_name, base_prefix, routes):
    # Create a folder with requests for each route
    items = []

    # Curated examples for common endpoints
    example_bodies = {
        f"{base_prefix}/ingredients": {
            "POST": {
                "ingredients": [
                    {
                        "name": "Tomates cherry",
                        "quantity": 500,
                        "type_unit": "gr",
                        "storage_type": "refrigerador",
                        "expiration_time": 5,
                        "time_unit": "Días",
                        "tips": "Mantener refrigerados para mayor duración",
                        "image_path": "https://storage.googleapis.com/bucket/tomates.jpg"
                    },
                    {
                        "name": "Arroz integral",
                        "quantity": 1,
                        "type_unit": "kg",
                        "storage_type": "despensa",
                        "expiration_time": 6,
                        "time_unit": "Meses",
                        "tips": "Almacenar en recipiente hermético",
                        "image_path": "https://storage.googleapis.com/bucket/arroz.jpg"
                    }
                ]
            }
        },

        "/api/inventory/add_item": {
            "POST": {
                "name": "Leche",
                "quantity": 1,
                "unit": "litros",
                "storage_type": "refrigerador",
                "category": "ingredient",
                "image_url": "https://example.com/leche.jpg"
            }
        },

        "/api/recognition/ingredients": {
            "POST": {"images_paths": ["uploads/recognition/example1.jpg"]}
        },

        "/api/recognition/ingredients/complete": {
            "POST": {"images_paths": ["uploads/recognition/example1.jpg", "uploads/recognition/example2.jpg"]}
        },

        "/api/recognition/ingredients/async": {
            "POST": {"images_paths": ["uploads/recognition/example1.jpg"]}
        },

        "/api/recognition/foods": {
            "POST": {"images_paths": ["uploads/recognition/food1.jpg"]}
        },

        "/api/recognition/batch": {
            "POST": {
                "images_paths": [
                    "uploads/recognition/batch1.jpg",
                    "uploads/recognition/batch2.jpg",
                    "uploads/recognition/batch3.jpg"
                ]
            }
        },

        "/api/recipes/generate-custom": {
            "POST": {
                "ingredients": [
                    {"name": "Pollo", "quantity": 500, "unit": "gr"},
                    {"name": "Pasta", "quantity": 300, "unit": "gr"},
                    {"name": "Tomates", "quantity": 400, "unit": "gr"}
                ],
                "cuisine_type": "italiana",
                "difficulty": "intermedio",
                "prep_time": "medio",
                "dietary_restrictions": [],
                "meal_type": "almuerzo",
                "servings": 4
            }
        },

        "/api/planning/save": {
            "POST": {
                "date": "2024-01-20",
                "meals": {
                    "breakfast": {
                        "name": "Avena con frutas",
                        "description": "Desayuno nutritivo",
                        "ingredients": ["Avena", "Plátano", "Miel", "Leche"],
                        "prep_time_minutes": 10
                    }
                }
            }
        },

        "/api/environmental_savings/calculate/from-title": {
            "POST": {"title": "Ensalada de Tomates Cherry con Queso Manchego"}
        },

        "/api/image_management/upload_image": {
            "POST": {
                "__formdata__": [
                    {"key": "image", "type": "file", "src": "/path/to/image.jpg"},
                    {"key": "item_name", "type": "text", "value": "banana"},
                    {"key": "image_type", "type": "text", "value": "default"}
                ]
            }
        },

        "/api/inventory/upload_image": {
            "POST": {
                "__formdata__": [
                    {"key": "image", "type": "file", "src": "/path/to/inventory.jpg"},
                    {"key": "upload_type", "type": "text", "value": "ingredient"},
                    {"key": "item_name", "type": "text", "value": "Tomates cherry"}
                ]
            }
        },

        "/api/image_management/assign_image": {
            "POST": {"item_name": "tomate cherry"}
        },
        "/api/image_management/search_similar_images": {
            "POST": {"item_name": "manzana"}
        },

        "/api/cooking_session/start": {
            "POST": {
                "__headers__": [
                    {"key": "Idempotency-Key", "value": "{{idempotency_key}}", "type": "text"}
                ],
                "recipe_uid": "rec_abc123",
                "servings": 2,
                "level": "beginner",
                "started_at": "2024-01-20T10:00:00Z"
            }
        },

        "/api/recipes/delete": {
            "DELETE": {"title": "Pasta carbonara casera"}
        },
        "/api/recipes/generated/<recipe_uid>/favorite": {
            "POST": {"rating": 4, "notes": "Muy buena, añadir más especias"},
            "PUT": {"rating": 5, "notes": "Excelente! Un poco más de ajo"}
        },

        "/api/user/profile": {
            "PUT": {
                "displayName": "Carlos Primo",
                "language": "es",
                "cookingLevel": "intermediate",
                "measurementUnit": "metric",
                "allergies": [],
                "preferredFoodTypes": ["mediterránea"],
                "specialDietItems": []
            }
        },

        "/api/inventory/ingredients/<ingredient_name>/<added_at>/quantity": {
            "PATCH": {"quantity": 750}
        },
        "/api/inventory/foods/<food_name>/<added_at>/quantity": {
            "PATCH": {"quantity": 2}
        },
        "/api/inventory/ingredients/<ingredient_name>/<added_at>/consume": {
            "POST": {"consumed_quantity": 100}
        },
        "/api/inventory/foods/<food_name>/<added_at>/consume": {
            "POST": {"consumed_portions": 1}
        },
    }

    # Specific path patterns needing example path values
    path_examples = {
        "<ingredient_name>": "Tomates cherry",
        "<food_name>": "Pizza casera",
        "<added_at>": "2024-01-15T10:00:00Z",
        "<recipe_uid>": "rec_abc123",
        "<task_id>": "task_12345",
        "<generation_id>": "gen_abc123",
        "<recognition_id>": "rec_abc123",
    }

    for r in routes:
        for method in r["methods"]:
            # Initialize request skeleton
            req = {
                "name": f"{method} {r['path']}",
                "request": {
                    "method": method,
                    "header": [
                        {"key": "Content-Type", "value": "application/json"},
                        {"key": "Authorization", "value": "Bearer {{jwt}}", "type": "text"},
                    ],
                    "url": {
                        "raw": f"{{{{base_url}}}}{base_prefix}{r['path']}",
                        "host": ["{{base_url}}"],
                        "path": [],
                    },
                },
            }

            # Admin endpoints require internal secret header
            if group_name == "Admin":
                req["request"]["header"].append({
                    "key": "X-Internal-Secret",
                    "value": "{{internal_secret}}",
                    "type": "text",
                })

            # Build path segments and expand Flask params with examples
            path_no_proto = base_prefix + r['path']
            raw_path = path_no_proto
            for token, sample in path_examples.items():
                if token in raw_path:
                    raw_path = raw_path.replace(token, sample)
            req["request"]["url"]["raw"] = f"{{{{base_url}}}}/{raw_path.lstrip('/')}"
            req["request"]["url"]["path"] = [seg for seg in raw_path.lstrip('/').split('/') if seg]

            # Default empty JSON body for write methods
            if method in {"POST", "PUT", "PATCH"}:
                req["request"]["body"] = {
                    "mode": "raw",
                    "raw": "{}",
                    "options": {"raw": {"language": "json"}},
                }

            # Attach curated examples if available for this absolute path
            absolute_path = base_prefix + r['path']
            ex = example_bodies.get(absolute_path)
            if ex and method in ex:
                data = ex[method]
                # Add extra headers if specified
                if isinstance(data, dict) and "__headers__" in data:
                    req["request"]["header"].extend(data["__headers__"])  # type: ignore
                # Multipart formdata handling
                if isinstance(data, dict) and "__formdata__" in data:
                    req["request"]["body"] = {
                        "mode": "formdata",
                        "formdata": data["__formdata__"],
                    }
                    # Remove JSON content-type to let Postman set multipart boundary
                    req["request"]["header"] = [h for h in req["request"]["header"] if h["key"].lower() != "content-type"]
                else:
                    # JSON body
                    data_json = {k: v for k, v in data.items() if k != "__headers__"}
                    req["request"]["body"] = {
                        "mode": "raw",
                        "raw": json.dumps(data_json, ensure_ascii=False, indent=2),
                        "options": {"raw": {"language": "json"}},
                    }

            # Add query param examples for specific GETs
            if method == "GET" and "/cooking_session/" in absolute_path and absolute_path.endswith("/mise_en_place"):
                req["request"]["url"]["query"] = [{"key": "servings", "value": "2"}]

            # Planning get by date
            if method == "GET" and req["request"]["url"]["raw"].endswith("/api/planning/get"):
                req["request"]["url"]["query"] = [{"key": "date", "value": "2024-01-20"}]
            # Recipes favorites list sorting
            if method == "GET" and req["request"]["url"]["raw"].endswith("/api/recipes/generated/favorites"):
                req["request"]["url"]["query"] = [{"key": "sort_by", "value": "favorited_at"}]
            # Recipes all: show favorites_only false as example
            if method == "GET" and req["request"]["url"]["raw"].endswith("/api/recipes/all"):
                req["request"]["url"]["query"] = [{"key": "favorites_only", "value": "false"}]
            # Inventory expiring endpoints: add days=7
            if method == "GET" and (req["request"]["url"]["raw"].endswith("/api/inventory/expiring_soon") or req["request"]["url"]["raw"].endswith("/api/inventory/expiring")):
                req["request"]["url"]["query"] = [{"key": "days", "value": "7"}]

            # Header overrides for specific endpoints
            raw_url = req["request"]["url"]["raw"]
            # Auth firebase-signin uses Firebase ID token instead of API JWT
            if raw_url.endswith("/api/auth/firebase-signin"):
                # Replace Authorization value
                for h in req["request"]["header"]:
                    if h["key"].lower() == "authorization":
                        h["value"] = "Bearer {{firebase_id_token}}"
            # Guest login does not require Authorization
            if raw_url.endswith("/api/auth/guest-login"):
                req["request"]["header"] = [h for h in req["request"]["header"] if h["key"].lower() != "authorization"]

            items.append(req)

    return {"name": group_name, "item": items}


def load_env_defaults():
    env_path = BASE_DIR / ".env"
    defaults = {"internal_secret": "", "base_url": "http://localhost:3000", "jwt": ""}
    if env_path.exists():
        try:
            for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                if not line or line.strip().startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("\r")
                    if k == "INTERNAL_SECRET_KEY":
                        defaults["internal_secret"] = v
                    if k == "PORT":
                        # Respect custom port
                        try:
                            port = int(v)
                            defaults["base_url"] = f"http://localhost:{port}"
                        except ValueError:
                            pass
        except Exception:
            pass
    return defaults


def create_collection(name, groups):
    defaults = load_env_defaults()
    return {
        "info": {
            "name": name,
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "item": groups,
        "variable": [
            {"key": "base_url", "value": defaults["base_url"]},
            {"key": "jwt", "value": defaults["jwt"]},
            {"key": "internal_secret", "value": defaults["internal_secret"]},
            {"key": "idempotency_key", "value": "00000000-0000-4000-8000-000000000001"},
            {"key": "firebase_id_token", "value": ""},
            {"key": "recipe_uid", "value": "rec_abc123"},
        ],
    }


def build_flows_group():
    def headers(auth=True, json_ct=True, extra=None):
        hs = []
        if json_ct:
            hs.append({"key": "Content-Type", "value": "application/json"})
        if auth:
            hs.append({"key": "Authorization", "value": "Bearer {{jwt}}", "type": "text"})
        if extra:
            hs.extend(extra)
        return hs

    def url(path):
        p = path.lstrip('/')
        return {
            "raw": f"{{{{base_url}}}}/{p}",
            "host": ["{{base_url}}"],
            "path": p.split('/')
        }

    def raw_body(obj):
        return {
            "mode": "raw",
            "raw": json.dumps(obj, ensure_ascii=False, indent=2),
            "options": {"raw": {"language": "json"}},
        }

    # Test scripts to set variables
    test_set_jwt = {
        "listen": "test",
        "script": {
            "type": "text/javascript",
            "exec": [
                "const json = pm.response.json ? pm.response.json() : {};",
                "const token = json.access_token || (json.tokens && json.tokens.access_token) || (json.data && json.data.access_token);",
                "if (token) { pm.environment.set('jwt', token); pm.test('JWT saved to environment', () => true); } else { pm.test('JWT not found in response', () => false); }",
            ],
        },
    }

    test_set_recognition = {
        "listen": "test",
        "script": {
            "type": "text/javascript",
            "exec": [
                "const json = pm.response.json ? pm.response.json() : {};",
                "if (json.ingredients) { pm.environment.set('recognized_ingredients', JSON.stringify(json.ingredients)); }",
                "if (json.recognition_id) { pm.environment.set('recognition_id', json.recognition_id); }",
                "pm.test('Recognition vars stored', () => true);",
            ],
        },
    }

    test_set_recognition_async = {
        "listen": "test",
        "script": {
            "type": "text/javascript",
            "exec": [
                "const json = pm.response.json ? pm.response.json() : {};",
                "const tid = json.task_id || (json.images && json.images.task_id);",
                "if (tid) { pm.environment.set('recognition_task_id', tid); }",
                "pm.test('recognition_task_id stored', () => Boolean(tid));",
            ],
        },
    }

    test_set_generation = {
        "listen": "test",
        "script": {
            "type": "text/javascript",
            "exec": [
                "const json = pm.response.json ? pm.response.json() : {};",
                "const imgTask = (json.images && json.images.task_id) || (json.images && json.images.check_images_url && json.images.check_images_url.split('/').pop());",
                "if (imgTask) pm.environment.set('generation_task_id', imgTask);",
                "if (json.generation_id) pm.environment.set('generation_id', json.generation_id);",
                "pm.test('Generation vars captured', () => true);",
            ],
        },
    }

    test_set_inventory_vars = {
        "listen": "test",
        "script": {
            "type": "text/javascript",
            "exec": [
                "try {",
                "  const json = pm.response.json();",
                "  // Try common shapes: ingredients list",
                "  const ing = (json.ingredients && (json.ingredients[0] || (json.ingredients.items && json.ingredients.items[0]))) || json.items && json.items[0];",
                "  if (ing && (ing.name || ing.ingredient_name)) {",
                "    const name = ing.name || ing.ingredient_name; pm.environment.set('ingredient_name', name);",
                "    let addedAt = ing.added_at || (ing.stacks && ing.stacks[0] && (ing.stacks[0].added_at || ing.stacks[0].addedAt));",
                "    if (addedAt) pm.environment.set('added_at', addedAt);",
                "  }",
                "  pm.test('Inventory vars attempted', () => true);",
                "} catch(e) { pm.test('Inventory vars parse failed', () => false); }",
            ],
        },
    }

    test_set_session = {
        "listen": "test",
        "script": {
            "type": "text/javascript",
            "exec": [
                "const json = pm.response.json ? pm.response.json() : {};",
                "if (json.session_id) pm.environment.set('session_id', json.session_id);",
                "pm.test('session_id stored', () => Boolean(pm.environment.get('session_id')));",
            ],
        },
    }

    # Capture uploaded paths (works for both general and inventory responses)
    test_capture_upload_paths = {
        "listen": "test",
        "script": {
            "type": "text/javascript",
            "exec": [
                "let json = {}; try { json = pm.response.json(); } catch(e) {}",
                "let sp = json?.image?.storage_path || json?.upload_info?.storage_path;",
                "let pu = json?.image?.image_path || json?.upload_info?.public_url;",
                "if (!pm.environment.get('uploaded_storage_path_1')) { pm.environment.set('uploaded_storage_path_1', sp || ''); pm.environment.set('uploaded_public_url_1', pu || ''); }",
                "else if (!pm.environment.get('uploaded_storage_path_2')) { pm.environment.set('uploaded_storage_path_2', sp || ''); pm.environment.set('uploaded_public_url_2', pu || ''); }",
                "pm.test('Captured upload paths', () => Boolean(sp || pu));",
            ],
        },
    }

    flows = {
        "name": "Flows",
        "item": [
            {
                "name": "Quickstart: Guest Auth → Basic Ops",
                "item": [
                    {
                        "name": "Auth: Guest Login (save JWT)",
                        "request": {
                            "method": "POST",
                            "header": headers(auth=False),
                            "url": url("api/auth/guest-login"),
                            "body": raw_body({"email": "guest@test.com", "name": "Usuario Invitado"}),
                        },
                        "event": [test_set_jwt],
                    },
                    {
                        "name": "Upload Image 1 (general)",
                        "request": {
                            "method": "POST",
                            "header": headers(json_ct=False),
                            "url": url("api/image_management/upload_image"),
                            "body": {"mode": "formdata", "formdata": [
                                {"key": "image", "type": "file", "src": "/path/to/image1.jpg"},
                                {"key": "item_name", "type": "text", "value": "tomates"},
                                {"key": "image_type", "type": "text", "value": "ingredient"}
                            ]},
                        },
                        "event": [test_capture_upload_paths],
                    },
                    {
                        "name": "Upload Image 2 (general)",
                        "request": {
                            "method": "POST",
                            "header": headers(json_ct=False),
                            "url": url("api/image_management/upload_image"),
                            "body": {"mode": "formdata", "formdata": [
                                {"key": "image", "type": "file", "src": "/path/to/image2.jpg"},
                                {"key": "item_name", "type": "text", "value": "arroz"},
                                {"key": "image_type", "type": "text", "value": "ingredient"}
                            ]},
                        },
                        "event": [test_capture_upload_paths],
                    },
                    {
                        "name": "User: Get Profile",
                        "request": {"method": "GET", "header": headers(), "url": url("api/user/profile")},
                    },
                    {
                        "name": "User: Update Profile",
                        "request": {"method": "PUT", "header": headers(), "url": url("api/user/profile"), "body": raw_body({
                            "displayName": "Usuario Invitado",
                            "language": "es",
                            "cookingLevel": "beginner",
                            "measurementUnit": "metric"
                        })},
                    },
                    {
                        "name": "Inventory: Add Ingredients (batch)",
                        "request": {
                            "method": "POST",
                            "header": headers(),
                            "url": url("api/inventory/ingredients"),
                            "body": raw_body({
                                "ingredients": [
                                    {"name": "Tomates cherry", "quantity": 500, "type_unit": "gr", "storage_type": "refrigerador", "expiration_time": 5, "time_unit": "Días", "tips": "Mantener refrigerados para mayor duración", "image_path": "{{uploaded_public_url_1}}"},
                                    {"name": "Arroz integral", "quantity": 1, "type_unit": "kg", "storage_type": "despensa", "expiration_time": 6, "time_unit": "Meses", "tips": "Almacenar en recipiente hermético", "image_path": "{{uploaded_public_url_2}}"}
                                ]
                            }),
                        },
                    },
                    {
                        "name": "Inventory: Get Simple",
                        "request": {
                            "method": "GET",
                            "header": headers(),
                            "url": url("api/inventory/simple"),
                        },
                    },
                    {
                        "name": "Recipes: Generate Custom",
                        "request": {
                            "method": "POST",
                            "header": headers(),
                            "url": url("api/recipes/generate-custom"),
                            "body": raw_body({
                                "ingredients": [
                                    {"name": "Pollo", "quantity": 500, "unit": "gr"},
                                    {"name": "Pasta", "quantity": 300, "unit": "gr"},
                                    {"name": "Tomates", "quantity": 400, "unit": "gr"}
                                ],
                                "cuisine_type": "italiana",
                                "difficulty": "intermedio",
                                "prep_time": "medio",
                                "dietary_restrictions": [],
                                "meal_type": "almuerzo",
                                "servings": 4
                            }),
                        },
                    },
                    {
                        "name": "Environmental: Calculate from Title",
                        "request": {
                            "method": "POST",
                            "header": headers(),
                            "url": url("api/environmental_savings/calculate/from-title"),
                            "body": raw_body({"title": "Ensalada de Tomates Cherry con Queso Manchego"}),
                        },
                    },
                ],
            },
            {
                "name": "Flow: Recognition → Inventory",
                "item": [
                    {
                        "name": "Upload Image A for Recognition",
                        "request": {"method": "POST", "header": headers(json_ct=False), "url": url("api/image_management/upload_image"), "body": {"mode":"formdata", "formdata": [
                            {"key":"image","type":"file","src":"/path/to/rec1.jpg"},
                            {"key":"item_name","type":"text","value":"ingrediente A"},
                            {"key":"image_type","type":"text","value":"ingredient"}
                        ]}},
                        "event": [test_capture_upload_paths],
                    },
                    {
                        "name": "Upload Image B for Recognition",
                        "request": {"method": "POST", "header": headers(json_ct=False), "url": url("api/image_management/upload_image"), "body": {"mode":"formdata", "formdata": [
                            {"key":"image","type":"file","src":"/path/to/rec2.jpg"},
                            {"key":"item_name","type":"text","value":"ingrediente B"},
                            {"key":"image_type","type":"text","value":"ingredient"}
                        ]}},
                        "event": [test_capture_upload_paths],
                    },
                    {
                        "name": "Recognition: Ingredients (save vars)",
                        "request": {
                            "method": "POST",
                            "header": headers(),
                            "url": url("api/recognition/ingredients"),
                            "body": raw_body({"images_paths": ["{{uploaded_storage_path_1}}", "{{uploaded_storage_path_2}}"]}),
                        },
                        "event": [test_set_recognition],
                    },
                    {
                        "name": "Recognition: Ingredients Async (save task)",
                        "request": {"method": "POST", "header": headers(), "url": url("api/recognition/ingredients/async"), "body": raw_body({"images_paths": ["{{uploaded_storage_path_1}}"]})},
                        "event": [test_set_recognition_async],
                    },
                    {
                        "name": "Recognition: Status by Task",
                        "request": {"method": "GET", "header": headers(), "url": url("api/recognition/status/{{recognition_task_id}}")},
                    },
                    {
                        "name": "Recognition: Images Status by Task",
                        "request": {"method": "GET", "header": headers(), "url": url("api/recognition/images/status/{{recognition_task_id}}")},
                    },
                    {
                        "name": "Recognition: Images by Recognition ID",
                        "request": {"method": "GET", "header": headers(), "url": url("api/recognition/recognition/{{recognition_id}}/images")},
                    },
                    {
                        "name": "Inventory: Add from Recognition (uses {{recognized_ingredients}})",
                        "request": {
                            "method": "POST",
                            "header": headers(),
                            "url": url("api/inventory/ingredients/from-recognition"),
                            "body": {
                                "mode": "raw",
                                "raw": "{\n  \"ingredients\": {{recognized_ingredients}}\n}",
                                "options": {"raw": {"language": "json"}},
                            },
                        },
                    },
                ],
            },
            {
                "name": "Flow: Recipes Generation & Images",
                "item": [
                    {
                        "name": "Recipes: Generate from Inventory (capture generation vars)",
                        "request": {"method": "POST", "header": headers(), "url": url("api/recipes/generate-from-inventory")},
                        "event": [test_set_generation],
                    },
                    {
                        "name": "Generation: Images Status (by task)",
                        "request": {"method": "GET", "header": headers(), "url": url("api/generation/images/status/{{generation_task_id}}")},
                    },
                    {
                        "name": "Generation: Recipes with Images (by generation id)",
                        "request": {"method": "GET", "header": headers(), "url": url("api/generation/{{generation_id}}/images")},
                    },
                    {
                        "name": "Recipes: Gallery (generated)",
                        "request": {"method": "GET", "header": headers(), "url": url("api/recipes/generated/gallery")},
                    },
                    {
                        "name": "Recipes: All (favorites_only=false)",
                        "request": {"method": "GET", "header": headers(), "url": url("api/recipes/all"), "url": {"raw": "{{base_url}}/api/recipes/all?favorites_only=false", "host": ["{{base_url}}"], "path": ["api","recipes","all"], "query": [{"key":"favorites_only","value":"false"}]}},
                    },
                ],
            },
            {
                "name": "Flow: Favorites & Cooking",
                "item": [
                    {
                        "name": "Recipes: Add Favorite (recipe_uid={{recipe_uid}})",
                        "request": {
                            "method": "POST",
                            "header": headers(),
                            "url": url("api/recipes/generated/{{recipe_uid}}/favorite"),
                            "body": raw_body({"rating": 4, "notes": "Muy buena, añadir más especias"}),
                        },
                    },
                    {
                        "name": "Recipes: Update Favorite",
                        "request": {
                            "method": "PUT",
                            "header": headers(),
                            "url": url("api/recipes/generated/{{recipe_uid}}/favorite"),
                            "body": raw_body({"rating": 5, "notes": "Excelente! Un poco más de ajo"}),
                        },
                    },
                    {
                        "name": "Cooking: Start Session (Idempotency-Key)",
                        "request": {
                            "method": "POST",
                            "header": headers(extra=[{"key": "Idempotency-Key", "value": "{{idempotency_key}}", "type": "text"}]),
                            "url": url("api/cooking_session/start"),
                            "body": raw_body({
                                "recipe_uid": "{{recipe_uid}}",
                                "servings": 2,
                                "level": "beginner",
                                "started_at": "2024-01-20T10:00:00Z"
                            }),
                        },
                        "event": [test_set_session],
                    },
                    {
                        "name": "Cooking: Complete Step",
                        "request": {
                            "method": "POST",
                            "header": headers(extra=[{"key": "Idempotency-Key", "value": "{{idempotency_key}}", "type": "text"}]),
                            "url": url("api/cooking_session/complete_step"),
                            "body": raw_body({
                                "session_id": "{{session_id}}",
                                "step_id": "step-1",
                                "timer_ms": 300000,
                                "consumptions": []
                            }),
                        },
                    },
                    {
                        "name": "Cooking: Finish Session",
                        "request": {
                            "method": "POST",
                            "header": headers(extra=[{"key": "Idempotency-Key", "value": "{{idempotency_key}}", "type": "text"}]),
                            "url": url("api/cooking_session/finish"),
                            "body": raw_body({
                                "session_id": "{{session_id}}",
                                "notes": "Sesión de cocina de prueba",
                                "photo_url": ""
                            }),
                        },
                    },
                ],
            },
            {
                "name": "Flow: Image Uploads",
                "item": [
                    {
                        "name": "Image Management: Upload (multipart)",
                        "request": {
                            "method": "POST",
                            "header": headers(json_ct=False),
                            "url": url("api/image_management/upload_image"),
                            "body": {
                                "mode": "formdata",
                                "formdata": [
                                    {"key": "image", "type": "file", "src": "/path/to/image.jpg"},
                                    {"key": "item_name", "type": "text", "value": "banana"},
                                    {"key": "image_type", "type": "text", "value": "default"}
                                ],
                            },
                        },
                    },
                    {
                        "name": "Inventory: Upload Image (multipart)",
                        "request": {
                            "method": "POST",
                            "header": headers(json_ct=False),
                            "url": url("api/inventory/upload_image"),
                            "body": {
                                "mode": "formdata",
                                "formdata": [
                                    {"key": "image", "type": "file", "src": "/path/to/inventory.jpg"},
                                    {"key": "upload_type", "type": "text", "value": "ingredient"},
                                    {"key": "item_name", "type": "text", "value": "Tomates cherry"}
                                ],
                            },
                        },
                    },
                ],
            },
            {
                "name": "Flow: Inventory Upload → Add Item",
                "item": [
                    {
                        "name": "Inventory: Upload Image (ingredient)",
                        "request": {
                            "method": "POST",
                            "header": headers(json_ct=False),
                            "url": url("api/inventory/upload_image"),
                            "body": {"mode": "formdata", "formdata": [
                                {"key": "image", "type": "file", "src": "/path/to/ingredient.jpg"},
                                {"key": "upload_type", "type": "text", "value": "ingredient"},
                                {"key": "item_name", "type": "text", "value": "Tomates cherry"}
                            ]},
                        },
                        "event": [test_capture_upload_paths],
                    },
                    {
                        "name": "Inventory: Add Item (uses uploaded image)",
                        "request": {
                            "method": "POST",
                            "header": headers(),
                            "url": url("api/inventory/add_item"),
                            "body": raw_body({
                                "name": "Tomates cherry",
                                "quantity": 1,
                                "unit": "unidades",
                                "storage_type": "refrigerador",
                                "category": "ingredient",
                                "image_url": "{{uploaded_public_url_1}}"
                            }),
                        },
                    },
                ],
            },
            {
                "name": "Flow: Inventory Upload → Recognition",
                "item": [
                    {
                        "name": "Inventory: Upload Image (recognition)",
                        "request": {
                            "method": "POST",
                            "header": headers(json_ct=False),
                            "url": url("api/inventory/upload_image"),
                            "body": {"mode": "formdata", "formdata": [
                                {"key": "image", "type": "file", "src": "/path/to/recognition.jpg"},
                                {"key": "upload_type", "type": "text", "value": "recognition"},
                                {"key": "item_name", "type": "text", "value": "foto reconocimiento"}
                            ]},
                        },
                        "event": [test_capture_upload_paths],
                    },
                    {
                        "name": "Recognition: Ingredients (from inventory upload)",
                        "request": {"method": "POST", "header": headers(), "url": url("api/recognition/ingredients"), "body": raw_body({
                            "images_paths": ["{{uploaded_storage_path_1}}"]
                        })},
                        "event": [test_set_recognition],
                    },
                ],
            },
            {
                "name": "Flow: Inventory Advanced",
                "item": [
                    {
                        "name": "Inventory: Ingredients List (capture vars)",
                        "request": {"method": "GET", "header": headers(), "url": url("api/inventory/ingredients/list")},
                        "event": [test_set_inventory_vars],
                    },
                    {
                        "name": "Inventory: Ingredient Detail",
                        "request": {"method": "GET", "header": headers(), "url": url("api/inventory/ingredients/{{ingredient_name}}/detail")},
                    },
                    {
                        "name": "Inventory: Update Ingredient Quantity",
                        "request": {"method": "PATCH", "header": headers(), "url": url("api/inventory/ingredients/{{ingredient_name}}/{{added_at}}/quantity"), "body": raw_body({"quantity": 750})},
                    },
                    {
                        "name": "Inventory: Consume Ingredient",
                        "request": {"method": "POST", "header": headers(), "url": url("api/inventory/ingredients/{{ingredient_name}}/{{added_at}}/consume"), "body": raw_body({"consumed_quantity": 100})},
                    },
                    {
                        "name": "Inventory: Expiring Soon (days=7)",
                        "request": {"method": "GET", "header": headers(), "url": {"raw": "{{base_url}}/api/inventory/expiring_soon?days=7", "host":["{{base_url}}"], "path":["api","inventory","expiring_soon"], "query":[{"key":"days","value":"7"}]}},
                    },
                ],
            },
            {
                "name": "Flow: Planning CRUD",
                "item": [
                    {
                        "name": "Planning: Save",
                        "request": {"method": "POST", "header": headers(), "url": url("api/planning/save"), "body": raw_body({
                            "date": "2024-01-20",
                            "meals": {"breakfast": {"name": "Avena con frutas", "ingredients": ["Avena","Plátano"]}}
                        })},
                    },
                    {"name": "Planning: Get by date", "request": {"method": "GET", "header": headers(), "url": {"raw":"{{base_url}}/api/planning/get?date=2024-01-20","host":["{{base_url}}"],"path":["api","planning","get"],"query":[{"key":"date","value":"2024-01-20"}]}}},
                    {"name": "Planning: Update", "request": {"method": "PUT", "header": headers(), "url": url("api/planning/update"), "body": raw_body({
                        "date": "2024-01-20",
                        "meals": {"breakfast": {"name": "Avena + yogurt"}}
                    })}},
                    {"name": "Planning: All", "request": {"method": "GET", "header": headers(), "url": url("api/planning/all")}},
                    {"name": "Planning: Dates", "request": {"method": "GET", "header": headers(), "url": url("api/planning/dates")}},
                    {"name": "Planning: Delete", "request": {"method": "DELETE", "header": headers(), "url": url("api/planning/delete"), "body": raw_body({"date": "2024-01-20"})}},
                ],
            },
            {
                "name": "Flow: Environmental Extensive",
                "item": [
                    {"name": "Environmental: From Title", "request": {"method": "POST", "header": headers(), "url": url("api/environmental_savings/calculate/from-title"), "body": raw_body({"title": "Ensalada de Tomates Cherry con Queso Manchego"})}},
                    {"name": "Environmental: From UID", "request": {"method": "POST", "header": headers(), "url": url("api/environmental_savings/calculate/from-uid/{{recipe_uid}}")}},
                    {"name": "Environmental: Calculations", "request": {"method": "GET", "header": headers(), "url": url("api/environmental_savings/calculations")}},
                    {"name": "Environmental: Status", "request": {"method": "GET", "header": headers(), "url": url("api/environmental_savings/calculations/status")}},
                    {"name": "Environmental: Summary", "request": {"method": "GET", "header": headers(), "url": url("api/environmental_savings/summary")}},
                ],
            },
            {
                "name": "Flow: Admin (Internal Secret)",
                "item": [
                    {"name": "Admin: Cleanup Tokens", "request": {"method": "POST", "header": headers(extra=[{"key":"X-Internal-Secret","value":"{{internal_secret}}","type":"text"}]), "url": url("api/admin/cleanup-tokens")}},
                    {"name": "Admin: Security Stats", "request": {"method": "GET", "header": headers(extra=[{"key":"X-Internal-Secret","value":"{{internal_secret}}","type":"text"}]), "url": url("api/admin/security-stats")}},
                ],
            },
        ],
    }
    return flows


def main():
    bp_prefixes = parse_blueprint_prefixes(MAIN_FILE)
    # Map controller files to blueprint var names present in that file
    controller_files = sorted(CTRL_DIR.glob("*_controller.py"))
    groups_by_bp = {bp: [] for bp in bp_prefixes}

    for ctrl in controller_files:
        routes = find_routes(ctrl, set(bp_prefixes.keys()))
        for r in routes:
            groups_by_bp[r["bp"]].append(r)

    # Define folder display names and order
    bp_display = {
        "auth_bp": "Auth",
        "user_bp": "User",
        "admin_bp": "Admin",
        "recognition_bp": "Recognition",
        "image_management_bp": "Image Management",
        "inventory_bp": "Inventory",
        "recipes_bp": "Recipes",
        "planning_bp": "Planning",
        "generation_bp": "Generation",
        "environmental_savings_bp": "Environmental Savings",
        "cooking_session_bp": "Cooking Session",
    }

    order = [
        "Auth",
        "User",
        "Recognition",
        "Image Management",
        "Recipes",
        "Planning",
        "Generation",
        "Environmental Savings",
        "Cooking Session",
        "Admin",
        "Inventory",
    ]

    # Build Postman groups
    groups_all = []
    groups_part1 = []
    groups_inventory = []

    for bp_var, routes in groups_by_bp.items():
        if not routes:
            continue
        group_name = bp_display.get(bp_var, bp_var)
        prefix = bp_prefixes[bp_var]
        group = build_postman_items(group_name, prefix, routes)
        groups_all.append(group)
        if group_name == "Inventory":
            groups_inventory.append(group)
        else:
            groups_part1.append(group)

    # Sort by desired order
    def sort_groups(gs):
        order_map = {name: i for i, name in enumerate(order)}
        return sorted(gs, key=lambda g: order_map.get(g["name"], 999))

    groups_all = sort_groups(groups_all)
    groups_part1 = sort_groups(groups_part1)
    groups_inventory = sort_groups(groups_inventory)

    # Append flows group to the final collection
    final_groups = list(groups_all)
    final_groups.insert(0, build_flows_group())

    # Create collections
    part1 = create_collection("ZeroWasteAI API — Part 1 (Non-Inventory)", groups_part1)
    part2 = create_collection("ZeroWasteAI API — Part 2 (Inventory)", groups_inventory)
    final = create_collection("ZeroWasteAI — Complete", final_groups)

    # Write files
    out_part1 = BASE_DIR / "ZeroWasteAI_Complete_Postman_Collection_Part1.json"
    out_part2 = BASE_DIR / "ZeroWasteAI_Complete_Postman_Collection_Part2_Inventory.json"
    out_final = BASE_DIR / "ZeroWasteAI_Complete_Postman_Collection_FINAL.json"

    out_part1.write_text(json.dumps(part1, indent=2), encoding="utf-8")
    out_part2.write_text(json.dumps(part2, indent=2), encoding="utf-8")
    out_final.write_text(json.dumps(final, indent=2), encoding="utf-8")

    print("Generated:")
    print(f" - {out_part1}")
    print(f" - {out_part2}")
    print(f" - {out_final}")


if __name__ == "__main__":
    main()
