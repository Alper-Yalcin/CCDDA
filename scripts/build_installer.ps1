param(
    [string]$Configuration = "Release"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$WebRoot = Join-Path $ProjectRoot "Web"
$DesktopVenvPython = Join-Path $ProjectRoot ".desktop-venv\Scripts\python.exe"
$DesktopVenvPyInstaller = Join-Path $ProjectRoot ".desktop-venv\Scripts\pyinstaller.exe"
$SpecPath = Join-Path $ProjectRoot "desktop_app.spec"
$InnoScript = Join-Path $ProjectRoot "installer\ChildArtAnalyzer.iss"
$InstallerOutput = Join-Path $ProjectRoot "installer\output\ChildArtAnalyzer-Setup.exe"

function Find-Iscc {
    $cmd = Get-Command "ISCC.exe" -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }

    return $null
}

Set-Location $ProjectRoot

if (-not (Test-Path -LiteralPath $DesktopVenvPython)) {
    py -3 -m venv ".desktop-venv"
}

& $DesktopVenvPython -m pip install --upgrade pip
& $DesktopVenvPython -m pip install -r "requirements-desktop.txt"

if (Test-Path -LiteralPath (Join-Path $WebRoot "package.json")) {
    Push-Location $WebRoot
    try {
        if (-not (Test-Path -LiteralPath "node_modules")) {
            npm install
        }
        npm run build
    }
    finally {
        Pop-Location
    }
}

if (-not (Test-Path -LiteralPath $DesktopVenvPyInstaller)) {
    throw "PyInstaller was not installed in .desktop-venv."
}

& $DesktopVenvPyInstaller $SpecPath --clean --noconfirm

if (-not (Test-Path -LiteralPath "dist\ChildArtAnalyzer\ChildArtAnalyzer.exe")) {
    throw "PyInstaller did not create dist\ChildArtAnalyzer\ChildArtAnalyzer.exe."
}

$iscc = Find-Iscc
if (-not $iscc) {
    throw "Inno Setup compiler was not found. Install Inno Setup 6, then rerun: powershell -ExecutionPolicy Bypass -File scripts\build_installer.ps1"
}

& $iscc $InnoScript

if (-not (Test-Path -LiteralPath $InstallerOutput)) {
    throw "Installer build finished, but output was not found: $InstallerOutput"
}

Write-Host "Installer created: $InstallerOutput"
