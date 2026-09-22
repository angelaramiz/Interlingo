# release.ps1 — Pipeline unificado Interlingo: build → deploy → DB → verify
#
# Uso:
#   ./release.ps1 -VersionCode 2 -VersionName "0.2.0" -ServerUrl "https://interlingo-api.onrender.com"
#   ./release.ps1 -VersionCode 2 -VersionName "0.2.0" -ServerUrl "..." -KeystorePassword "xxx" -KeyPassword "xxx"
#   ./release.ps1 -VersionCode 2 -VersionName "0.2.0" -BuildType debug
#   ./release.ps1 -VersionCode 2 -VersionName "0.2.0" -SkipBuild   # APK ya compilado
#
# Requisitos: keystore en android/keystore/ para release (ver android/keystore/README.md).
# Las passwords NUNCA van al repo: se pasan por parámetro en cada ejecución.

param(
    [Parameter(Mandatory=$true)]
    [int]$VersionCode,

    [Parameter(Mandatory=$true)]
    [string]$VersionName,

    [string]$ServerUrl = "",

    [ValidateSet("release", "debug")]
    [string]$BuildType = "release",

    [switch]$SkipBuild,

    [string]$KeystorePath = "android/keystore/lenglearning-release.jks",
    [string]$KeystorePassword = "",
    [string]$KeyAlias = "lenglearning",
    [string]$KeyPassword = ""
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$ApkName = "interlingo.apk"
$DbKey = "app_version"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "═══ $Message ═══" -ForegroundColor Cyan
}

function Write-Ok {
    param([string]$Message)
    Write-Host "  OK $Message" -ForegroundColor Green
}

function Write-Fail {
    param([string]$Message)
    Write-Host "  FALLO $Message" -ForegroundColor Red
}

# ─── Paso 1: Build ───
$apkPath = ""
if (-not $SkipBuild) {
    Write-Step "1/4 BUILD ($BuildType)"
    $env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"
    $env:GRADLE_USER_HOME = "D:\gradle-home"

    $gradleArgs = @(":composeApp:assembleRelease")
    if ($BuildType -eq "debug") {
        $gradleArgs = @(":composeApp:assembleDebug")
    }
    $gradleArgs += "`"-PappVersionCode=$VersionCode`""
    $gradleArgs += "`"-PappVersionName=$VersionName`""
    if ($ServerUrl) {
        $gradleArgs += "`"-PserverUrl=$ServerUrl`""
    }

    if ($BuildType -eq "release") {
        if (-not (Test-Path (Join-Path $Root $KeystorePath))) {
            Write-Fail "Keystore no encontrado: $KeystorePath (ver android/keystore/README.md)"
            exit 1
        }
        if (-not $KeystorePassword -or -not $KeyPassword) {
            Write-Fail "Release requiere -KeystorePassword y -KeyPassword"
            exit 1
        }
        $ksAbs = (Resolve-Path (Join-Path $Root $KeystorePath)).Path
        $gradleArgs += "`"-Pandroid.injected.signing.store.file=$ksAbs`""
        $gradleArgs += "`"-Pandroid.injected.signing.store.password=$KeystorePassword`""
        $gradleArgs += "`"-Pandroid.injected.signing.key.alias=$KeyAlias`""
        $gradleArgs += "`"-Pandroid.injected.signing.key.password=$KeyPassword`""
    }

    Push-Location (Join-Path $Root "android")
    try {
        & .\gradlew.bat @gradleArgs --no-daemon
        if ($LASTEXITCODE -ne 0) {
            Write-Fail "gradle $gradleArgs falló"
            exit 1
        }
    } finally {
        Pop-Location
    }

    $suffix = if ($BuildType -eq "release") { "release" } else { "debug" }
    $apk = Get-ChildItem -Path (Join-Path $Root "android/composeApp/build/outputs/apk/$suffix/composeApp-$suffix.apk") -ErrorAction SilentlyContinue
    if (-not $apk) {
        Write-Fail "No se encontró el APK en outputs/apk/$suffix"
        exit 1
    }
    $apkPath = $apk.FullName
    Write-Ok "APK: $($apk.Name) ($([math]::Round($apk.Length / 1MB, 1)) MB)"
} else {
    Write-Step "1/4 BUILD (omitido, -SkipBuild)"
    $suffix = if ($BuildType -eq "release") { "release" } else { "debug" }
    $apk = Get-ChildItem -Path (Join-Path $Root "android/composeApp/build/outputs/apk/$suffix/composeApp-$suffix.apk") -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $apk) {
        Write-Fail "No hay APK existente en outputs/apk/$suffix"
        exit 1
    }
    $apkPath = $apk.FullName
    Write-Ok "APK existente: $($apk.Name)"
}

# ─── Paso 2: Deploy (copiar al backend/static) ───
Write-Step "2/4 DEPLOY"
$staticDir = Join-Path $Root "backend/static"
if (-not (Test-Path $staticDir)) {
    New-Item -ItemType Directory -Path $staticDir -Force | Out-Null
}
Copy-Item $apkPath (Join-Path $staticDir $ApkName) -Force
Write-Ok "Copiado a backend/static/$ApkName"

# ─── Paso 3: DB (SQLite app_versions) ───
Write-Step "3/4 DB"
$dbPath = Join-Path $Root "backend/interlingo.db"
$py = Join-Path $Root "backend/.venv/Scripts/python.exe"
if (-not (Test-Path $py)) {
    $py = "python"
}
& $py (Join-Path $Root "backend/scripts/set_version.py") $dbPath $DbKey $VersionCode $VersionName "/static/$ApkName"
if ($LASTEXITCODE -ne 0) {
    Write-Fail "set_version.py falló"
    exit 1
}
Write-Ok "app_versions[$DbKey] = v$VersionName (code=$VersionCode)"

# ─── Paso 4: Verify ───
Write-Step "4/4 VERIFY"
if (-not $ServerUrl) {
    Write-Host "  Omitido (sin -ServerUrl). Verificar manual: GET /api/app-version" -ForegroundColor Yellow
} else {
    try {
        $r = Invoke-RestMethod -Uri "$($ServerUrl.TrimEnd('/'))/api/app-version" -Method GET -TimeoutSec 15
        if ($r.versionCode -eq $VersionCode) {
            Write-Ok "Endpoint devuelve v$($r.versionName) (code=$($r.versionCode))"
        } else {
            Write-Host "  Aviso: endpoint devuelve code=$($r.versionCode), esperado $VersionCode" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  Aviso: no se pudo verificar endpoint: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Release v$VersionName (code=$VersionCode) completado." -ForegroundColor Green
