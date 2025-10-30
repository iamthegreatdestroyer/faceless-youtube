# 🚀 Faceless YouTube - Desktop Application Build Guide

## Overview

This guide explains how to build the **Faceless YouTube Desktop Application** from source code into a standalone Windows executable that can be distributed and installed on end-user machines.

---

## 🎯 What You're Building

### The Application

- **PyQt6 Desktop GUI** - Modern, responsive desktop interface
- **Video Processing** - MoviePy, FFmpeg, PIL
- **AI Integration** - Claude API, OpenAI, Torch
- **YouTube Integration** - Upload, analytics, scheduling
- **Database** - PostgreSQL backend (optional for standalone)
- **Standalone Runtime** - Works without Python installed

### Output

```
dist/
├── faceless-youtube.exe        ← Main application (can run standalone)
└── faceless-youtube/
    ├── PyQt6 libraries
    ├── Python runtime
    ├── All dependencies
    └── Assets
```

### Size & Performance

- **Uncompressed Size:** 800MB - 1.2GB
- **Build Time:** 5-10 minutes
- **Runtime:** ~2-3 seconds to start
- **Requires:** 2GB RAM, 1.5GB disk space

---

## ✅ Prerequisites

### 1. System Requirements

```powershell
# Check Python version (need 3.13+)
python --version

# Check if venv is available
python -m venv --help

# Check available disk space (need ~2GB free)
Get-Volume
```

### 2. Install Dependencies

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install PyInstaller
pip install PyInstaller

# Verify all dependencies installed
pip list | findstr PyInstaller
```

### 3. Optional: External Tools

```powershell
# FFmpeg (for video processing)
# Download from: https://ffmpeg.org/download.html
# OR use: choco install ffmpeg

# ImageMagick (for image processing)
# Download from: https://imagemagick.org/

# These are optional - bundled version will work
```

---

## 🔨 Building the Application

### Quick Build (Recommended)

```powershell
cd C:\FacelessYouTube
.\build_desktop_app.bat
```

**This will:**

1. Verify Python installation
2. Check virtual environment
3. Verify PyInstaller
4. Build the executable
5. Show output location

### Build with Options

#### Clean Build (Remove Old Artifacts)

```powershell
.\build_desktop_app.bat --clean
```

#### Single-File Executable (For Distribution)

```powershell
.\build_desktop_app.bat --onefile
```

This creates a single `faceless-youtube.exe` file (~1.2GB) instead of a directory.

- **Pros:** Easier to distribute, single file to download
- **Cons:** Slower startup, larger file size

#### Show Help

```powershell
.\build_desktop_app.bat --help
```

---

## 📊 Build Process Explained

### Step-by-Step

1. **Analysis Phase**

   - PyInstaller analyzes `faceless_video_app.py`
   - Finds all imported modules
   - Identifies dependencies

2. **Collection Phase**

   - Gathers all Python packages
   - Includes hidden imports (PyQt6, AI libraries, etc.)
   - Bundles asset files

3. **Compilation Phase**

   - Converts Python to bytecode
   - Compresses into archive
   - Creates bootloader

4. **Linking Phase**

   - Links all components
   - Creates executable
   - Generates runtime

5. **Output Phase**
   - Saves to `dist/` directory
   - Creates metadata files
   - Shows build statistics

### Configuration File

The build is controlled by `build_desktop_app.spec`:

```python
# Key sections:
a = Analysis(...)           # What to include
hidden_imports = [...]      # Modules PyInstaller might miss
datas = [...]               # Data files (assets, config)
exe = EXE(...)              # Executable settings
```

---

## 🧪 Testing the Build

### 1. Quick Test (Run the Executable)

```powershell
# Navigate to output
cd C:\FacelessYouTube\dist

# Run the executable
.\faceless-youtube.exe

# OR if you built with --onefile in parent directory:
cd C:\FacelessYouTube
.\dist\faceless-youtube.exe
```

### 2. Verify Features

```
✓ Application starts without Python
✓ GUI renders correctly
✓ Menus work
✓ Settings dialog opens
✓ Project creation works
✓ Video generation works (if assets available)
✓ YouTube integration connects (with API keys)
```

### 3. Check for Missing Files

```powershell
# If you see "Module not found" errors:
1. Check build_desktop_app.spec for the module
2. Add to hidden_imports section
3. Rebuild

# If assets are missing:
1. Check that assets/ directory exists
2. Update datas section in spec
3. Rebuild
```

### 4. Performance Test

```powershell
# Measure startup time
Measure-Command { .\faceless-youtube.exe }

# Expected: 2-5 seconds first run, 1-2 seconds subsequent
```

---

## 🔧 Troubleshooting

### Build Fails with "Module Not Found"

**Error:**

```
ModuleNotFoundError: No module named 'xyz'
```

**Solution:**

1. Add module to `hidden_imports` in `build_desktop_app.spec`
2. Rebuild: `build_desktop_app.bat --clean`

**Example:**

```python
hidden_imports = [
    "PyQt6.QtCore",
    "xyz",  # Add here
]
```

### Build Takes Too Long

**Issue:** Build stuck for >15 minutes

**Solutions:**

1. Use `--clean` to remove old files: `build_desktop_app.bat --clean`
2. Disable unnecessary imports in spec file
3. Use directory build instead of `--onefile`
4. Check disk space: `Get-Volume`

### Executable Won't Start

**Error:** "Entry point not found" or immediate crash

**Solutions:**

```powershell
# 1. Check for PyQt6 errors
# Run with console to see errors:
# Temporarily modify spec: console=True

# 2. Verify dependencies installed
pip list | Select-String PyQt6

# 3. Check for file permissions
# Ensure dist/ folder is readable

# 4. Run from command line for error output
cd dist
faceless-youtube.exe 2>&1
```

### Executable Too Large

**If 1.2GB is too large:**

1. **Remove unnecessary modules** from `hidden_imports`:

   ```python
   # Remove if not needed:
   "torch",                 # If not using ML
   "sentence_transformers", # If not using embeddings
   ```

2. **Use --onefile for compression:**

   ```powershell
   build_desktop_app.bat --onefile
   ```

3. **Upx compression:**
   ```powershell
   # Install: choco install upx
   # PyInstaller uses it automatically (upx=True in spec)
   ```

### Missing Assets

**Error:** "Assets not found" when running

**Solution:**

```python
# In build_desktop_app.spec, ensure:
datas = [
    (str(PROJECT_ROOT / "assets"), "assets"),
    # ✓ This copies assets/ to the executable
]
```

---

## 📦 Next Steps: Creating an Installer

After building the executable, you can create a professional installer:

### Option 1: NSIS Installer

```
1. Download NSIS: https://nsis.sourceforge.io
2. Create installer script (example provided)
3. Run: makensis installer.nsi
4. Output: faceless-youtube-setup.exe
```

### Option 2: Inno Setup

```
1. Download: https://www.innosetup.com
2. Create installer config (.iss file)
3. Run: iscc installer.iss
4. Output: faceless-youtube-setup.exe
```

### Option 3: Windows Package Manager (Winget)

```
1. Create package manifest
2. Submit to: https://github.com/microsoft/winget-pkgs
3. Users can: winget install faceless-youtube
```

---

## 📋 Build Checklist

Before distributing, verify:

- [ ] Executable starts without errors
- [ ] All main features work
- [ ] No "Module not found" errors
- [ ] Assets load correctly
- [ ] API key configuration works
- [ ] File sizes acceptable
- [ ] Startup time reasonable (<5s)
- [ ] No console errors
- [ ] Uninstall works cleanly
- [ ] Works on fresh Windows install

---

## 🔐 Security Considerations

### Before Distribution

1. **Remove Sensitive Data**

   - No API keys in source code
   - No database credentials
   - No OAuth tokens

2. **Code Signing** (Optional but Recommended)

   ```powershell
   # Sign the executable to avoid SmartScreen warnings
   $cert = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert
   Set-AuthenticodeSignature -FilePath dist\faceless-youtube.exe -Certificate $cert
   ```

3. **Antivirus Scan**

   - Submit to VirusTotal for scanning
   - Clean executable = better user trust

4. **Privacy Policy**
   - Include privacy policy in installer
   - Disclose data collection practices
   - Include license information

---

## 📊 Build Statistics

### Typical Build Output

```
Analysis: 2.5 seconds
  - Found 500+ modules
  - Included 1200+ files

Compilation: 30 seconds
  - Bytecode generated
  - Compression applied

Linking: 45 seconds
  - Executable created
  - Runtime bundled

Total Time: 5-8 minutes
Output Size: 950 MB
```

---

## 📞 Support

### If Something Goes Wrong

1. **Check build_desktop_app.bat output** - Most errors are printed
2. **Review build_desktop_app.spec** - Verify configuration
3. **Run with --clean** - Remove cached files
4. **Check Python version** - Must be 3.13+
5. **Verify venv activated** - Check prompt shows (venv)
6. **Check disk space** - Need 2GB free

### Common Issues & Fixes

| Issue                       | Cause                        | Fix                                    |
| --------------------------- | ---------------------------- | -------------------------------------- |
| "Python not found"          | Not installed or not in PATH | Install Python 3.13+ from python.org   |
| "PyInstaller not installed" | Not pip installed            | `pip install PyInstaller`              |
| "venv not found"            | Virtual env not created      | `python -m venv venv` then activate    |
| Module not found            | Hidden import missing        | Add to hidden_imports in spec          |
| Huge file size              | All dependencies included    | Use --onefile or remove unused imports |
| Slow startup                | Large executable             | Normal, 2-5 seconds expected           |
| Can't write files           | Permissions issue            | Run as Administrator                   |

---

## 🎉 Success

After building successfully, you have:

✅ Standalone Windows executable  
✅ No Python installation required  
✅ All dependencies bundled  
✅ Professional desktop application  
✅ Ready for distribution  
✅ Can create installer with NSIS/Inno Setup

**Next:** Create an installer package and distribute to users!

---

## 📚 References

- **PyInstaller Documentation:** https://pyinstaller.org/
- **PyQt6 Documentation:** https://www.riverbankcomputing.com/static/Docs/PyQt6/
- **NSIS Installer:** https://nsis.sourceforge.io/Docs/
- **Inno Setup:** https://jrsoftware.org/isinfo.php

---

**Built with:** PyInstaller, PyQt6, and Python  
**Last Updated:** 2025-10-30  
**Version:** 1.0.0
