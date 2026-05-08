<#
.SYNOPSIS
  Windows / PowerShell 替代方案：与 w2/db_query/Makefile 目标一致（未安装 GNU make 时使用）。

.EXAMPLE
  cd w2/db_query
  .\db_query.ps1 help
  .\db_query.ps1 install
  .\db_query.ps1 dev-backend
  $env:PORT = "9000"; .\db_query.ps1 dev-backend
#>
param(
    [Parameter(Position = 0)]
    [string]$Target = "help",
    [string]$ListenHost = $(if ($env:HOST) { $env:HOST } else { "0.0.0.0" }),
    [string]$Port = $(if ($env:PORT) { $env:PORT } else { "8000" })
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"

function Invoke-Backend {
    param([scriptblock]$Action)
    Push-Location $Backend
    try { & $Action } finally { Pop-Location }
}

function Invoke-Frontend {
    param([scriptblock]$Action)
    Push-Location $Frontend
    try { & $Action } finally { Pop-Location }
}

switch ($Target) {
    "help" {
        Write-Host "db_query.ps1 <target>   (PowerShell, same targets as Makefile)"
        Write-Host "  install             uv sync + npm install"
        Write-Host "  install-backend     uv sync --all-groups"
        Write-Host "  install-frontend    npm install"
        Write-Host "  sync-backend / sync same as install-backend"
        Write-Host '  dev-backend         uv run uvicorn; env HOST, PORT (default 8000)'
        Write-Host "  dev-frontend        vite dev"
        Write-Host "  lint / lint-backend / lint-frontend"
        Write-Host "  test-backend"
        Write-Host "  build-frontend"
        Write-Host "  openapi-json        GET openapi JSON - backend must be running"
        Write-Host "  clean-backend-cache"
        Write-Host "  audit-frontend      npm audit (run in frontend, where lockfile lives)"
        Write-Host "  audit-fix-frontend  npm audit fix (no --force)"
        Write-Host ""
        Write-Host "After npm install, vulnerability summary is advisory; install still succeeds."
        Write-Host "Install GNU make: scoop install make, or use Git Bash."
    }
    "install" {
        & (Join-Path $Root "db_query.ps1") install-backend
        & (Join-Path $Root "db_query.ps1") install-frontend
    }
    { $_ -in "install-backend", "sync-backend", "sync" } {
        Invoke-Backend { uv sync --all-groups }
    }
    "install-frontend" {
        Invoke-Frontend { npm install }
    }
    "dev-backend" {
        Invoke-Backend { uv run uvicorn db_query.main:app --reload --host $ListenHost --port $Port }
    }
    "dev-frontend" {
        Invoke-Frontend { npm run dev }
    }
    "lint" {
        & (Join-Path $Root "db_query.ps1") lint-backend
        & (Join-Path $Root "db_query.ps1") lint-frontend
    }
    "lint-backend" {
        Invoke-Backend { uv run ruff check src tests }
    }
    "lint-frontend" {
        Invoke-Frontend { npm run lint }
    }
    "test-backend" {
        Invoke-Backend { uv run pytest }
    }
    "build-frontend" {
        Invoke-Frontend { npm run build }
    }
    "openapi-json" {
        $uri = "http://127.0.0.1:$Port/openapi.json"
        $r = Invoke-WebRequest -Uri $uri -UseBasicParsing
        Write-Output $r.Content
    }
    "clean-backend-cache" {
        foreach ($p in @(
                (Join-Path $Backend "src/db_query/__pycache__"),
                (Join-Path $Backend "tests/__pycache__"),
                (Join-Path $Backend ".pytest_cache"),
                (Join-Path $Backend ".ruff_cache")
            )) {
            if (Test-Path $p) { Remove-Item -Recurse -Force $p }
        }
        Write-Host "cleaned under backend/"
    }
    "audit-frontend" {
        Invoke-Frontend { npm audit }
    }
    "audit-fix-frontend" {
        Invoke-Frontend { npm audit fix }
    }
    default {
        Write-Error "Unknown target: $Target. Run: .\db_query.ps1 help"
    }
}
