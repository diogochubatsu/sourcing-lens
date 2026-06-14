#!/bin/bash
# Daily Pipeline Runner
# Runs the full pipeline and logs output
# Usage: Add to crontab: 0 9 * * * /home/hermeshideki/arbt.ly/scripts/daily_pipeline.sh

set -e

PROJECT_DIR="/home/hermeshideki/arbt.ly"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/pipeline_$(date +%Y%m%d).log"

# Create logs directory
mkdir -p "$LOG_DIR"

# Activate venv
source "$PROJECT_DIR/.venv/bin/activate"

echo "========================================" >> "$LOG_FILE"
echo "Pipeline started: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Run pipeline
cd "$PROJECT_DIR"
python3 scripts/run_pipeline.py --all >> "$LOG_FILE" 2>&1

echo "========================================" >> "$LOG_FILE"
echo "Pipeline finished: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Cleanup old logs (keep 30 days)
find "$LOG_DIR" -name "pipeline_*.log" -mtime +30 -delete 2>/dev/null || true
