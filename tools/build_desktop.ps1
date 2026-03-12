param(
    [string]$PythonExe = ".\.venv\Scripts\python.exe",
    [string]$IsccExe = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    [switch]$SkipFrontend,
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Resolve-CommandPath {
    param([string]$Candidate)

    if ([System.IO.Path]::IsPathRooted($Candidate) -and (Test-Path $Candidate)) {
        return (Resolve-Path $Candidate).Path
    }

    $localCandidate = Join-Path $ProjectRoot $Candidate
    if (Test-Path $localCandidate) {
        return (Resolve-Path $localCandidate).Path
    }

    return (Get-Command $Candidate -ErrorAction Stop).Source
}

function Resolve-PythonFromLauncher {
    foreach ($version in @("-3.12", "-3.11", "-3.10", "")) {
        try {
            $args = @()
            if ($version) {
                $args += $version
            }
            $args += "-c"
            $args += "import sys; print(sys.executable)"
            $resolved = (& py @args 2>$null | Select-Object -First 1).Trim()
            if ($LASTEXITCODE -eq 0 -and $resolved -and (Test-Path $resolved)) {
                return $resolved
            }
        }
        catch {
        }
    }

    return $null
}

function Resolve-PythonFromKnownLocations {
    $candidates = @(
        (Join-Path $ProjectRoot ".desktop-venv\Scripts\python.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python311\python.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python310\python.exe"),
        (Join-Path $env:ProgramFiles "Python312\python.exe"),
        (Join-Path $env:ProgramFiles "Python311\python.exe"),
        (Join-Path $env:ProgramFiles "Python310\python.exe")
    )

    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path $candidate)) {
            return (Resolve-Path $candidate).Path
        }
    }

    try {
        return (Resolve-CommandPath "python")
    }
    catch {
        return $null
    }
}

function Resolve-HuggingFaceSnapshot {
    param([string]$RepoId)

    $repoCache = Join-Path $env:USERPROFILE ".cache\huggingface\hub\models--$($RepoId.Replace('/', '--'))"
    $refsMain = Join-Path $repoCache "refs\main"
    if (Test-Path $refsMain) {
        $revision = (Get-Content $refsMain -Raw).Trim()
        $snapshot = Join-Path $repoCache "snapshots\$revision"
        if (Test-Path $snapshot) {
            return $snapshot
        }
    }

    $snapshotsDir = Join-Path $repoCache "snapshots"
    if (-not (Test-Path $snapshotsDir)) {
        return $null
    }

    $latestSnapshot = Get-ChildItem $snapshotsDir -Directory | Sort-Object Name | Select-Object -Last 1
    if ($latestSnapshot) {
        return $latestSnapshot.FullName
    }

    return $null
}

function Ensure-BertAssets {
    $targetDir = Join-Path $ProjectRoot "models\bert-base-turkish-cased"
    if (Test-Path (Join-Path $targetDir "config.json")) {
        return $targetDir
    }

    $snapshot = Resolve-HuggingFaceSnapshot "dbmdz/bert-base-turkish-cased"
    if (-not $snapshot) {
        throw "BERT assets not found in local HuggingFace cache. Download the model once before building the desktop package."
    }

    New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
    Copy-Item (Join-Path $snapshot "*") $targetDir -Recurse -Force
    return $targetDir
}

$venvCfg = Join-Path $ProjectRoot ".venv\pyvenv.cfg"
$venvLooksBroken = $false
if (Test-Path $venvCfg) {
    $venvText = Get-Content $venvCfg -Raw
    if ($venvText -match "WindowsApps") {
        $venvLooksBroken = $true
        Write-Warning ".venv points to the Windows Store Python alias. If the build fails, recreate the venv from a python.org CPython installation and rerun this script."
    }
}

if (-not $SkipFrontend) {
    Push-Location (Join-Path $ProjectRoot "Web")
    try {
        cmd /c npm run build
        if ($LASTEXITCODE -ne 0) {
            throw "Frontend build failed."
        }
    }
    finally {
        Pop-Location
    }
}

if (-not (Test-Path (Join-Path $ProjectRoot "checkpoints\best_multimodal.pt"))) {
    throw "Missing checkpoint: checkpoints\best_multimodal.pt"
}

Ensure-BertAssets | Out-Null

$ResolvedPython = $null
if (-not ($venvLooksBroken -and $PythonExe -eq ".\.venv\Scripts\python.exe")) {
    try {
        $ResolvedPython = Resolve-CommandPath $PythonExe
    }
    catch {
    }
}

if (-not $ResolvedPython) {
    $ResolvedPython = Resolve-PythonFromLauncher
    if ($ResolvedPython) {
        Write-Warning "Using fallback Python interpreter: $ResolvedPython"
    }
}

if (-not $ResolvedPython) {
    $ResolvedPython = Resolve-PythonFromKnownLocations
    if ($ResolvedPython) {
        Write-Warning "Using fallback Python interpreter: $ResolvedPython"
    }
}

if (-not $ResolvedPython) {
    throw "Could not resolve a usable Python interpreter. Pass -PythonExe with a real CPython path."
}

& $ResolvedPython -m PyInstaller (Join-Path $ProjectRoot "desktop_app.spec") --noconfirm --clean
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed."
}

if (-not $SkipInstaller) {
    if (-not (Test-Path $IsccExe)) {
        $localIscc = Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"
        if (Test-Path $localIscc) {
            $IsccExe = $localIscc
        }
        else {
            Write-Warning "Inno Setup compiler not found. The app bundle is ready in dist\ChildArtAnalyzer, but no installer was created."
            return
        }
    }

    & $IsccExe (Join-Path $ProjectRoot "installer\ChildArtAnalyzer.iss")
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup build failed."
    }
}
