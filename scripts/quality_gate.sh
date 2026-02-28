#!/bin/bash
# =============================================================================
# Code Quality Gate - Standalone CI Script
# =============================================================================
# Usage:
#   ./scripts/quality_gate.sh <file_or_repo_url> [threshold]
#
# Examples:
#   ./scripts/quality_gate.sh ./my_code.py 7.0
#   ./scripts/quality_gate.sh https://github.com/user/repo 6.0
#
# Environment Variables:
#   CQG_API_URL   - API base URL (default: http://localhost:8000)
#   CQG_THRESHOLD - Quality threshold (default: 6.0)
#
# Exit codes:
#   0 - Quality gate passed
#   1 - Quality gate failed
#   2 - Error (API unreachable, invalid input, etc.)
# =============================================================================

set -euo pipefail

# Configuration
API_URL="${CQG_API_URL:-http://localhost:8000}"
INPUT="${1:-}"
THRESHOLD="${2:-${CQG_THRESHOLD:-6.0}}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ---------- Helper Functions ----------

usage() {
    echo "Usage: $0 <file_path_or_github_url> [threshold]"
    echo ""
    echo "Examples:"
    echo "  $0 ./my_code.py 7.0"
    echo "  $0 https://github.com/user/repo 6.0"
    exit 2
}

check_api() {
    if ! curl -s "${API_URL}/health" | grep -q "healthy"; then
        echo -e "${RED}ERROR: API is not reachable at ${API_URL}${NC}"
        echo "Start the API with: make docker-run  OR  make run"
        exit 2
    fi
}

analyze_file() {
    local file_path="$1"

    if [ ! -f "$file_path" ]; then
        echo -e "${RED}ERROR: File not found: ${file_path}${NC}"
        exit 2
    fi

    echo -e "${YELLOW}Analyzing file: ${file_path}${NC}"
    echo "Threshold: ${THRESHOLD}"
    echo "API: ${API_URL}"
    echo "---"

    RESPONSE=$(curl -s -X POST "${API_URL}/api/v1/analyze/file" \
        -F "file=@${file_path}" \
        -F "threshold=${THRESHOLD}")

    print_report "$RESPONSE"
}

analyze_github() {
    local repo_url="$1"

    echo -e "${YELLOW}Analyzing GitHub repo: ${repo_url}${NC}"
    echo "Threshold: ${THRESHOLD}"
    echo "API: ${API_URL}"
    echo "---"

    RESPONSE=$(curl -s -X POST "${API_URL}/api/v1/analyze/github" \
        -H "Content-Type: application/json" \
        -d "{\"repo_url\": \"${repo_url}\", \"threshold\": ${THRESHOLD}}")

    print_report "$RESPONSE"
}

print_report() {
    local response="$1"

    # Pretty print the report
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"

    echo ""
    echo "============================================"

    # Extract pass/fail
    PASSED=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('passed', 'unknown'))" 2>/dev/null)
    SCORE=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('overall_score', 'N/A'))" 2>/dev/null)

    if [ "$PASSED" = "True" ]; then
        echo -e "${GREEN}QUALITY GATE PASSED${NC} | Score: ${SCORE}/10 (threshold: ${THRESHOLD})"
        exit 0
    elif [ "$PASSED" = "False" ]; then
        echo -e "${RED}QUALITY GATE FAILED${NC} | Score: ${SCORE}/10 (threshold: ${THRESHOLD})"
        exit 1
    else
        echo -e "${RED}ERROR: Could not parse API response${NC}"
        echo "$response"
        exit 2
    fi
}

# ---------- Main ----------

if [ -z "$INPUT" ]; then
    usage
fi

check_api

# Auto-detect: file or GitHub URL
if [[ "$INPUT" == https://github.com/* ]]; then
    analyze_github "$INPUT"
else
    analyze_file "$INPUT"
fi
