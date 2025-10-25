# 📦 Installation Scripts

**Purpose:** One-click installers for all platforms  
**Status:** ✅ Production Ready

---

## 🪟 Windows Installation

### `setup.bat`

- **Purpose:** One-click Windows installer
- **Time:** ~2-3 minutes
- **Features:**
  - Automatic system validation
  - Python virtual environment setup
  - Dependency installation
  - Configuration wizard
  - Docker support

**Usage:**

```bash
setup.bat
```

**What It Does:**

1. Checks Windows version (10/11)
2. Validates Python 3.11+ installation
3. Creates virtual environment
4. Installs dependencies
5. Launches configuration wizard
6. Starts services

---

## 🐧 Linux/macOS Installation

### `setup.sh`

- **Purpose:** One-click Linux/macOS installer
- **Time:** ~2-3 minutes
- **Features:**
  - Automatic system validation
  - Python virtual environment setup
  - Dependency installation
  - Configuration wizard
  - Docker support

**Usage:**

```bash
chmod +x setup.sh
./setup.sh
```

**What It Does:**

1. Checks OS compatibility (Ubuntu 20.04+, Debian 11+, macOS 12+)
2. Validates Python 3.11+ installation
3. Creates virtual environment
4. Installs dependencies
5. Launches configuration wizard
6. Starts services

---

## 📋 Quick Start Installation

### `setup_faceless_youtube.bat`

- **Purpose:** Alternative Windows installer with enhanced features
- **Platform:** Windows 10/11 only
- **Time:** ~2-3 minutes

**Usage:**

```bash
setup_faceless_youtube.bat
```

---

## ✅ Installation Checklist

Before running installer, verify:

- [ ] Windows 10/11 (for .bat) or Ubuntu 20.04+/Debian 11+/macOS 12+ (for .sh)
- [ ] Python 3.11+ installed and in PATH
- [ ] 5GB available disk space
- [ ] 2GB available RAM
- [ ] Internet connection for dependency downloads
- [ ] Administrator/sudo access if needed

---

## 🆘 Troubleshooting

### Issue: Python not found

**Solution:**

```bash
# Check Python version
python --version

# If not found, install from python.org or package manager
```

### Issue: Permission denied (Linux/macOS)

**Solution:**

```bash
chmod +x setup.sh
./setup.sh
```

### Issue: Setup fails partway through

**Solution:**

1. Check `.logs/setup.log` for errors
2. See `.documentation/02_quick_start/QUICK_FIX_GUIDE.md`
3. Run setup again (idempotent, safe to retry)

---

## 📞 For More Help

- **Full Installation Guide:** `.documentation/01_installation/INSTALLATION_GUIDE.md`
- **Quick Start:** `.documentation/02_quick_start/QUICK_START.md`
- **Troubleshooting:** `.documentation/02_quick_start/QUICK_FIX_GUIDE.md`

---

**Last Updated:** October 25, 2025  
**Status:** ✅ Production Ready
