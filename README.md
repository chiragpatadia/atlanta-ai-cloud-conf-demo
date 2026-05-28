# Sovereign Demo — Atlanta Cloud + AI Conference 2026
### "From Legacy Integration to Sovereign Cloud-Native Systems"
**Chirag Patadia**

---

## What This Demo Shows

Two FastAPI services running side by side on your laptop:

| Port | Service | Represents |
|------|---------|------------|
| 8001 | ❌ Bad API | The anti-pattern — AI as bypass, direct DB access, no audit |
| 8002 | ✅ Good API | Sovereign pattern — Tool Gateway, policy gates, audit trail |

**Same underlying data. Same AI agent scenario. Completely different architecture.**

---

## Setup (do this the night before)

```bash
# 1. Install dependencies (one time)
pip install fastapi uvicorn pydantic requests

# 2. Make startup script executable
chmod +x start_demo.sh
```

---

## Running the Demo

```bash
./start_demo.sh
```

This starts both servers and launches the interactive demo script.
Press **ENTER** to advance through each step.

---

## Demo Flow

### ACT 1 — The Anti-Pattern (Bad API, port 8001) ~4 min

| Step | What happens | Your talking point |
|------|-------------|-------------------|
| 1 | AI reads orders table | "Seems harmless..." |
| 2 | AI reads users table — **SSNs exposed** | "Nothing stopped it. No scope check." |
| 3 | AI reads config — **DB password + API key exposed** | "Broad access means the AI can see everything." |
| 4 | AI approves **$8,900 order** — no policy gate | "Zero friction. Zero oversight." |
| 5 | Audit log is **empty** | "Try explaining this to your compliance team." |

### ACT 2 — The Sovereign Pattern (Good API, port 8002) ~5 min

| Step | What happens | Your talking point |
|------|-------------|-------------------|
| 1 | No token → **401 rejected** | "No identity, no access. Full stop." |
| 2 | Read-only token tries to approve → **403 forbidden** | "Least privilege. The token can't do what it wasn't scoped for." |
| 3 | Valid token reads orders — **no SSNs, no secrets** | "Only what the agent needs. Nothing more." |
| 4 | Tries to reach user/config data → **endpoint doesn't exist** | "The boundary is enforced by design, not policy." |
| 5 | Approves **$450 order** → succeeds with audit record | "Works. But notice: reason required, audit_id written." |
| 6 | Tries to approve **$8,900 order** → **ESCALATED** | "Architecture enforces the limit. Not the AI's judgment." |
| 7 | Low confidence (0.55) → **rejected** | "A hesitant AI shouldn't decide. Architecture catches it." |
| 8 | Audit log → **everything is there** | "Every decision. Every identity. Fully reconstructable." |

---

## Swagger UI (optional — show in browser)

Open both in side-by-side browser windows:
- **http://localhost:8001/docs** — Anti-Pattern
- **http://localhost:8002/docs** — Sovereign Pattern

The contrast in available endpoints alone tells the story.

---

## Key Phrases for Each Moment

- When SSNs appear: *"The AI just read every customer's social security number. Nothing stopped it. No scope check. No audit record."*
- When $8,900 is approved without a gate: *"Eight thousand nine hundred dollars. Approved. Instantly. No reason. No review. No trace."*
- When 401 fires: *"No identity, no access. This is what a trust boundary looks like."*
- When escalation fires: *"The architecture made that decision — not the AI. That's the whole point."*
- When the audit log appears: *"Every decision. Every agent. Every reason. Every outcome. This is what evidence-ready looks like."*

---

## Timing Guide (60-minute session)

| Segment | Time |
|---------|------|
| Hook + Problem (slides 1–3) | 0–8 min |
| Case Studies (slides 6–8) | 8–30 min |
| Architecture Patterns (slide 9) | 30–38 min |
| **LIVE DEMO** | 38–48 min |
| 60-Day Playbook + Takeaways | 48–55 min |
| Q&A | 55–60 min |
