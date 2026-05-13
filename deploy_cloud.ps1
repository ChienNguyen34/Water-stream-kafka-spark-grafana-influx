<#
.SYNOPSIS
    Deploy Kafka + InfluxDB + Grafana len EC2, sau do chay local services tro vao Cloud.

.USAGE
    .\deploy_cloud.ps1

.NOTES
    Yeu cau: file batadal-key_new.pem nam trong d:\Workspace\Bigdata\
#>

$EC2_IP     = "18.138.224.73"
$EC2_USER   = "ubuntu"
$KEY_FILE   = "$PSScriptRoot\batadal-key_new.pem"
$SSH_ARGS   = @("-i", $KEY_FILE, "-o", "StrictHostKeyChecking=no")
$SSH_TARGET = "$EC2_USER@$EC2_IP"

function Invoke-SSH([string]$cmd) {
    Write-Host "  >> $cmd" -ForegroundColor DarkGray
    & ssh @SSH_ARGS $SSH_TARGET $cmd
}

function Invoke-SCP([string]$src, [string]$dst, [switch]$Recurse) {
    if ($Recurse) {
        & scp @SSH_ARGS -r $src "${SSH_TARGET}:${dst}"
    } else {
        & scp @SSH_ARGS $src "${SSH_TARGET}:${dst}"
    }
}

function Section([string]$title) {
    Write-Host "`n================================================================" -ForegroundColor Cyan
    Write-Host "  $title" -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor Cyan
}

# -- Kiem tra key file --
if (-not (Test-Path $KEY_FILE)) {
    Write-Host "[ERROR] Khong tim thay $KEY_FILE" -ForegroundColor Red
    exit 1
}

# -- Buoc 1: Test SSH --
Section "Buoc 1: Test SSH connection toi EC2"
$result = (& ssh @SSH_ARGS $SSH_TARGET "echo OK") 2>&1
$resultStr = ($result | Out-String).Trim()
if ($resultStr -notlike "*OK*") {
    Write-Host "[ERROR] SSH that bai: $resultStr" -ForegroundColor Red
    exit 1
}
Write-Host "  SSH OK" -ForegroundColor Green

# -- Buoc 2: Cai Docker --
Section "Buoc 2: Cai Docker tren EC2"
$dockerVer = (& ssh @SSH_ARGS $SSH_TARGET "docker --version 2>/dev/null || echo NOTFOUND") 2>&1
if (($dockerVer | Out-String) -like "*NOTFOUND*") {
    Write-Host "  Cai dat Docker..." -ForegroundColor Yellow
    Invoke-SSH "sudo apt-get update -qq"
    Invoke-SSH "sudo apt-get install -y -qq ca-certificates curl"
    Invoke-SSH "sudo install -m 0755 -d /etc/apt/keyrings"
    Invoke-SSH "sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc"
    Invoke-SSH "sudo chmod a+r /etc/apt/keyrings/docker.asc"
    & ssh @SSH_ARGS $SSH_TARGET '. /etc/os-release && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $VERSION_CODENAME stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null'
    Invoke-SSH "sudo apt-get update -qq"
    Invoke-SSH "sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin"
    Invoke-SSH "sudo usermod -aG docker ubuntu"
    Write-Host "  Docker installed." -ForegroundColor Green
} else {
    Write-Host "  Docker da co: $($dockerVer | Out-String)" -ForegroundColor Green
}

# -- Buoc 3: Upload files --
Section "Buoc 3: Upload files len EC2"
Invoke-SSH "mkdir -p ~/batadal"

Write-Host "  Uploading docker-compose.cloud.yml..." -ForegroundColor Yellow
Invoke-SCP "$PSScriptRoot\docker-compose.cloud.yml" "~/batadal/docker-compose.yml"

Write-Host "  Uploading grafana/..." -ForegroundColor Yellow
Invoke-SCP "$PSScriptRoot\grafana" "~/batadal/" -Recurse

Write-Host "  Upload done." -ForegroundColor Green

# -- Buoc 4: Start services --
Section "Buoc 4: Start Kafka + InfluxDB + Grafana tren EC2"
& ssh @SSH_ARGS $SSH_TARGET "cd ~/batadal && EC2_PUBLIC_IP=$EC2_IP docker compose up -d"

Write-Host "  Waiting 30s for services to start..." -ForegroundColor DarkGray
Start-Sleep -Seconds 30

& ssh @SSH_ARGS $SSH_TARGET "cd ~/batadal && docker compose ps"

# -- Buoc 5: Health check --
Section "Buoc 5: Health check"
Write-Host "  InfluxDB health..." -ForegroundColor Yellow
try {
    $resp = Invoke-RestMethod "http://${EC2_IP}:8086/health" -TimeoutSec 10
    Write-Host "  InfluxDB: $($resp.status)" -ForegroundColor Green
} catch {
    Write-Host "  InfluxDB: chua ready" -ForegroundColor Yellow
}

Write-Host "  Grafana health..." -ForegroundColor Yellow
try {
    $resp = Invoke-RestMethod "http://${EC2_IP}:3000/api/health" -TimeoutSec 10
    Write-Host "  Grafana: $($resp.database)" -ForegroundColor Green
} catch {
    Write-Host "  Grafana: chua ready" -ForegroundColor Yellow
}

# -- Summary --
Section "Deploy hoan tat!"
Write-Host "  Grafana  : http://${EC2_IP}:3000  (admin / adminpassword)" -ForegroundColor Cyan
Write-Host "  InfluxDB : http://${EC2_IP}:8086" -ForegroundColor Cyan
Write-Host "  Kafka    : ${EC2_IP}:9092" -ForegroundColor Cyan
