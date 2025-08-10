# ZeroWasteAI Backend API Reference

A concise reference of all API endpoints, auth, status checks, and performance features (Redis caching and rate limiting). The running application exposes Swagger UI at `/apidocs` with live examples and schemas.

- Base URL: `http://<host>:3000`
- API Prefix: `/api`
- Swagger UI: `/apidocs`
- Health/Status: `/status`

## Quick Start

- Local (Python): `FLASK_APP=src/main.py flask run -p 3000`
- Docker: `docker-compose up --build`
- Check status: `curl http://localhost:3000/status`


## API Status

- `GET /status`
  - Checks DB connectivity (`SELECT 1`), lists known SQLAlchemy tables, reports table counts for key auth/profile tables, and reports security features status.
  - Example response keys:
    - `status`: `success` or `error`
    - `database_info`: `host`, `port`, `name`, `user`
    - `known_tables`: array of table names
    - `table_status`: per-table existence and record counts
    - `security_status`: JWT, token blacklisting, security headers, Firebase integration


## Authentication

All protected endpoints require a Bearer Access Token from this flow.

- `POST /api/auth/firebase-signin`
  - Header: `Authorization: Bearer <Firebase_ID_Token>`
  - Validates Firebase token, creates/updates user and profile, returns internal JWT tokens.
  - Response: `{ user, tokens: { access_token, refresh_token, token_type, expires_in }, profile_synced }`

- `POST /api/auth/refresh`
  - Header: `Authorization: Bearer <Refresh_Token>`
  - Requires JWT refresh token; rotates tokens and invalidates prior refresh token.
  - Response: `{ access_token, refresh_token, ... }`

- `POST /api/auth/logout`
  - Header: `Authorization: Bearer <Access_Token>`
  - Invalidates current access token and all refresh tokens for the user.

- `GET /api/auth/firebase-debug` (dev only)
  - Returns Firebase admin configuration and credential checks for debugging.

Security notes:
- JWT callbacks enforce token blacklisting, expiration handling, and missing/invalid token responses.
- Token models: `token_blacklist`, `refresh_token_tracking`.


## User

- `GET /api/user/profile` (auth)
  - Returns the current user profile.

- `PUT /api/user/profile` (auth)
  - Updates profile fields such as name, photo, preferences, etc.


## Inventory

Prefix: `/api/inventory`

- `POST /ingredients` (auth)
  - Batch add ingredients with fields: `name`, `quantity`, `type_unit`, `storage_type`, `expiration_time`, `time_unit`, plus optional `tips`, `image_path`, `expiration_date`.

- `GET /` (auth)
  - Returns full inventory (ingredients grouped into stacks and foods list).
  - Caching: cached per-user for ~5 min via `@cache_user_data('inventory_basic', timeout=300)`.

- `GET /complete` (auth)
  - Returns expanded inventory view with additional details.

- Update and delete operations (auth):
  - `PUT /ingredients/<ingredient_name>/<added_at>`
  - `DELETE /ingredients/<ingredient_name>/<added_at>`
  - `PATCH /ingredients/<ingredient_name>/<added_at>/quantity`
  - `POST /ingredients/<ingredient_name>/<added_at>/consume`
  - `DELETE /ingredients/<ingredient_name>` (delete all stacks for an ingredient)

- Foods operations (auth):
  - `POST /foods/from-recognition`
  - `PATCH /foods/<food_name>/<added_at>/quantity`
  - `POST /foods/<food_name>/<added_at>/consume`
  - `DELETE /foods/<food_name>/<added_at>`

- Listings and details (auth):
  - `GET /simple` — lightweight inventory
  - `GET /expiring` — expiring soon
  - `GET /ingredients/list`, `GET /foods/list`
  - `GET /ingredients/<ingredient_name>/detail`
  - `GET /foods/<food_name>/<added_at>/detail`

- Images (auth):
  - `POST /upload_image` — upload an inventory image
  - `POST /add_item` — add a single item

All inventory endpoints are rate-limited using the smart limiter; see Performance section.


## Recognition (AI)

Prefix: `/api/recognition`

- `POST /ingredients` — recognize ingredients from image(s)
- `POST /ingredients/complete` — detailed recognition results
- `POST /foods` — recognize foods
- `POST /batch` — batch recognition
- `POST /ingredients/async` — start async recognition task
- `GET /status/<task_id>` — async recognition status
- `GET /images/status/<task_id>` — image processing status
- `GET /recognition/<recognition_id>/images` — images for a recognition record

These endpoints are typically more restrictive in rate limits (costly operations).


## Recipes

Prefix: `/api/recipes`

- `POST /generate-from-inventory` (auth) — generate recipes from current inventory
- `POST /generate-custom` (auth) — custom recipe generation
- `GET /saved` (auth) — saved recipes
- `GET /all` (auth) — all generated recipes for the user
- `DELETE /delete` (auth) — delete recipe
- `GET /generated/gallery` (auth) — generated recipes gallery
- `GET /default` — default recipe list
- Favorites (auth):
  - `POST /generated/<recipe_uid>/favorite`
  - `DELETE /generated/<recipe_uid>/favorite`
  - `PUT /generated/<recipe_uid>/favorite`
- `GET /generated/favorites` (auth) — list favorites


## Planning

Prefix: `/api/planning`

- `POST /save` — save meal plan
- `PUT /update` — update meal plan
- `DELETE /delete` — delete plan
- `GET /get` — get plan by ID/criteria
- `GET /all` — list user plans
- `GET /dates` — list planned dates
- `POST /images/update` — update plan images


## Image Management

Prefix: `/api/image_management`

- `POST /assign_image` — assign a reference image
- `POST /search_similar_images` — find similar images
- `POST /sync_images` — sync images repository/index
- `POST /upload_image` — upload a reference image


## Generation

Prefix: `/api/generation`

- `GET /images/status/<task_id>` — async generation status
- `GET /<generation_id>/images` — images generated for an ID


## Environmental Savings

Prefix: `/api/environmental_savings`

- `POST /calculate/from-title` — compute impact from a recipe title
- `POST /calculate/from-uid/<recipe_uid>` — compute from a recipe UID
- `GET /calculations` — list past calculations
- `GET /calculations/status` — status of calculations
- `GET /summary` — user summary (often good candidate for caching)


## Admin (Internal Only)

Prefix: `/api/admin`

- `POST /cleanup-tokens`
  - Header: `X-Internal-Secret: <INTERNAL_SECRET_KEY>`
  - Cleans up expired tokens from blacklist and tracking.

- `GET /security-stats`
  - Header: `X-Internal-Secret: <INTERNAL_SECRET_KEY>`
  - Returns counts for blacklisted and refresh tokens.


## Performance (Redis, Caching, Rate Limiting)

This API integrates Redis for both caching and rate limiting. Configuration lives in `src/config/optimization_config.py` and is initialized in `src/main.py`.

- Environment variable: `REDIS_URL` (e.g., `redis://localhost:6379/0`).
  - Docker Compose sets `REDIS_URL=redis://redis:6379/0` and provides a `redis` service.

### Caching (Flask-Caching)

- Initialization: `cache_service.init_app(app)` creates a Redis-backed cache using `OptimizationConfig.get_cache_config()`.
- Health check: on startup it sets/gets a key; on failure it logs a warning and falls back to in-memory `simple` cache.
- Decorators:
  - `@smart_cache(cache_type, timeout=None, key_suffix=None)`: caches expensive function results; key based on function + args.
  - `@cache_user_data(cache_type, timeout=None)`: caches results per authenticated user (pulls user UID from JWT).
- Example in code: `GET /api/inventory` uses `@cache_user_data('inventory_basic', timeout=300)`.
- Defaults and timeouts (`OptimizationConfig`):
  - `CACHE_DEFAULT_TIMEOUT`: 300s
  - AI results: `ai_recognition_result: 7200`, `ai_environmental_impact: 3600`, `ai_utilization_ideas: 1800`
  - Inventory: `inventory_complete: 600`, `inventory_basic: 300`, `expiring_items: 900`
  - Planning: `meal_plans: 300`, `meal_plan_dates: 600`
  - Calculations/Search: `environmental_*: 1800–3600`, `search_results: 900`
- Key patterns: `zerowasteai:` prefix plus templates like:
  - `inventory:user:{user_id}:basic`
  - `inventory:user:{user_id}:complete`
  - `environmental:user:{user_id}:summary`
  - `planning:user:{user_id}:date:{date}`

### Rate Limiting (Flask-Limiter)

- Initialization: `rate_limiter.init_app(app)` with Redis storage (disabled in `testing` or `development`).
- Default limit: `RATELIMIT_DEFAULT="1000 per hour"`.
- Per-endpoint categories (examples):
  - AI: `ai_recognition: "5 per minute"`, `ai_environmental: "10 per minute"`, `ai_recipe_generation: "8 per minute"`, `ai_inventory_complete: "3 per minute"`
  - Inventory: `inventory_crud: "50 per minute"`, `inventory_bulk: "10 per minute"`
  - Planning: `planning_crud: "30 per minute"`
  - Auth: `auth_login: "10 per minute"`, `auth_signup: "5 per minute"`, `auth_sensitive: "3 per minute"`
  - Data: `data_read: "100 per minute"`, `data_write: "40 per minute"`
- Usage: endpoints can use `@smart_rate_limit('<category>')` to apply the configured limit.
- Additional in-repo limiter: `src/infrastructure/security/rate_limiter.py` provides in-memory decorators such as `@api_rate_limit` and is used for some admin/auth routes.


## Configuration

Main config: `src/config/config.py` (loaded from `.env`):

- JWT:
  - `JWT_SECRET_KEY`
  - `JWT_ACCESS_TOKEN_EXPIRES` (30 min), `JWT_REFRESH_TOKEN_EXPIRES` (30 days)
- Database (MySQL via SQLAlchemy): `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASS`
  - Pool tuning: `pool_size`, `max_overflow`, `pool_timeout`, `pool_recycle`, `pool_pre_ping`
- Firebase: `FIREBASE_CREDENTIALS_PATH`, `FIREBASE_STORAGE_BUCKET`
- Internal ops: `INTERNAL_SECRET_KEY` (header required by admin routes)
- Optimization: `REDIS_URL` (used by both cache and limiter)

Docker Compose (`docker-compose.yml`) provisions:
- `redis` on `6379` with `allkeys-lru` eviction
- `mysql` on `3306` with database/user/password
- `backend` service exposing port `3000`, with env wired to Redis/MySQL/Firebase


## Swagger and Examples

Every controller includes Flasgger `@swag_from` annotations with request schemas and example responses. Visit `/apidocs` for a live, browsable spec. For programmatic access, you can export the Swagger JSON from that UI.


## Notes and Tips

- Health: use `GET /status` to verify DB and security stack wiring.
- Dev vs Prod:
  - Rate limiting is disabled automatically in `testing`/`development`.
  - Caching is disabled when `TESTING=True`.
- Redis fallback: if Redis is unreachable, caching falls back to in-memory; rate limiting still runs if initialized against Redis.
- Security headers: automatically applied to all responses (HSTS, CSP, XSS/XFO protections).

