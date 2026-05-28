#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  START DEMO  —  Atlanta Cloud + AI Conference 2026
#  Starts both servers in background, then opens the demo runner
# ─────────────────────────────────────────────────────────────

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "  ╔══════════════════════════════════════════════════╗"
echo "  ║   Sovereign Demo — Starting Services             ║"
echo "  ╚══════════════════════════════════════════════════╝"
echo ""

# Check Python + uvicorn
if ! command -v uvicorn &> /dev/null; then
    echo "  Installing dependencies..."
    pip install fastapi uvicorn pydantic requests --quiet
fi

# Kill any old instances
pkill -f "uvicorn bad_api" 2>/dev/null || true
pkill -f "uvicorn good_api" 2>/dev/null || true
sleep 0.5

# Start Bad API on 8001
cd "$SCRIPT_DIR/bad_api"
uvicorn main:app --port 8001 --log-level warning &
BAD_PID=$!
echo "  ✓ Bad API  started  → http://localhost:8001  (pid $BAD_PID)"

# Start Good API on 8002
cd "$SCRIPT_DIR/good_api"
uvicorn main:app --port 8002 --log-level warning &
GOOD_PID=$!
echo "  ✓ Good API started  → http://localhost:8002  (pid $GOOD_PID)"

# Save PIDs for cleanup
echo "$BAD_PID $GOOD_PID" > "$SCRIPT_DIR/.pids"

sleep 1.5

echo ""
echo "  Swagger UIs (open in browser for side-by-side):"
echo "    ❌  http://localhost:8001/docs   — Anti-Pattern"
echo "    ✅  http://localhost:8002/docs   — Sovereign Pattern"
echo ""
echo "  Press Ctrl+C to stop servers after the demo."
echo ""

# Run the interactive demo script
cd "$SCRIPT_DIR"
python demo.py

# Cleanup on exit
trap "kill $BAD_PID $GOOD_PID 2>/dev/null; echo '  Servers stopped.'" EXIT
wait
