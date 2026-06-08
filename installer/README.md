# Windows setup wizard

This folder contains the Inno Setup definition for the Windows installer.

Build from the project root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_installer.ps1
```

Output:

```text
installer\output\ChildArtAnalyzer-Setup.exe
```

Requirements:

- Python 3
- Node.js/npm
- Inno Setup 6 (`ISCC.exe`)

The installer installs the PyInstaller desktop bundle, creates Start Menu and optional Desktop shortcuts, and launches `ChildArtAnalyzer.exe` after installation.
