# ⚡ Desktop Build Quick Reference

## One Command to Rule Them All

```powershell
cd C:\FacelessYouTube
.\build_desktop_app.bat
```

**That's it.** Your executable will be in `dist/faceless-youtube.exe`

---

## Options

```powershell
# Clean build (recommended for first-time)
.\build_desktop_app.bat --clean

# Single file (for easy distribution)
.\build_desktop_app.bat --onefile

# Help
.\build_desktop_app.bat --help
```

---

## What You Get

- ✅ Standalone Windows executable (no Python needed)
- ✅ All dependencies bundled
- ✅ PyQt6 desktop interface
- ✅ Video processing, AI, YouTube integration
- ✅ ~950MB application

---

## Test It

```powershell
# Run the built executable
.\dist\faceless-youtube.exe

# Should start in 2-5 seconds
# All features should work
```

---

## Next: Create Installer

After testing, create a professional installer:

- **NSIS:** https://nsis.sourceforge.io
- **Inno Setup:** https://www.innosetup.com

---

## Troubleshooting

| Problem                 | Solution                                 |
| ----------------------- | ---------------------------------------- |
| "Python not found"      | Install Python 3.13+                     |
| "PyInstaller not found" | `pip install PyInstaller`                |
| "venv not found"        | `python -m venv venv`                    |
| Build takes forever     | Use `--clean` first                      |
| Module not found error  | Add to `build_desktop_app.spec`          |
| Executable too large    | Use `--onefile` or remove unused imports |

---

## Architecture

```
faceless_video_app.py (PyQt6 GUI)
       ↓
[PyInstaller Analysis]
       ↓
[Gathers all dependencies & assets]
       ↓
dist/faceless-youtube.exe ← Standalone executable!
```

---

## Size & Time

- **Build Time:** 5-10 minutes
- **Output Size:** 800-1200 MB
- **Startup Time:** 2-5 seconds
- **Requires:** 2GB RAM, 1.5GB disk space

---

## What's Inside

- Python runtime (~500MB)
- PyQt6 libraries (~200MB)
- All dependencies (Torch, FastAPI, etc.) (~300MB)
- Assets and configuration
- Video processing tools (FFmpeg integration)

---

## Distribution

Once built:

1. **For Testing:** Share `dist/faceless-youtube.exe` directly
2. **For Production:** Create installer using NSIS or Inno Setup
3. **For Organizations:** Sign executable and submit to VirusTotal

---

**Ready to build?** Run: `.\build_desktop_app.bat`
