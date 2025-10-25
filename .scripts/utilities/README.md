# 🛠️ Utility Scripts & Tools

**Purpose:** Troubleshooting, maintenance, and system utilities  
**Status:** ✅ Production Ready  
**Platform Support:** Windows (PowerShell), Linux/macOS (Bash), Python (Cross-platform)

---

## 🔍 PostgreSQL Utilities

### Windows: `find_postgres_password.ps1`

- **Purpose:** Locate PostgreSQL admin password
- **Platform:** Windows (PowerShell)
- **When to Use:** Cannot remember postgres password

**Usage:**

```powershell
.\find_postgres_password.ps1
```

**What It Does:**

1. Searches environment variables
2. Checks configuration files
3. Queries registry (Windows)
4. Suggests password reset if not found

---

### Windows: `fix_postgresql_*.ps1` Scripts

Three variations for different fix scenarios:

#### `fix_postgresql_password_admin.ps1`

- **Purpose:** Reset PostgreSQL admin password
- **Safe:** Non-destructive
- **Time:** ~1 minute

**Usage:**

```powershell
.\fix_postgresql_password_admin.ps1
```

#### `fix_postgresql_simple.ps1`

- **Purpose:** Quick PostgreSQL fixes
- **Fixes:**
  - Connection issues
  - Permission problems
  - Service startup issues

**Usage:**

```powershell
.\fix_postgresql_simple.ps1
```

---

### Linux/macOS: `pg_audit_init.sh`

- **Purpose:** Initialize PostgreSQL audit logging
- **Platform:** Linux/macOS
- **Features:**
  - Enable audit extension
  - Configure logging
  - Set retention policies

**Usage:**

```bash
chmod +x pg_audit_init.sh
./pg_audit_init.sh
```

---

## 📦 Dependency Management

### Windows: `monitor_pip_install.ps1`

- **Purpose:** Monitor Python package installations
- **Platform:** Windows (PowerShell)
- **Features:**
  - Progress tracking
  - Error detection
  - Auto-retry failed packages

**Usage:**

```powershell
.\monitor_pip_install.ps1
```

**Use When:**

- Installing large package sets
- Debugging installation failures
- Tracking dependency resolution

---

## 🔐 Security & Certificates

### Python: `generate_certificates.py`

- **Purpose:** Generate self-signed SSL/TLS certificates
- **Platform:** Windows, Linux, macOS (Python)
- **Output:** `.pem` certificate files

**Usage:**

```bash
python generate_certificates.py
```

**What It Does:**

1. Generates private key
2. Creates certificate signing request
3. Signs certificate
4. Outputs to `certs/` directory

**Certificate Details:**

- Algorithm: RSA 2048-bit
- Validity: 365 days
- Use: Development/staging

**Files Generated:**

- `private.key` - Private key
- `certificate.pem` - Certificate
- `server.crt` - Server certificate

---

### Python: `verify_database_hardening.py`

- **Purpose:** Verify database security configuration
- **Platform:** Windows, Linux, macOS (Python)
- **Checks:**
  - Connection security
  - User permissions
  - Encryption status
  - Audit logging

**Usage:**

```bash
python verify_database_hardening.py
```

**Output:**

```
Checking database security...
✓ Encryption enabled
✓ Audit logging active
✓ User permissions correct
✓ Connection SSL verified
All security checks passed!
```

---

## 📊 Common Utility Tasks

### Reset Everything (Start Fresh)

```bash
# 1. Stop services
./stop.sh

# 2. Reset PostgreSQL
fix_postgresql_simple.ps1  # Windows
./reset_postgres.sh        # Linux/macOS

# 3. Clear cache and temporary files
rm -rf venv/
rm -rf node_modules/
rm -rf __pycache__/

# 4. Reinstall
./setup.sh  # or setup.bat
```

### Verify Security

```bash
python verify_database_hardening.py
```

### Monitor Installation

```bash
# Windows
.\monitor_pip_install.ps1

# Linux/macOS
# (Use standard pip progress)
```

### Generate Certificates

```bash
python generate_certificates.py
# Creates SSL certificates in certs/ directory
```

---

## 🆘 Troubleshooting Guide

### PostgreSQL Issues

**Cannot Connect:**

```powershell
.\fix_postgresql_simple.ps1
```

**Forgot Password:**

```powershell
.\find_postgres_password.ps1
.\fix_postgresql_password_admin.ps1
```

**Enable Audit Logging:**

```bash
./pg_audit_init.sh
```

---

### Installation Issues

**Packages Won't Install:**

```powershell
.\monitor_pip_install.ps1
```

**Then check specific package:**

```bash
pip install --verbose <package_name>
```

---

### Security Issues

**Verify Database Security:**

```bash
python verify_database_hardening.py
```

**Generate New Certificates:**

```bash
python generate_certificates.py
```

---

## 📋 Pre-Deployment Checklist

Before deploying, run:

```bash
# 1. Verify database security
python verify_database_hardening.py

# 2. Check PostgreSQL configuration
./pg_audit_init.sh

# 3. Generate SSL certificates if needed
python generate_certificates.py

# 4. Test installation
./monitor_pip_install.ps1  # Windows
```

---

## 🔧 Script Maintenance

### To Keep Scripts Updated

1. Check `.documentation/05_security/SECURITY.md` for security best practices
2. Run security verification regularly
3. Update certificates annually
4. Review audit logs monthly

---

## 📞 When to Use Each Script

| Issue                     | Script                         | Platform    |
| ------------------------- | ------------------------------ | ----------- |
| PostgreSQL password lost  | `find_postgres_password.ps1`   | Windows     |
| PostgreSQL won't start    | `fix_postgresql_simple.ps1`    | Windows     |
| Installation slow/failing | `monitor_pip_install.ps1`      | Windows     |
| Setup audit logging       | `pg_audit_init.sh`             | Linux/macOS |
| Need SSL certificates     | `generate_certificates.py`     | All         |
| Verify security config    | `verify_database_hardening.py` | All         |

---

## 📞 For More Help

- **Database Security:** `.documentation/05_security/ITEM_3_DATABASE_HARDENING_IMPLEMENTATION.md`
- **Secrets Management:** `.documentation/05_security/ITEM_4_SECRETS_MANAGEMENT_IMPLEMENTATION.md`
- **TLS/HTTPS:** `.documentation/05_security/ITEM_2_TLS_HTTPS_IMPLEMENTATION.md`
- **Quick Fixes:** `.documentation/02_quick_start/QUICK_FIX_GUIDE.md`

---

**Last Updated:** October 25, 2025  
**Status:** ✅ Production Ready
