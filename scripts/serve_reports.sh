#!/bin/bash
#
# serve_reports.sh - Start a local HTTP server for HTML reports
#
# Usage:
#   ./scripts/serve_reports.sh [PORT]
#
# Examples:
#   ./scripts/serve_reports.sh           # Uses default port 8080
#   ./scripts/serve_reports.sh 3000      # Uses port 3000
#
# Access reports at: http://localhost:8080
#

set -e

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORTS_DIR="${PROJECT_ROOT}/reports/html"
DEFAULT_PORT=8080
PORT="${1:-$DEFAULT_PORT}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Stock Analyzer - Report Server${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if reports directory exists
if [ ! -d "$REPORTS_DIR" ]; then
    echo -e "${RED}Error: Reports directory not found: ${REPORTS_DIR}${NC}"
    echo -e "${YELLOW}Run the analyzer first to generate reports.${NC}"
    exit 1
fi

# Count available reports
REPORT_COUNT=$(find "$REPORTS_DIR" -name "*.html" -type f | wc -l | tr -d ' ')
if [ "$REPORT_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}Warning: No HTML reports found in ${REPORTS_DIR}${NC}"
    echo -e "${YELLOW}Run the analyzer first to generate reports.${NC}"
else
    echo -e "${GREEN}Found ${REPORT_COUNT} HTML report(s)${NC}"
fi

# Get latest report
LATEST_REPORT=$(ls -t "${REPORTS_DIR}"/*.html 2>/dev/null | head -1)
if [ -n "$LATEST_REPORT" ]; then
    LATEST_NAME=$(basename "$LATEST_REPORT")
    echo -e "${GREEN}Latest report: ${LATEST_NAME}${NC}"
fi

echo ""
echo -e "${BLUE}Starting HTTP server...${NC}"
echo -e "  Directory: ${REPORTS_DIR}"
echo -e "  Port: ${PORT}"
echo ""
echo -e "${GREEN}Access your reports at:${NC}"
echo -e "  ${BLUE}http://localhost:${PORT}${NC}"
if [ -n "$LATEST_REPORT" ]; then
    echo -e "  ${BLUE}http://localhost:${PORT}/${LATEST_NAME}${NC}"
fi
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Change to reports directory and start server
cd "$REPORTS_DIR"
python3 -m http.server "$PORT"
