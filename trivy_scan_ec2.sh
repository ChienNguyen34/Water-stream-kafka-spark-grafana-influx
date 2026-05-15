#!/bin/bash
# trivy_scan_ec2.sh — Scan Docker images trên EC2 bằng Trivy
# Chạy trước khi docker compose up để kiểm tra bảo mật
#
# Usage:
#   chmod +x ~/batadal/trivy_scan_ec2.sh
#   ~/batadal/trivy_scan_ec2.sh

set -euo pipefail

TRIVY_IMAGE="aquasec/trivy:0.61.0"
SEVERITY="HIGH,CRITICAL"
REPORT_PATH="$HOME/batadal/trivy_report.txt"

IMAGES=(
    "confluentinc/cp-kafka:8.1.2"
    "influxdb:2"
    "grafana/grafana:13.0.1"
)

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ── Init report ───────────────────────────────────────────────────────────────
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
cat > "$REPORT_PATH" <<EOF
================================================================
  Trivy Security Scan Report (EC2)
  Date    : $TIMESTAMP
  Severity: $SEVERITY
================================================================
EOF

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}  Trivy Security Scan — EC2${NC}"
echo -e "${CYAN}  Date    : $TIMESTAMP${NC}"
echo -e "${CYAN}  Severity: $SEVERITY${NC}"
echo -e "${CYAN}================================================================${NC}"

# ── Pull Trivy once ───────────────────────────────────────────────────────────
echo -e "\n${YELLOW}Pulling Trivy image...${NC}"
docker pull "$TRIVY_IMAGE" --quiet
echo -e "${GREEN}Trivy ready.${NC}"

# ── Scan ─────────────────────────────────────────────────────────────────────
FOUND_CRITICAL=0
declare -A RESULTS

for IMAGE in "${IMAGES[@]}"; do
    echo -e "\n${CYAN}--- Scanning: $IMAGE ---${NC}"
    echo -e "\n$(printf '%.0s-' {1..60})\nImage: $IMAGE\n$(printf '%.0s-' {1..60})" >> "$REPORT_PATH"

    OUTPUT=$(docker run --rm \
        -v /var/run/docker.sock:/var/run/docker.sock \
        "$TRIVY_IMAGE" image \
        --severity "$SEVERITY" \
        --no-progress \
        --quiet \
        "$IMAGE" 2>&1) || true

    echo "$OUTPUT" >> "$REPORT_PATH"

    if echo "$OUTPUT" | grep -q "CRITICAL"; then
        echo -e "${RED}[FAIL] CRITICAL vulnerability found in: $IMAGE${NC}"
        RESULTS[$IMAGE]="FAIL"
        FOUND_CRITICAL=1
    else
        echo -e "${GREEN}[PASS] No CRITICAL vulnerabilities: $IMAGE${NC}"
        RESULTS[$IMAGE]="PASS"
    fi
done

# ── Summary ───────────────────────────────────────────────────────────────────
echo -e "\n${CYAN}================================================================${NC}"
echo -e "${CYAN}  Summary${NC}"
echo -e "${CYAN}================================================================${NC}"
{
    echo ""
    echo "$(printf '%.0s=' {1..60})"
    echo "SUMMARY"
    echo "$(printf '%.0s=' {1..60})"
} >> "$REPORT_PATH"

for IMAGE in "${IMAGES[@]}"; do
    STATUS="${RESULTS[$IMAGE]}"
    if [ "$STATUS" = "PASS" ]; then
        echo -e "  ${GREEN}[PASS]${NC} $IMAGE"
    else
        echo -e "  ${RED}[FAIL]${NC} $IMAGE"
    fi
    echo "  [$STATUS] $IMAGE" >> "$REPORT_PATH"
done

echo -e "\nReport saved to: $REPORT_PATH"
echo "" >> "$REPORT_PATH"
echo "Report saved to: $REPORT_PATH" >> "$REPORT_PATH"

# ── Exit ──────────────────────────────────────────────────────────────────────
if [ $FOUND_CRITICAL -eq 1 ]; then
    echo -e "\n${RED}[!] CRITICAL vulnerabilities found. Review report before proceeding.${NC}"
    exit 1
else
    echo -e "\n${GREEN}[OK] All images passed. Safe to run docker compose up.${NC}"
    exit 0
fi
