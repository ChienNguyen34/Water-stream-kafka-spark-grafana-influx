<#
.SYNOPSIS
    Khởi động toàn bộ BATADAL pipeline và mở log viewer cho từng service.
    Yêu cầu: Docker Desktop đang chạy, Windows Terminal (wt) đã cài.

.USAGE
    .\start_pipeline.ps1

.NOTES
    Nếu không có Windows Terminal, script fallback sang Start-Process PowerShell.
#>

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# ── Bước 1: Fix ivy cache permissions (idempotent) ─────────────────────────────
Write-Host "[1/4] Fixing ivy cache permissions..." -ForegroundColor Yellow
docker run --rm `
    -v bigdata_ivy_cache:/tmp/.ivy2 `
    -u root apache/spark:3.5.8-java17-python3 `
    bash -c "mkdir -p /tmp/.ivy2/cache /tmp/.ivy2/jars && chmod -R 777 /tmp/.ivy2" `
    2>&1 | Out-Null
Write-Host "      Done." -ForegroundColor Green

# ── Bước 2: Khởi động infrastructure ──────────────────────────────────────────
Write-Host "[2/4] Starting infrastructure (kafka, influxdb, grafana)..." -ForegroundColor Yellow
docker-compose up -d kafka influxdb grafana
Write-Host "      Waiting for kafka + influxdb healthcheck..." -ForegroundColor DarkGray

$timeout = 90
$elapsed = 0
while ($elapsed -lt $timeout) {
    $kafkaHealth   = (docker inspect --format "{{.State.Health.Status}}" kafka   2>$null)
    $influxHealth  = (docker inspect --format "{{.State.Health.Status}}" influxdb 2>$null)
    if ($kafkaHealth -eq "healthy" -and $influxHealth -eq "healthy") { break }
    Start-Sleep -Seconds 5
    $elapsed += 5
    Write-Host "      kafka=$kafkaHealth  influxdb=$influxHealth  (${elapsed}s)" -ForegroundColor DarkGray
}
if ($elapsed -ge $timeout) {
    Write-Host "[ERROR] Healthcheck timeout sau ${timeout}s. Kiểm tra docker logs." -ForegroundColor Red
    exit 1
}
Write-Host "      kafka=healthy  influxdb=healthy" -ForegroundColor Green

# ── Bước 3: Khởi động Spark cluster + driver + generator ──────────────────────
Write-Host "[3/4] Starting spark-master, spark-workers, spark-driver, generator..." -ForegroundColor Yellow
docker-compose up -d spark-master spark-worker spark-worker-2
Start-Sleep -Seconds 5
docker-compose up -d spark-driver
docker-compose up -d generator
Write-Host "      All services started." -ForegroundColor Green

# ── Bước 4: Mở log viewers ────────────────────────────────────────────────────
Write-Host "[4/4] Opening log viewers..." -ForegroundColor Yellow

$wtAvailable = $null -ne (Get-Command wt -ErrorAction SilentlyContinue)

if ($wtAvailable) {
    # Windows Terminal: 1 cửa sổ với 4 tab
    Write-Host "      Using Windows Terminal (tabs)..." -ForegroundColor DarkGray
    wt `
        --title "spark-driver" `
        powershell -NoExit -Command "docker logs spark-driver -f" `; `
        new-tab --title "generator" `
        powershell -NoExit -Command "docker logs generator -f" `; `
        new-tab --title "kafka" `
        powershell -NoExit -Command "docker logs kafka -f" `; `
        new-tab --title "influxdb" `
        powershell -NoExit -Command "docker logs influxdb -f"
} else {
    # Fallback: mở 4 cửa sổ PowerShell riêng
    Write-Host "      Windows Terminal not found. Opening separate windows..." -ForegroundColor DarkGray
    $services = @(
        @{ Name = "spark-driver"; Color = "DarkBlue"  },
        @{ Name = "generator";   Color = "DarkGreen" },
        @{ Name = "kafka";       Color = "DarkRed"   },
        @{ Name = "influxdb";    Color = "DarkMagenta" }
    )
    foreach ($svc in $services) {
        Start-Process powershell -ArgumentList @(
            "-NoExit",
            "-Command",
            "`$host.UI.RawUI.WindowTitle = '$($svc.Name)'; docker logs $($svc.Name) -f"
        )
    }
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  Pipeline running!" -ForegroundColor Cyan
Write-Host "  Spark UI  : http://localhost:8090" -ForegroundColor Cyan
Write-Host "  Grafana   : http://localhost:3000  (admin / adminpassword)" -ForegroundColor Cyan
Write-Host "  InfluxDB  : http://localhost:8086" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Attacks appear ~3.5 min after generator starts (dataset04 row 1731+)" -ForegroundColor DarkYellow
