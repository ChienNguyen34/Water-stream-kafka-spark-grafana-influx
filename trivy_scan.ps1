<#
.SYNOPSIS
    Scan Docker images dùng trong docker-compose.yml bằng Trivy.
    Fail nếu tìm thấy lỗ hổng mức CRITICAL.
    Kết quả lưu vào tst\trivy_report.txt

.USAGE
    .\trivy_scan.ps1

.NOTES
    Yêu cầu: Docker Desktop đang chạy.
    Trivy chạy qua Docker image aquasec/trivy:0.61.0 — không cần cài native.
#>

$ErrorActionPreference = "Continue"   # Cho phép stderr từ docker (Trivy INFO logs) không crash script
Set-StrictMode -Version Latest

# ── Cấu hình ──────────────────────────────────────────────────────────────────
$TRIVY_IMAGE    = "aquasec/trivy:0.61.0"
$REPORT_PATH    = Join-Path $PSScriptRoot "tst\trivy_report.txt"
$SEVERITY       = "HIGH,CRITICAL"

# ── Danh sách images cần scan ─────────────────────────────────────────────────
#
# Pre-built images (pull từ Docker Hub):
#   - Scan trực tiếp qua tên image
#
# Custom-built images (build: trong docker-compose):
#   - spark-master/worker/driver và generator được build LOCAL
#   - Trivy scan được local image sau khi docker-compose build đã chạy
#   - Tên image local = "<compose_project>-<service>" (mặc định: "bigdata-<service>")
#   - Base image của Spark (apache/spark:3.5.8-java17-python3) cũng được scan riêng
#     vì đây là layer có nhiều CVE nhất (JDK, Python packages)
#
$PREBUILT_IMAGES = @(
    "confluentinc/cp-kafka:8.1.2",
    "influxdb:2",
    "grafana/grafana:13.0.1",
    "apache/spark:3.5.8-java17-python3"   # base image của spark-master/worker/driver
)

# Local images sau docker-compose build (chỉ scan nếu đã build)
$LOCAL_IMAGES = @(
    "bigdata-spark-master",
    "bigdata-spark-worker",
    "bigdata-spark-driver",
    "bigdata-generator"
)

$IMAGES_TO_SCAN = $PREBUILT_IMAGES

# ── Helper ─────────────────────────────────────────────────────────────────────
function Write-Section([string]$title) {
    $line = "=" * 60
    Write-Host "`n$line" -ForegroundColor Cyan
    Write-Host "  $title" -ForegroundColor Cyan
    Write-Host "$line" -ForegroundColor Cyan
}

function Append-Report([string]$text) {
    Add-Content -Path $REPORT_PATH -Value $text -Encoding UTF8
}

# ── Init report file ───────────────────────────────────────────────────────────
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$header = @"
================================================================
  Trivy Security Scan Report
  Date   : $timestamp
  Severity Filter: $SEVERITY
================================================================
"@
Set-Content -Path $REPORT_PATH -Value $header -Encoding UTF8
Write-Host $header

# ── Thêm local images nếu đã được build ──────────────────────────────────────
Write-Host "`nChecking for locally built images..." -ForegroundColor Yellow
foreach ($localImage in $LOCAL_IMAGES) {
    $exists = docker image inspect $localImage 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Found local image: $localImage" -ForegroundColor Green
        $IMAGES_TO_SCAN += $localImage
    } else {
        Write-Host "  Skip (not built yet): $localImage" -ForegroundColor DarkGray
    }
}

# ── Pull Trivy image once ──────────────────────────────────────────────────────
Write-Section "Pulling Trivy image: $TRIVY_IMAGE"
docker pull $TRIVY_IMAGE | Out-Null
Write-Host "Trivy ready." -ForegroundColor Green

# ── Scan each image ────────────────────────────────────────────────────────────
$foundCritical  = $false
$scanResults    = @{}

foreach ($image in $IMAGES_TO_SCAN) {
    Write-Section "Scanning: $image"
    Append-Report "`n$("-" * 60)`nImage: $image`n$("-" * 60)"

    # 2>&1 hợp nhất stderr (Trivy INFO logs) vào stdout
    $output = docker run --rm `
        -v //var/run/docker.sock:/var/run/docker.sock `
        $TRIVY_IMAGE image `
        --severity $SEVERITY `
        --no-progress `
        --quiet `
        --exit-code 0 `
        $image 2>&1

    $outputStr = ($output | ForEach-Object { "$_" }) -join "`n"
    Append-Report $outputStr

    $hasCritical = $outputStr -match "CRITICAL"
    $scanResults[$image] = -not $hasCritical

    if ($hasCritical) {
        Write-Host "[FAIL] CRITICAL vulnerability found in: $image" -ForegroundColor Red
        $foundCritical = $true
    } else {
        Write-Host "[PASS] No CRITICAL vulnerabilities: $image" -ForegroundColor Green
    }
}

# ── Summary ────────────────────────────────────────────────────────────────────
Write-Section "Scan Summary"
Append-Report "`n$("=" * 60)`nSUMMARY`n$("=" * 60)"

foreach ($image in $IMAGES_TO_SCAN) {
    $status = if ($scanResults[$image]) { "PASS" } else { "FAIL (CRITICAL found)" }
    $line   = "  [$status] $image"
    Write-Host $line
    Append-Report $line
}

$reportLine = "`nReport saved to: $REPORT_PATH"
Write-Host $reportLine
Append-Report $reportLine

# ── Exit code ─────────────────────────────────────────────────────────────────
if ($foundCritical) {
    Write-Host "`n[SCAN FAILED] CRITICAL vulnerabilities detected. Review: $REPORT_PATH" -ForegroundColor Red
    exit 1
} else {
    Write-Host "`n[SCAN PASSED] No CRITICAL vulnerabilities found across all images." -ForegroundColor Green
    exit 0
}
