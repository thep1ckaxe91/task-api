# Tasks API (`tasks-api`)

Production-grade, Spec-First Task Management REST API built with Flask, OpenAPI 3.0.3, Bearer JWT Authentication, and RFC 7807 Problem Details error responses.

---

## 1. Quick Start & Local Development

All dependencies must be installed in a localized virtual environment. Never install packages globally.

### 1.1. Prerequisites
- Python >= 3.10
- Bash / cURL

### 1.2. Virtual Environment Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### 1.3. Running the Service
```bash
python wsgi.py
```
- API Base URL: `http://127.0.0.1:5000`
- Swagger UI Documentation: `http://127.0.0.1:5000/docs`
- Raw OpenAPI JSON: `http://127.0.0.1:5000/openapi.json`
- Healthcheck: `http://127.0.0.1:5000/health`

---

## 2. Automated Testing

### 2.1. Pytest Test Suite
```bash
timeout 30 pytest -v
```

### 2.2. Automated CLI Smoke Tests (`curl`)
Execute end-to-end verification across all 5 CRUD endpoints, auth, and error contracts:
```bash
timeout 60 ./tests/curl_smoke_test.sh
```

---

## 3. Architecture Decision Records (ADRs)

### ADR-01: Cursor-based Pagination vs. Offset Pagination

* **Context:**
  High-throughput REST APIs require a predictable, low-latency strategy for paginating large data collections. Standard SQL `OFFSET N LIMIT M` pagination introduces significant performance and consistency degradation as $N$ scales.

* **Analysis (Quantitative & Low-Latency Systems Perspective):**
  1. **Algorithmic Complexity & Index Traversal:**
     - `OFFSET N`: The storage engine is forced to scan and discard $N$ tuple rows before reading the requested $M$ rows ($\mathcal{O}(N + M)$).
     - `Cursor-based` (`WHERE (created_at, id) < (:cursor_created_at, :cursor_id) LIMIT M`): Enables direct B+ Tree index seek ($\mathcal{O}(\log K + M)$). Execution latency is $\mathcal{O}(1)$ relative to page depth.
  2. **Hardware Cache Locality & Buffer Pool Thrashing:**
     - Sequentially scanning thousands of discarded index entries causes high cache eviction in CPU L1/L2/L3 data caches and flushes active database buffer pool pages.
     - Kept records via cursor seek minimize memory bandwidth saturation and retain deterministic p99 response times.
  3. **Data Drift Elimination:**
     - Offset pagination produces duplicated or skipped items when tasks are inserted or removed between client requests. Cursor pagination maintains a deterministic window anchored on immutable keys.

* **Decision:**
  Adopt **Cursor-based Pagination** (`limit`, `starting_after`) across all collection endpoints.

---

### ADR-02: RFC 7396 (JSON Merge Patch) vs. RFC 6902 (JSON Patch) and Full PUT

* **Context:**
  Partial updates require precise semantics for modifying entity fields without full resource re-transmission or race hazards.

* **Analysis:**
  1. **Full Replacement (`PUT`):**
     - Forces client to submit all entity fields, creating race conditions (Lost Update problem) when concurrent clients update distinct fields simultaneously.
  2. **[RFC 6902 (JSON Patch)](https://datatracker.ietf.org/doc/html/rfc6902):**
     - Uses an array of mutation operations (`[{"op": "replace", "path": "/title", "value": "..."}]`).
     - Higher serialization overhead, requires allocating an Abstract Syntax Tree (AST) parser in memory, complex transactional rollbacks on multi-operation failures.
  3. **[RFC 7396 (JSON Merge Patch)](https://datatracker.ietf.org/doc/html/rfc7396):**
     - Uses a flat dictionary matching the target resource layout (`{"status": "completed"}`).
     - Directly deserializable into target object structures with minimal CPU cycle overhead. Null values explicitly denote deletion of optional fields.

* **Decision:**
  Implement `PATCH /tasks/{id}` conforming strictly to **[RFC 7396 JSON Merge Patch](https://datatracker.ietf.org/doc/html/rfc7396)**.

---

## 4. Error Handling Standard ([RFC 7807](https://datatracker.ietf.org/doc/html/rfc7807) / [RFC 9457](https://datatracker.ietf.org/doc/html/rfc9457))

All non-2xx responses strictly emit `Content-Type: application/problem+json`:
```json
{
  "type": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/422",
  "title": "Unprocessable Entity",
  "status": 422,
  "detail": "Validation failed: 'title' is required.",
  "instance": "/tasks",
  "invalid_params": [
    {
      "name": "title",
      "reason": "Field is required and cannot be empty"
    }
  ]
}
```
HTTP status code hygiene is enforced: zero 200 responses with embedded error bodies.
