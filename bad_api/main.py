"""
BAD API  —  "AI as Bypass" anti-pattern
========================================
What's wrong here (the audience should spot all of these):
  1. AI agent calls the database DIRECTLY — no service boundary
  2. No authentication or identity check on any endpoint
  3. No input validation — SQL injection possible
  4. No audit trail — decisions are invisible
  5. Broad access — agent can read/write ANY table
  6. Silent failures — errors swallowed, no observability
  7. No rate limiting — runaway agent can hammer the DB
"""

import sqlite3, time, random
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="❌ Unsafe AI Gateway (Anti-Pattern)", version="0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Simulated "database" (flat dict — no schema, no validation) ──────────────
_db = {
    "orders": [
        {"id": 1, "customer": "Alice",   "amount": 1200, "status": "pending"},
        {"id": 2, "customer": "Bob",     "amount": 450,  "status": "pending"},
        {"id": 3, "customer": "Charlie", "amount": 8900, "status": "pending"},
    ],
    "users": [
        {"id": 1, "name": "Alice",   "ssn": "123-45-6789", "credit_score": 720},
        {"id": 2, "name": "Bob",     "ssn": "987-65-4321", "credit_score": 580},
        {"id": 3, "name": "Charlie", "ssn": "555-44-3333", "credit_score": 810},
    ],
    "config": [
        {"key": "db_password",   "value": "prod-db-p@ssw0rd!"},
        {"key": "api_secret",    "value": "sk-live-abc123xyz"},
        {"key": "max_auto_approve", "value": "999999"},
    ]
}

# ── PROBLEM 1: AI agent hits the raw DB endpoint directly ────────────────────
@app.get("/db/query")
def raw_db_query(table: str, filter: str = ""):
    """
    Direct database access — no boundary, no contract.
    The AI agent uses this endpoint to read ANY table it wants.
    """
    time.sleep(0.05)  # fake latency
    rows = _db.get(table, [])
    if filter:
        rows = [r for r in rows if filter.lower() in str(r).lower()]
    return {"table": table, "rows": rows, "count": len(rows)}  # returns EVERYTHING including SSNs, passwords

# ── PROBLEM 2: AI agent approves orders with no policy check ─────────────────
@app.post("/db/orders/{order_id}/approve")
def approve_order_direct(order_id: int, approved_by: str = "ai-agent"):
    """
    No workflow, no policy gate, no human approval threshold.
    The AI just writes directly. $8,900 order? Approved. No questions asked.
    """
    for order in _db["orders"]:
        if order["id"] == order_id:
            order["status"] = "approved"
            order["approved_by"] = approved_by
            # No audit record written anywhere
            return {"result": "approved", "order": order}
    return {"result": "not_found"}

# ── PROBLEM 3: No audit trail whatsoever ─────────────────────────────────────
@app.get("/audit/log")
def get_audit_log():
    """There is no audit log. Decisions are invisible."""
    return {"audit_log": [], "message": "No audit trail exists. AI decisions are untracked."}

# ── PROBLEM 4: Agent can access sensitive config ─────────────────────────────
@app.get("/db/config")
def get_config():
    """Secrets exposed because the agent has broad access."""
    return {"config": _db["config"]}

@app.get("/health")
def health():
    return {"status": "running", "service": "bad-api", "port": 8001}
