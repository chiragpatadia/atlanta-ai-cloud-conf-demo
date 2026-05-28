#!/usr/bin/env python3
"""
LIVE DEMO SCRIPT  —  Atlanta Cloud + AI Conference 2026
=======================================================
Run this AFTER starting both servers.
Each section maps to a talking point in your presentation.

Usage:
    python demo.py

The script pauses at each step so you can narrate to the audience.
Press ENTER to advance.
"""

import requests, json, time, sys

BAD  = "http://localhost:8001"
GOOD = "http://localhost:8002"

# ── Colors ───────────────────────────────────────────────────────────────────
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

def banner(title, color=CYAN):
    width = 70
    print(f"\n{color}{BOLD}{'═'*width}")
    print(f"  {title}")
    print(f"{'═'*width}{RESET}\n")

def step(label):
    print(f"\n{YELLOW}{BOLD}▶  {label}{RESET}")

def show_response(r, label="Response"):
    try:
        data = r.json()
        pretty = json.dumps(data, indent=2)
    except Exception:
        pretty = r.text
    status_color = GREEN if r.status_code < 400 else RED
    print(f"{DIM}  HTTP {r.status_code}  ← {label}{RESET}")
    # Highlight key fields
    for line in pretty.split("\n"):
        if any(k in line for k in ["error", "UNAUTHORIZED", "FORBIDDEN", "ESCALATED", "LOW_CONF"]):
            print(f"  {RED}{line}{RESET}")
        elif any(k in line for k in ["APPROVED", "SUCCESS", "audit_id", "policy_enforced"]):
            print(f"  {GREEN}{line}{RESET}")
        elif any(k in line for k in ["ssn", "password", "secret", "credit_score", "api_secret"]):
            print(f"  {RED}{BOLD}{line}  ← ⚠️  SENSITIVE DATA EXPOSED{RESET}")
        else:
            print(f"  {line}")

def pause(msg="Press ENTER to continue..."):
    input(f"\n  {DIM}{msg}{RESET}")

def wait_for_servers():
    print(f"\n{DIM}  Checking servers...", end="")
    for port, name in [(8001, "Bad API"), (8002, "Good API")]:
        try:
            r = requests.get(f"http://localhost:{port}/health", timeout=2)
            print(f"  ✓ {name} running", end="")
        except Exception:
            print(f"\n\n  {RED}✗ {name} not running on port {port}.{RESET}")
            print(f"  Start it with:  {BOLD}uvicorn {name.lower().replace(' ','_').replace('-','_')}.main.main:app --port {port}{RESET}\n")
            sys.exit(1)
    print(f"  — ready!{RESET}\n")

# ═════════════════════════════════════════════════════════════════════════════
# DEMO BEGINS
# ═════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    wait_for_servers()

    print(f"""
{CYAN}{BOLD}
  ╔══════════════════════════════════════════════════════════════════╗
  ║   LIVE DEMO: Boundary Violation vs. Sovereign AI Gateway        ║
  ║   Atlanta Cloud + AI Conference 2026  —  Chirag Patadia         ║
  ╚══════════════════════════════════════════════════════════════════╝
{RESET}
  Two services are running:
    {RED}Port 8001{RESET}  —  ❌ Unsafe Anti-Pattern  (what most systems look like today)
    {GREEN}Port 8002{RESET}  —  ✅ Sovereign Pattern    (what we're building toward)

  Same underlying data. Completely different architecture.
    """)

    pause("Press ENTER to start the demo...")

    # ─────────────────────────────────────────────────────────────────────
    # ACT 1: THE BAD API
    # ─────────────────────────────────────────────────────────────────────
    banner("ACT 1  —  ❌ The Anti-Pattern: AI as Bypass", RED)

    print(f"""  {DIM}Narrator: "Here's what happens when AI gets wired directly into your
  systems with no architectural discipline. No boundaries. No contracts.
  No audit trail. Let's see what the AI agent can actually access."{RESET}""")

    pause()

    # --- Step 1: AI reads orders (fine so far...)
    step("AI agent reads pending orders — seems fine...")
    r = requests.get(f"{BAD}/db/query?table=orders")
    show_response(r, "Direct DB read — orders table")
    pause()

    # --- Step 2: AI reads the USERS table — SSNs exposed
    step("AI agent reads the USERS table next — same endpoint, no restriction...")
    r = requests.get(f"{BAD}/db/query?table=users")
    show_response(r, "Direct DB read — users table (SSNs exposed!)")
    print(f"\n  {RED}{BOLD}  ⚠️  The AI just read every customer's SSN and credit score.{RESET}")
    print(f"  {RED}  Nothing stopped it. No scope check. No audit record.{RESET}")
    pause()

    # --- Step 3: AI reads config / secrets
    step("Let's try the config table...")
    r = requests.get(f"{BAD}/db/config")
    show_response(r, "Config endpoint — secrets exposed!")
    print(f"\n  {RED}{BOLD}  ⚠️  Production DB password and API secret — fully visible.{RESET}")
    pause()

    # --- Step 4: AI approves a high-value order — no policy gate
    step("AI approves a $8,900 order with no policy gate, no human review...")
    r = requests.post(f"{BAD}/db/orders/3/approve")
    show_response(r, "Direct order approval — $8,900, no questions asked")
    print(f"\n  {RED}{BOLD}  ⚠️  $8,900 approved instantly. No reason required. No audit record.{RESET}")
    pause()

    # --- Step 5: No audit trail
    step("Let's check the audit log to see what the AI did...")
    r = requests.get(f"{BAD}/audit/log")
    show_response(r, "Audit log")
    print(f"\n  {RED}{BOLD}  ⚠️  Nothing. Zero visibility into what the AI decided or why.{RESET}")
    print(f"  {RED}  Try explaining that to your compliance team.{RESET}")
    pause()

    # ─────────────────────────────────────────────────────────────────────
    # TRANSITION
    # ─────────────────────────────────────────────────────────────────────
    print(f"""
  {YELLOW}{BOLD}  ──────────────────────────────────────────────────────────
  This is what "AI as Bypass" looks like in production.
  Same system. Same data. Zero architecture.
  Now let's see what sovereign architecture changes.
  ──────────────────────────────────────────────────────────{RESET}""")
    pause("Press ENTER for Act 2: The Sovereign Pattern...")

    # ─────────────────────────────────────────────────────────────────────
    # ACT 2: THE GOOD API
    # ─────────────────────────────────────────────────────────────────────
    banner("ACT 2  —  ✅ The Sovereign Pattern: Bounded AI", GREEN)

    print(f"""  {DIM}Narrator: "Same AI agent. Same underlying data. But now it goes
  through a Tool Gateway with scoped identity, schema contracts,
  a policy gate, and an immutable audit trail."{RESET}""")
    pause()

    # --- Step 1: No token = rejected
    step("AI agent tries to call the gateway with NO identity token...")
    r = requests.get(f"{GOOD}/tools/orders/pending")
    show_response(r, "No token — should be rejected")
    print(f"\n  {GREEN}  ✓ Rejected immediately. No identity = no access.{RESET}")
    pause()

    # --- Step 2: Wrong scope = rejected
    step("AI agent uses a read-only token to try to approve an order...")
    r = requests.post(
        f"{GOOD}/tools/orders/1/approve",
        json={"reason": "Customer meets all criteria for approval", "confidence_score": 0.95},
        headers={"X-Agent-Token": "agent-token-readonly"}
    )
    show_response(r, "Read-only token attempting approval — should be forbidden")
    print(f"\n  {GREEN}  ✓ Forbidden. Least-privilege enforced. Token scope doesn't include orders:approve.{RESET}")
    pause()

    # --- Step 3: Valid token reads orders — but only safe fields
    step("AI agent reads orders with a valid scoped token...")
    r = requests.get(
        f"{GOOD}/tools/orders/pending",
        headers={"X-Agent-Token": "agent-token-readonly"}
    )
    show_response(r, "Scoped read — only approved fields returned")
    print(f"\n  {GREEN}  ✓ Works — but notice: no SSNs, no credit scores, no secrets.{RESET}")
    print(f"  {GREEN}  Only what the agent needs to do its job.{RESET}")
    pause()

    # --- Step 4: Try to read SSNs via the tool gateway
    step("AI agent tries to read sensitive user data through the gateway...")
    r = requests.get(
        f"{GOOD}/tools/orders/pending?table=users",
        headers={"X-Agent-Token": "agent-token-readonly"}
    )
    show_response(r, "Attempting to access user/SSN data")
    print(f"\n  {GREEN}  ✓ The tool simply doesn't expose that endpoint. Boundary enforced.{RESET}")
    pause()

    # --- Step 5: Approve a low-value order — succeeds
    step("AI agent approves a low-value order ($450) with proper reason...")
    r = requests.post(
        f"{GOOD}/tools/orders/2/approve",
        json={
            "reason": "Order amount $450 is within automated approval threshold. Customer history verified.",
            "confidence_score": 0.92
        },
        headers={"X-Agent-Token": "agent-token-approver"}
    )
    show_response(r, "Low-value order approval")
    print(f"\n  {GREEN}  ✓ Approved. But notice: audit_id recorded, reason required, confidence checked.{RESET}")
    pause()

    # --- Step 6: Try to approve the HIGH-VALUE order — policy gate kicks in
    step("AI agent tries to approve the $8,900 order...")
    r = requests.post(
        f"{GOOD}/tools/orders/3/approve",
        json={
            "reason": "Order amount $8900 verified against customer credit profile and purchase history.",
            "confidence_score": 0.88
        },
        headers={"X-Agent-Token": "agent-token-approver"}
    )
    show_response(r, "High-value order — policy gate")
    print(f"\n  {GREEN}  ✓ ESCALATED to human review. AI cannot approve high-risk actions autonomously.{RESET}")
    print(f"  {GREEN}  Architecture enforces the boundary — not the AI's judgment.{RESET}")
    pause()

    # --- Step 7: Low confidence — rejected
    step("What if the AI is uncertain? Low confidence score...")
    r = requests.post(
        f"{GOOD}/tools/orders/1/approve",
        json={
            "reason": "Order appears valid based on available context and pattern matching.",
            "confidence_score": 0.55
        },
        headers={"X-Agent-Token": "agent-token-approver"}
    )
    show_response(r, "Low confidence — should be rejected")
    print(f"\n  {GREEN}  ✓ Rejected. Confidence 0.55 < threshold 0.70. Architecture won't let a hesitant AI decide.{RESET}")
    pause()

    # --- Step 8: Audit trail — everything is there
    step("Now let's check the audit log...")
    r = requests.get(
        f"{GOOD}/audit/log",
        headers={"X-Agent-Token": "agent-token-readonly"}
    )
    show_response(r, "Immutable audit trail")
    print(f"\n  {GREEN}  ✓ Every decision. Every identity. Every reason. Every outcome.{RESET}")
    print(f"  {GREEN}  Fully reconstructable. Compliance-ready.{RESET}")
    pause()

    # ─────────────────────────────────────────────────────────────────────
    # WRAP-UP
    # ─────────────────────────────────────────────────────────────────────
    banner("DEMO COMPLETE  —  Key Takeaways", CYAN)

    print(f"""
  {BOLD}What we just showed:{RESET}

  {RED}❌  Anti-Pattern (Bad API){RESET}
      • AI read SSNs, passwords, config secrets — no boundary
      • $8,900 order approved with zero policy check
      • Zero audit trail — decisions invisible to compliance

  {GREEN}✅  Sovereign Pattern (Good API){RESET}
      • No token = no access (identity enforced)
      • Read-only agent cannot approve (least privilege)
      • Sensitive data never exposed (scoped contracts)
      • High-value orders escalated to humans (policy gate)
      • Low-confidence AI rejected (confidence threshold)
      • Every decision auditable (immutable trail)

  {CYAN}{BOLD}Same data. Same AI agent. Completely different risk profile.{RESET}

  {DIM}Full code at: github.com/chiragpatadia  (add your repo before the talk!){RESET}
    """)
