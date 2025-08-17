# ZeroWasteAI — Especificación de API (Backend) v1.3

**Objetivo:** habilitar *Modo Cocina* por niveles, **Mise en place**, consumos por paso, sobras, rescates por vencimiento y métricas ambientales con cambios mínimos sobre tu arquitectura (Flask + Clean Architecture).

> ⚠️ **NO OLVIDAR (clave para UI):** exponer `GET /recipes/{uid}/mise_en_place` para que la app muestre la **Mise en place** antes de iniciar el Modo Cocina.

---

## 0) Principios & Compatibilidad

* **Compatibilidad**: no romper endpoints existentes; añadir rutas nuevas bajo `/api`.
* **Atómico por paso**: cada *complete\_step* descuenta stock de **lote FEFO** en una transacción.
* **Idempotencia**: todas las mutaciones aceptan `Idempotency-Key` por header.
* **Versionado**: `X-Api-Version: 1.3`, deprecaciones con 2 versiones de gracia.
* **Auth**: JWT como hoy; roles `user`, `admin`.

---

## 1) Modelos de Dominio (JSON Schemas simplificados)

### 1.1 `IngredientBatch`

```json
{
  "id": "batch_123",
  "ingredient_uid": "ing_chicken_breast",
  "qty": 750.0, "unit": "g",
  "storage_location": "fridge",              // pantry|fridge|freezer
  "label_type": "use_by",                     // use_by|best_before
  "expiry_date": "2025-08-20",
  "state": "available",                       // available|reserved|in_cooking|leftover|frozen|expiring_soon|quarantine|expired
  "sealed": true,
  "created_at": "2025-08-10T12:30:00Z",
  "updated_at": "2025-08-16T23:15:00Z"
}
```

### 1.2 `CookingSession`

```json
{
  "session_id": "cook_9a1f",
  "recipe_uid": "rcp_aji_gallina_01",
  "servings": 3,
  "level": "beginner",                        // beginner|intermediate|advanced
  "started_at": "2025-08-16T23:25:00Z",
  "finished_at": null,
  "steps": [
    {
      "step_id": "S1",
      "status": "done|pending|skipped",
      "timer_ms": 120000,
      "consumptions": [
        {"ingredient_uid": "ing_onion", "lot_id": "batch_777", "qty": 80, "unit": "g"}
      ]
    }
  ],
  "notes": null,
  "photo_url": null
}
```

### 1.3 `StepConsumption`

```json
{"ingredient_uid":"ing_onion","lot_id":"batch_777","qty":80,"unit":"g"}
```

### 1.4 `LeftoverItem`

```json
{
  "leftover_id": "left_123",
  "recipe_uid": "rcp_aji_gallina_01",
  "title": "Ají de gallina (sobras)",
  "portions": 2,
  "eat_by": "2025-08-18",
  "storage_location": "fridge"
}
```

### 1.5 `WasteLog`

```json
{
  "waste_id":"w_88",
  "batch_id":"batch_123",
  "reason":"expired|bad_condition|other",
  "estimated_weight": 250.0,
  "unit":"g",
  "date":"2025-08-16"
}
```

### 1.6 `EnvironmentalSaving`

```json
{
  "co2e_kg": 0.42,
  "water_l": 120.0,
  "waste_kg": 0.18,
  "basis": "per_session",             // per_recipe_estimate|per_session
  "inputs": [{"ingredient_uid":"ing_chicken_breast","qty":320,"unit":"g"}]
}
```

---

## 2) Máquina de Estados (Batch)

* **available** → (reserve) → **reserved**
* **reserved** → (start cooking) → **in\_cooking**
* **in\_cooking** → (consume qty) → **available**|**leftover** (si llega a 0, se elimina o queda histórico)
* **available** → (freeze) → **frozen**
* **available**/**reserved** → (expiring job) → **expiring\_soon**
* **expiring\_soon**/**available** → (quarantine trigger tras fecha) → **quarantine**/**expired**
* **quarantine/expired** → (discard) → **removed** (histórico vía `WasteLog`)

---

## 3) Endpoints Nuevos/Actualizados

### 3.1 **Mise en place** (⚠️ imprescindible para la UI)

**GET** `/api/recipes/{recipe_uid}/mise_en_place?servings=3`
**200**

```json
{
  "recipe_uid":"rcp_aji_gallina_01",
  "servings":3,
  "tools":["olla mediana","sartén","cuchillo","tabla"],
  "preheat":[{"device":"stove","setting":"medium","duration_ms":60000}],
  "prep_tasks":[
    {"id":"mp1","text":"Picar 1/2 cebolla en cubos (80 g)","ingredient_uid":"ing_onion","suggested_qty":80,"unit":"g"},
    {"id":"mp2","text":"Deshilachar pollo cocido (320 g)","ingredient_uid":"ing_chicken_breast","suggested_qty":320,"unit":"g"}
  ],
  "measured_ingredients":[
    {"ingredient_uid":"ing_onion","qty":80,"unit":"g","lot_suggestion":"batch_777"},
    {"ingredient_uid":"ing_bread","qty":50,"unit":"g"}
  ]
}
```

> **Regla:** aquí **no** se descuenta stock; sólo **sugiere** lote FEFO.

---

### 3.2 **Cooking Session**

**POST** `/api/recipes/cooking_session/start`
Request

```json
{"recipe_uid":"rcp_aji_gallina_01","servings":3,"level":"beginner","started_at":"2025-08-16T23:25:00Z"}
```

**201**

```json
{"session_id":"cook_9a1f","status":"running"}
```

**POST** `/api/recipes/cooking_session/complete_step`
Request

```json
{
  "session_id":"cook_9a1f",
  "step_id":"S3",
  "timer_ms":120000,
  "consumptions":[
    {"ingredient_uid":"ing_onion","lot_id":"batch_777","qty":80,"unit":"g"},
    {"ingredient_uid":"ing_oil","lot_id":"batch_552","qty":10,"unit":"ml"}
  ]
}
```

**200**

```json
{"ok":true,"inventory_updates":[{"lot_id":"batch_777","new_qty":120},{"lot_id":"batch_552","new_qty":490}]}
```

**POST** `/api/recipes/cooking_session/finish`
Request

```json
{"session_id":"cook_9a1f","notes":"Quedó perfecto","photo_url":"https://.../cook_9a1f.jpg"}
```

**200**

```json
{
  "ok":true,
  "environmental_saving":{"co2e_kg":0.38,"water_l":95,"waste_kg":0.12},
  "leftover_suggestion":{"portions":2,"eat_by":"2025-08-18"}
}
```

---

### 3.3 **Sobras**

**POST** `/api/inventory/leftovers`
Request

```json
{"recipe_uid":"rcp_aji_gallina_01","title":"Ají de gallina (sobras)","portions":2,"eat_by":"2025-08-18","storage_location":"fridge"}
```

**201**

```json
{"leftover_id":"left_123","planner_suggestion":{"date":"2025-08-17","meal_type":"dinner"}}
```

---

### 3.4 **Rescate (a punto de vencer) y Cuarentena**

**GET** `/api/inventory/expiring_soon?withinDays=3&storage=fridge`
**200**

```json
[{"batch_id":"batch_321","ingredient_uid":"ing_spinach","expiry_date":"2025-08-17","urgency_score":0.92}]
```

**POST** `/api/inventory/batch/{batch_id}/reserve`

```json
{"planner_date":"2025-08-17","meal_type":"dinner"}
```

**POST** `/api/inventory/batch/{batch_id}/freeze`

```json
{"new_best_before":"2025-09-05"}
```

**POST** `/api/inventory/batch/{batch_id}/transform`

```json
{"output_type":"sofrito","yield_qty":250,"unit":"g","eat_by":"2025-08-20"}
```

**POST** `/api/inventory/batch/{batch_id}/quarantine`
`204 No Content`

**POST** `/api/inventory/batch/{batch_id}/discard`

```json
{"estimated_weight":180,"unit":"g","reason":"expired"}
```

**201**

```json
{"waste_id":"w_88","co2e_wasted_kg":0.11}
```

---

### 3.5 **Métricas ambientales**

**POST** `/api/environmental_savings/calculate/from-session`
Request

```json
{"session_id":"cook_9a1f","actual_consumptions":[{"ingredient_uid":"ing_chicken_breast","qty":320,"unit":"g"}]}
```

**200**

```json
{"co2e_kg":0.42,"water_l":120,"waste_kg":0.18,"basis":"per_session"}
```

**GET** `/api/environmental_savings/summary?period=week`
**200**

```json
{"period":"week","total":{"co2e_kg":2.9,"water_l":740,"waste_kg":1.1},"top_actions":["rescates","sobras_consumidas"]}
```

---

### 3.6 **Planner**

**POST** `/api/planner/add_meal_from_leftovers`

```json
{"leftover_id":"left_123","date":"2025-08-18","meal_type":"lunch"}
```

**201** `{ "planner_item_id":"plan_77" }`

---

## 4) Errores & Idempotencia

**Headers**:

* `Idempotency-Key: <uuid>` (requerido en POST).
* `X-Api-Version: 1.3`

**ErrorBody**

```json
{"error":"validation_error","message":"qty must be > 0","field":"consumptions[0].qty"}
```

**Códigos**: `400, 401, 403, 404, 409 (conflict de lote), 422 (regla FEFO), 500`.

---

## 5) Transacciones & Concurrencia

* `complete_step` ejecuta:

  1. lock por `lot_id` (SELECT … FOR UPDATE)
  2. valida `qty_available >= qty`
  3. descuenta, actualiza `state` si `qty==0`
  4. registra `ConsumptionLog(session_id, step_id, lot_id, qty)`
  5. *commit*
* Reintentos idempotentes: misma `Idempotency-Key` → devolver resultado previo.

---

## 6) Jobs & Reglas de vencimiento

* **Job diario (02:00 Lima)**:

  * marca `expiring_soon` si `expiry_date - now <= threshold(category)`
  * mueve a `quarantine/expired` si `now > expiry_date` (según `label_type`)
  * emite eventos `inventory.expiringSoon` / `inventory.expired`

---

## 7) Índices & Persistencia

* Índices:

  * `ingredient_batches(ingredient_uid, expiry_date)`
  * `ingredient_batches(state, storage_location)`
  * `consumption_log(session_id, step_id)`
* Tablas nuevas: `cooking_sessions`, `consumption_log`, `leftovers`, `waste_log`.

---

## 8) Seguridad & Validaciones

* **Label awareness**: si `label_type=use_by` y `now > expiry_date` → **prohibir** uso en recetas.
* **Unidad canónica**: normalizar `g/ml/u` en backend.
* **Servings scaling**: `mise_en_place` calcula cantidades escaladas.

---

## 9) OpenAPI (extracto YAML)

```yaml
openapi: 3.0.3
info:
  title: ZeroWasteAI API
  version: "1.3"
paths:
  /recipes/{recipe_uid}/mise_en_place:
    get:
      parameters:
        - in: path
          name: recipe_uid
          required: true
          schema: { type: string }
        - in: query
          name: servings
          schema: { type: integer, minimum: 1, default: 2 }
      responses:
        "200":
          description: Mise en place data
  /recipes/cooking_session/start:
    post:
      requestBody:
        required: true
      responses: { "201": { description: "Session created" } }
  /recipes/cooking_session/complete_step:
    post:
      requestBody: { required: true }
      responses: { "200": { description: "Step completed" } }
  /recipes/cooking_session/finish:
    post:
      requestBody: { required: true }
      responses: { "200": { description: "Finished" } }
  /inventory/expiring_soon:
    get:
      parameters:
        - in: query
          name: withinDays
          schema: { type: integer, default: 3 }
  /inventory/batch/{batch_id}/freeze:
    post:
      parameters: [{ in: path, name: batch_id, required: true, schema: {type:string}}]
      requestBody: { required: true }
      responses: { "200": { description: "Frozen" } }
```

> Puedes pegar este YAML en **Cursor** y completar *schemas* con los JSON de arriba.

---

## 10) Checklist de Aceptación (para PR)

* [ ] Endpoint **Mise en place** expone *tools/preheat/prep\_tasks/measured\_ingredients* escalados por `servings`.
* [ ] `start/complete_step/finish` registran telemetría y aplican **descuento por paso**.
* [ ] Consumos usan **lote FEFO** por defecto; selector de override permitido.
* [ ] `leftovers` crea ítem preparado y sugiere *planner*.
* [ ] `expiring_soon` ordena por `urgency_score`; `freeze/transform/quarantine/discard` actualizan estado y métricas.
* [ ] `calculate/from-session` usa **consumos reales** y guarda resultado.
* [ ] Idempotencia con `Idempotency-Key` en POST.
* [ ] Tests de integración para: concurrencia de `complete_step`, job de vencimientos y cálculo ambiental.

---

## 11) Prompts listos (para **Cursor** / agente de refactor)

**Crear endpoints de Cooking Session y Mise en place**

```
Implementa en Flask los endpoints:
- GET /api/recipes/{recipe_uid}/mise_en_place?servings=
- POST /api/recipes/cooking_session/start
- POST /api/recipes/cooking_session/complete_step
- POST /api/recipes/cooking_session/finish
Sigue los contratos JSON del documento. Usa transacciones en complete_step con lock por lot_id y respeta Idempotency-Key.
```

**Rescate y Cuarentena**

```
Añade:
- GET /api/inventory/expiring_soon?withinDays=
- POST /api/inventory/batch/{id}/reserve
- POST /api/inventory/batch/{id}/freeze
- POST /api/inventory/batch/{id}/transform
- POST /api/inventory/batch/{id}/quarantine
- POST /api/inventory/batch/{id}/discard
Incluye cálculo de urgency_score y reglas según label_type (use_by vs best_before).
```

**Métricas ambientales (reales por sesión)**

```
Crea POST /api/environmental_savings/calculate/from-session que reciba session_id y actual_consumptions[], compute co2e_kg/water_l/waste_kg, y persista.
Expón GET /api/environmental_savings/summary?period=week|month.
```


