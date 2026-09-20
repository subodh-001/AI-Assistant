#!/bin/bash
# ============================================================
#   BRO-BOT — One-Command Launcher 🤖
#   Usage: chmod +x start.sh && ./start.sh
# ============================================================

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

echo ""
echo -e "${PURPLE}${BOLD}"
echo "  ██████╗ ██████╗  ██████╗       ██████╗  ██████╗ ████████╗"
echo "  ██╔══██╗██╔══██╗██╔═══██╗      ██╔══██╗██╔═══██╗╚══██╔══╝"
echo "  ██████╔╝██████╔╝██║   ██║█████╗██████╔╝██║   ██║   ██║   "
echo "  ██╔══██╗██╔══██╗██║   ██║╚════╝██╔══██╗██║   ██║   ██║   "
echo "  ██████╔╝██║  ██║╚██████╔╝      ██████╔╝╚██████╔╝   ██║   "
echo "  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝       ╚═════╝  ╚═════╝    ╚═╝   "
echo -e "${NC}"
echo -e "${CYAN}  Your Personal AI Life Manager${NC}"
echo -e "${BLUE}  ────────────────────────────────────────${NC}"
echo ""

# ── Check Python ──
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found! Install it first.${NC}"
    exit 1
fi

PYTHON=python3
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# ── Check .env ──
echo -e "${YELLOW}🔍 Checking configuration...${NC}"
if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo -e "${YELLOW}⚠️  No .env file found. Creating from template...${NC}"
    cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
    echo -e "${YELLOW}📝 Edit ${BACKEND_DIR}/.env and add your API keys!${NC}"
    echo ""
fi

# ── Install dependencies ──
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
cd "$BACKEND_DIR"
$PYTHON -m pip install -r requirements.txt -q --no-warn-script-location 2>&1 | tail -5
echo -e "${GREEN}✅ Dependencies ready${NC}"
echo ""

# ── Start backend ──
echo -e "${PURPLE}🚀 Starting BRO-BOT Backend...${NC}"
echo -e "${CYAN}   API: http://localhost:8000${NC}"
echo -e "${CYAN}   Docs: http://localhost:8000/docs${NC}"
echo ""

# Open dashboard in browser after a delay
(sleep 3 && xdg-open "http://localhost:8000" 2>/dev/null || open "http://localhost:8000" 2>/dev/null || echo "") &

# Alternative: open frontend directly if no server is running
(sleep 2 && xdg-open "$FRONTEND_DIR/index.html" 2>/dev/null || open "$FRONTEND_DIR/index.html" 2>/dev/null || echo "") &

# Start the FastAPI server
$PYTHON "$BACKEND_DIR/main.py"
