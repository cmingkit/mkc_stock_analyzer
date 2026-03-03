#!/bin/bash
# Stock Analyzer Cron Wrapper Script
# Usage: ./run_analyzer.sh [daily|alerts|weekly]

set -e

MODE=${1:-daily}
PROJECT_ROOT="/Users/mkc/.openclaw/workspace/stock_analyzer"
VENV_PYTHON="$PROJECT_ROOT/venv/bin/python"
MAIN_SCRIPT="$PROJECT_ROOT/src/main.py"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/cron_$(date +%Y%m%d).log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Log start
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting $MODE analysis" >> "$LOG_FILE"

# Run analyzer with PYTHONPATH set
cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT"
"$VENV_PYTHON" "$MAIN_SCRIPT" --mode "$MODE" >> "$LOG_FILE" 2>&1

# Log completion
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Completed $MODE analysis" >> "$LOG_FILE"
echo "---" >> "$LOG_FILE"
