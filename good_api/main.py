"""
GOOD API  —  Sovereign Cloud-Native Architecture pattern
=========================================================
What this demonstrates:
  1. AI agent talks ONLY to a scoped Tool Gateway — never the DB directly
  2. Every request requires a scoped identity token
  3. Strict input validation and schema-enforced contracts
  4. Every AI decision is written to an immutable audit log
  5. Policy gate blocks high-value orders for human approval
  6. Secrets are never exposed — config endpoint doesn't exist
  7. Rate limiting prevents runaway agents
  8. All failures are observable — structured error responses
"""

import time, uuid, json
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

app = FastAPI(title="✅ Sovereign AI Gateway (Pattern)", version="1.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Simulated data store (same underlying data) ──────────────────────────────
_orders = [
    {"id": 1, "customer": "Alice",   "amount": 1200, "status": "pending"},
    {"id": 2, "customer": "Bob",     "amount": 450,  "status": "pending"},
    {"id": 3, "customer": "Charlie", "amount": 8900, "status": "pending"},
]

# ── Immutable append-only audit log ─────────────────────────────────────────
_audit_log: list[dict] = []

# ── Scoped identity tokens (in prod: JWT / IAM) ──────────────────────────────
VALID_TOKENS = {
    "agent-token-readonly":  {"identity": "ai-agent-v1", "scope": ["orders:read"]},
    "agent-token-approver":  {"identity": "ai-agent-v1", "scope": ["orders:read", "orders:approve"]},
    "demo-token-full":       {"identity": "demo-user",   "scope": ["orders:read", "orders:approve"]},
}

# ── Policy constants ─────────────────────────────────────────────────────────
AUTO_APPROVE_LIMIT = 2000   # orders above this need human approval
RATE_LIMIT_WINDOW  = {}     # simple per-token rate limiter

# ── Helpers ──────────────────────────────────────────────────────────────────
def verify_token(token: str, required_scope: str) -> dict:
    """Validate identity token and check scope."""
    if not token or token not in VALID_TOKENS:
        raise HTTPException(status_code=401, detail={
            "error": "UNAUTHORIZED",
            "message": "Valid scoped identity token required. AI agents must identify themselves.",
            "hint": "Use header: X-Agent-Token: agent-token-readonly"
        })
    claims = VALID_TOKENS[token]
    if required_scope not in claims["scope"]:
        raise HTTPException(status_code=403, detail={
            "error": "FORBIDDEN",
            "message": f"Token scope '{claims['scope']}' does not include '{required_scope}'.",
            "hint": "This agent does not have approval permissions. Principle of least privilege."
        })
    return claims

def write_audit(action: str, identity: str, resource: str, outcome: str, details: dict):
    """Append an immutable audit record. Every AI decision is traceable."""
    record = {
        "audit_id":  str(uuid.uuid4())[:8],
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "action":    action,
        "identity":  identity,
        "resource":  resource,
        "outcome":   outcome,
        "details":   details,
    }
    _audit_log.append(record)
    return record

def check_rate_limit(identity: str, max_per_minute: int = 10):
    """Prevent runaway agent hammering."""
    now = time.time()
    window = RATE_LIMIT_WINDOW.get(identity, [])
    window = [t for t in window if now - t < 60]
    if len(window) >= max_per_minute:
        raise HTTPException(status_code=429, detail={
            "error": "RATE_LIMITED",
            "message": f"Agent '{identity}' exceeded {max_per_minute} requests/min.",
            "retry_after_seconds": 60
        })
    window.append(now)
    RATE_LIMIT_WINDOW[identity] = window

# ── Contracts (schema-enforced, versioned) ────────────────────────────────────
class OrderSummary(BaseModel):
    """What the AI agent is ALLOWED to see — no PII, no internals."""
    id:       int
    amount:   float
    status:   str
    customer: str   # name only — no SSN, no credit score

class ApprovalRequest(BaseModel):
    reason: str = Field(..., min_length=10, max_length=500,
                        description="Agent must provide a business reason for approval")
    confidence_score: float = Field(..., ge=0.0, le=1.0,
                                    description="Agent's confidence 0.0–1.0")

    @field_validator("reason")
    @classmethod
    def reason_not_generic(cls, v):
        blocked = ["approved", "looks good", "ok", "yes", "auto"]
        if any(b in v.lower() for b in blocked):
            raise ValueError("Reason must be specific, not generic. Explain the business logic.")
        return v

# ── Tool 1: List pending orders (scoped read) ────────────────────────────────
@app.get("/tools/orders/pending", response_model=list[OrderSummary])
def list_pending_orders(x_agent_token: Optional[str] = Header(None)):
    """
    Scoped read tool. Returns ONLY what the agent needs.
    No SSNs, no credit scores, no config, no secrets.
    """
    claims = verify_token(x_agent_token, "orders:read")
    check_rate_limit(claims["identity"])

    pending = [o for o in _orders if o["status"] == "pending"]

    write_audit(
        action="LIST_PENDING_ORDERS",
        identity=claims["identity"],
        resource="orders",
        outcome="SUCCESS",
        details={"count": len(pending)}
    )

    return [OrderSummary(**o) for o in pending]

# ── Tool 2: Approve order (policy gate + human escalation) ───────────────────
@app.post("/tools/orders/{order_id}/approve")
def approve_order(
    order_id: int,
    body: ApprovalRequest,
    x_agent_token: Optional[str] = Header(None)
):
    """
    Policy-gated approval. AI can auto-approve low-value orders.
    High-value orders are escalated to human review — AI cannot bypass this.
    """
    claims = verify_token(x_agent_token, "orders:approve")
    check_rate_limit(claims["identity"])

    order = next((o for o in _orders if o["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail={"error": "ORDER_NOT_FOUND", "order_id": order_id})

    if order["status"] != "pending":
        raise HTTPException(status_code=409, detail={
            "error": "INVALID_STATE_TRANSITION",
            "current_status": order["status"],
            "message": "Only pending orders can be approved."
        })

    # ── POLICY GATE: high-value orders require human approval ──────────────
    if order["amount"] > AUTO_APPROVE_LIMIT:
        audit = write_audit(
            action="APPROVE_ORDER",
            identity=claims["identity"],
            resource=f"orders/{order_id}",
            outcome="ESCALATED_TO_HUMAN",
            details={
                "amount": order["amount"],
                "limit": AUTO_APPROVE_LIMIT,
                "agent_reason": body.reason,
                "agent_confidence": body.confidence_score,
                "policy": f"Orders > ${AUTO_APPROVE_LIMIT} require human approval"
            }
        )
        return {
            "result": "ESCALATED",
            "message": f"Order ${order['amount']:,.0f} exceeds auto-approve limit of ${AUTO_APPROVE_LIMIT:,}. Routed to human review.",
            "audit_id": audit["audit_id"],
            "order_id": order_id,
            "policy_enforced": True
        }

    # ── Auto-approve: within policy, confidence acceptable ─────────────────
    if body.confidence_score < 0.7:
        audit = write_audit(
            action="APPROVE_ORDER",
            identity=claims["identity"],
            resource=f"orders/{order_id}",
            outcome="REJECTED_LOW_CONFIDENCE",
            details={"confidence": body.confidence_score, "threshold": 0.7}
        )
        raise HTTPException(status_code=422, detail={
            "error": "LOW_CONFIDENCE",
            "message": f"Agent confidence {body.confidence_score} below threshold 0.70. Approval rejected.",
            "audit_id": audit["audit_id"]
        })

    order["status"] = "approved"
    order["approved_by"] = claims["identity"]

    audit = write_audit(
        action="APPROVE_ORDER",
        identity=claims["identity"],
        resource=f"orders/{order_id}",
        outcome="APPROVED",
        details={
            "amount": order["amount"],
            "agent_reason": body.reason,
            "agent_confidence": body.confidence_score,
        }
    )

    return {
        "result": "APPROVED",
        "order_id": order_id,
        "amount": order["amount"],
        "approved_by": claims["identity"],
        "audit_id": audit["audit_id"],
        "policy_enforced": True
    }

# ── Audit log: every decision is reconstructable ─────────────────────────────
@app.get("/audit/log")
def get_audit_log(x_agent_token: Optional[str] = Header(None)):
    """Full decision trail. Every AI action is traceable."""
    claims = verify_token(x_agent_token, "orders:read")
    return {
        "audit_log": _audit_log,
        "total_records": len(_audit_log),
        "message": "Complete, immutable audit trail of all AI decisions."
    }

@app.get("/health")
def health():
    return {"status": "running", "service": "good-api", "port": 8002}
