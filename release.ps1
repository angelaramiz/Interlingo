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

    [string]$KeystorePath = "android/keystore/interlingo-release.jks",
    [string]$KeystorePassword = "",
    [string]$KeyAlias = "interlingo",
    [string]$KeyPassword = "",

    [string]$GithubRepo = "angelaramiz/Interlingo",

    [string]$RenderHookUrl = "",

    [switch]$KeepLocalApk
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

# ─── Paso 2: Deploy (GitHub Release con el APK) ───
Write-Step "2/4 DEPLOY (GitHub Release)"
$tag = "v$VersionName"
$assetPath = Join-Path $Root "backend/static/$ApkName"
Copy-Item $apkPath $assetPath -Force
Write-Ok "APK listo para release: $ApkName ($([math]::Round((Get-Item $assetPath).Length / 1MB, 1)) MB)"

$prevEAP = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$existing = & gh release view $tag --repo $GithubRepo 2>&1
$tagExists = ($LASTEXITCODE -eq 0)
$ErrorActionPreference = $prevEAP
if ($tagExists) {
    Write-Host "  Release $tag existe, subiendo asset..." -ForegroundColor Gray
    & gh release upload $tag $assetPath --repo $GithubRepo --clobber
} else {
    Write-Host "  Creando release $tag..." -ForegroundColor Gray
    & gh release create $tag $assetPath --repo $GithubRepo --title "Interlingo v$VersionName" --notes "Release v$VersionName (code=$VersionCode)"
}
if ($LASTEXITCODE -ne 0) {
    Write-Fail "gh release falló"
    exit 1
}
$apkUrl = "https://github.com/$GithubRepo/releases/download/$tag/$ApkName"
Write-Ok "APK publicado: $apkUrl"

# ─── Paso 3: Versión (version.json + SQLite local + push) ───
Write-Step "3/4 VERSION"
$versionJson = @{ versionCode = $VersionCode; versionName = $VersionName; apkUrl = $apkUrl } | ConvertTo-Json -Compress
Set-Content (Join-Path $Root "backend/static/version.json") $versionJson -NoNewline -Encoding utf8
Write-Ok "backend/static/version.json = $versionJson"

$dbPath = Join-Path $Root "backend/interlingo.db"
$py = Join-Path $Root "backend/.venv/Scripts/python.exe"
if (-not (Test-Path $py)) {
    $py = "python"
}
& $py (Join-Path $Root "backend/scripts/set_version.py") $dbPath $DbKey $VersionCode $VersionName $apkUrl
if ($LASTEXITCODE -ne 0) {
    Write-Fail "set_version.py falló"
    exit 1
}
Write-Ok "SQLite local actualizado (desarrollo)"

Push-Location $Root
try {
    git add backend/static/version.json
    $needsCommit = git status --short backend/static/version.json
    if ($needsCommit) {
        git commit -m "release v$VersionName (code=$VersionCode)" -- backend/static/version.json | Out-Null
        $prevEAP2 = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        git push origin main 2>&1 | Out-Null
        $pushOk = ($LASTEXITCODE -eq 0)
        $ErrorActionPreference = $prevEAP2
        if (-not $pushOk) {
            Write-Fail "git push falló"
            exit 1
        }
        Write-Ok "version.json publicado (Render redesplegará)"
    } else {
        Write-Ok "version.json sin cambios"
    }
} finally {
    Pop-Location
}

# ─── Paso 4: Deploy en Render + Verify ───
Write-Step "4/4 RENDER + VERIFY"
if ($RenderHookUrl) {
    try {
        Invoke-RestMethod -Uri $RenderHookUrl -Method POST -TimeoutSec 30 | Out-Null
        Write-Ok "Redeploy de Render disparado vía hook"
    } catch {
        Write-Host "  Aviso: el hook de Render falló: $($_.Exception.Message)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  Sin -RenderHookUrl: se confía en el autodeploy por push (más lento)" -ForegroundColor Gray
}
if (-not $ServerUrl) {
    Write-Host "  Omitido (sin -ServerUrl). Verificar manual: GET /api/app-version" -ForegroundColor Yellow
} else {
    $ok = $false
    for ($i = 1; $i -le 20; $i++) {
        Start-Sleep -Seconds 20
        try {
            $r = Invoke-RestMethod -Uri "$($ServerUrl.TrimEnd('/'))/api/app-version" -Method GET -TimeoutSec 15
            if ($r.versionCode -eq $VersionCode) {
                Write-Ok "Endpoint devuelve v$($r.versionName) (code=$($r.versionCode)) — intento $i"
                $ok = $true
                break
            }
            Write-Host "  Intento ${i}: endpoint en code=$($r.versionCode), esperando $VersionCode..." -ForegroundColor Gray
        } catch {
            Write-Host "  Intento ${i}: sin respuesta ($($_.Exception.Message))" -ForegroundColor Gray
        }
    }
    if (-not $ok) {
        Write-Host "  Aviso: Render aún no sirve la nueva versión (redeploy en curso). Reintenta en unos minutos." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Release v$VersionName (code=$VersionCode) completado." -ForegroundColor Green
Write-Host "  APK: $apkUrl" -ForegroundColor Gray
if (-not $KeepLocalApk) {
    Remove-Item $assetPath -Force -ErrorAction SilentlyContinue
    Write-Host "  APK local eliminado. Vive en GitHub Releases." -ForegroundColor Gray
}
