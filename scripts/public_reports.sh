#!/bin/bash
#
# public_reports.sh - Create a public URL for HTML reports using ngrok
#
# Usage:
#   ./scripts/public_reports.sh [PORT]
#
# Prerequisites:
#   - ngrok installed (https://ngrok.com)
#   - ngrok authenticated (run: ngrok config add-authtoken <token>)
#
# Examples:
#   ./scripts/public_reports.sh           # Uses default port 8080
#   ./scripts/public_reports.sh 3000      # Uses port 3000
#
# The script will:
#   1. Start a local HTTP server (background)
#   2. Start ngrok tunnel
#   3. Display the public URL
#

set -e

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORTS_DIR="${PROJECT_ROOT}/reports/html"
DEFAULT_PORT=8080
PORT="${1:-$DEFAULT_PORT}"
PID_FILE="/tmp/stock_analyzer_server.pid"
NGROK_LOG="/tmp/ngrok.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down...${NC}"
    
    # Kill HTTP server
    if [ -f "$PID_FILE" ]; then
        SERVER_PID=$(cat "$PID_FILE")
        if kill -0 "$SERVER_PID" 2>/dev/null; then
            kill "$SERVER_PID" 2>/dev/null || true
            echo -e "${GREEN}Stopped HTTP server (PID: ${SERVER_PID})${NC}"
        fi
        rm -f "$PID_FILE"
    fi
    
    # Kill ngrok
    if pgrep -x ngrok > /dev/null; then
        pkill -x ngrok 2>/dev/null || true
        echo -e "${GREEN}Stopped ngrok${NC}"
    fi
    
    rm -f "$NGROK_LOG"
    echo -e "${GREEN}Cleanup complete.${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}   Stock Analyzer - Public Report Server${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} Python 3 found"

# Check ngrok
if ! command -v ngrok &> /dev/null; then
    echo -e "${RED}Error: ngrok is not installed.${NC}"
    echo -e "${YELLOW}Install ngrok from: https://ngrok.com/download${NC}"
    echo -e "${YELLOW}Then authenticate: ngrok config add-authtoken <your-token>${NC}"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} ngrok found"

# Check ngrok authentication
if ! ngrok config check &> /dev/null 2>&1; then
    echo -e "${RED}Error: ngrok is not authenticated.${NC}"
    echo -e "${YELLOW}Run: ngrok config add-authtoken <your-token>${NC}"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} ngrok authenticated"

# Check reports directory
if [ ! -d "$REPORTS_DIR" ]; then
    echo -e "${RED}Error: Reports directory not found: ${REPORTS_DIR}${NC}"
    exit 1
fi

# Count reports
REPORT_COUNT=$(find "$REPORTS_DIR" -name "*.html" -type f | wc -l | tr -d ' ')
if [ "$REPORT_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}Warning: No HTML reports found.${NC}"
else
    echo -e "  ${GREEN}✓${NC} Found ${REPORT_COUNT} HTML report(s)"
fi

# Get latest report
LATEST_REPORT=$(ls -t "${REPORTS_DIR}"/*.html 2>/dev/null | head -1)
LATEST_NAME=""
if [ -n "$LATEST_REPORT" ]; then
    LATEST_NAME=$(basename "$LATEST_REPORT")
    echo -e "  ${GREEN}✓${NC} Latest: ${LATEST_NAME}"
fi

echo ""

# Kill any existing processes
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        kill "$OLD_PID" 2>/dev/null || true
    fi
    rm -f "$PID_FILE"
fi

if pgrep -x ngrok > /dev/null; then
    echo -e "${YELLOW}Stopping existing ngrok process...${NC}"
    pkill -x ngrok 2>/dev/null || true
    sleep 1
fi

# Start HTTP server in background
echo -e "${BLUE}Starting local HTTP server on port ${PORT}...${NC}"
cd "$REPORTS_DIR"
python3 -m http.server "$PORT" > /dev/null 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > "$PID_FILE"
echo -e "  ${GREEN}✓${NC} Server started (PID: ${SERVER_PID})"

# Wait for server to be ready
sleep 1
if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo -e "${RED}Error: HTTP server failed to start.${NC}"
    exit 1
fi

# Start ngrok
echo -e "${BLUE}Starting ngrok tunnel...${NC}"
ngrok http "$PORT" --log="$NGROK_LOG" > /dev/null 2>&1 &
NGROK_PID=$!

# Wait for ngrok to be ready
echo -e "${YELLOW}Waiting for ngrok to establish tunnel...${NC}"
sleep 3

# Get public URL from ngrok API
MAX_RETRIES=10
RETRY_COUNT=0
PUBLIC_URL=""

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    PUBLIC_URL=$(curl -s http://127.0.0.1:4040/api/tunnels 2>/dev/null | \
        python3 -c "import sys, json; data = json.load(sys.stdin); print(data['tunnels'][0]['public_url'] if data.get('tunnels') else '')" 2>/dev/null || echo "")
    
    if [ -n "$PUBLIC_URL" ]; then
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    sleep 1
done

if [ -z "$PUBLIC_URL" ]; then
    echo -e "${RED}Error: Failed to get ngrok public URL.${NC}"
    echo -e "${YELLOW}Check ngrok status at: http://127.0.0.1:4040${NC}"
    cleanup
    exit 1
fi

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}   🌐 Public URL Ready!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "  ${CYAN}Public URL:${NC}"
echo -e "  ${BLUE}${PUBLIC_URL}${NC}"
echo ""

if [ -n "$LATEST_NAME" ]; then
    echo -e "  ${CYAN}Latest Report:${NC}"
    echo -e "  ${BLUE}${PUBLIC_URL}/${LATEST_NAME}${NC}"
fi

echo ""
echo -e "  ${CYAN}Local URL:${NC}"
echo -e "  ${BLUE}http://localhost:${PORT}${NC}"
echo ""
echo -e "  ${CYAN}Ngrok Dashboard:${NC}"
echo -e "  ${BLUE}http://127.0.0.1:4040${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Keep script running
wait $NGROK_PID 2>/dev/null || wait $SERVER_PID 2>/dev/null || true
