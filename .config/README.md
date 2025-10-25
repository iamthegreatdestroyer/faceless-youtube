# ⚙️ Configuration Files

**Purpose:** Centralized configuration management  
**Status:** ✅ Production Ready  
**Security:** ⚠️ Keep .env files private (do not commit)

---

## 📋 Environment Configuration

### `.env` (CURRENT - Active Configuration)

- **Purpose:** Current environment variables
- **Security:** ⚠️ **KEEP PRIVATE** - Do not commit or share
- **Status:** Runtime configuration
- **Content:**
  - Database credentials
  - API keys
  - Service URLs
  - Feature flags

**Important:**

- Contains sensitive data
- Unique to each environment
- Created by setup wizard
- Never commit to repository

**Never commit .env to Git!**

---

### `.env.example` (TEMPLATE)

- **Purpose:** Configuration template for setup
- **Security:** ✅ Safe to share - no sensitive data
- **Use:** Reference for required variables
- **Content:** All variables with placeholder values

**How to Use:**

1. Copy `.env.example` to `.env`
2. Fill in actual values
3. Save (keep private)
4. Never commit `.env`

```bash
# Linux/macOS
cp .env.example .env

# Windows
copy .env.example .env
```

---

### `.env.backup` (BACKUP)

- **Purpose:** Backup of previous configuration
- **Security:** ⚠️ Keep private
- **Use:** Recovery if needed
- **Rotation:** Automatically created on major changes

---

### `.env.staging` (STAGING ENVIRONMENT)

- **Purpose:** Configuration for staging environment
- **Security:** ⚠️ Keep private
- **Use:** `docker-compose -f docker-compose.staging.yml`
- **Content:**
  - Staging database URLs
  - Staging API keys
  - Staging service URLs

**When to Use:**

- Before production deployment
- Final validation testing
- Performance benchmarking

---

### `.env.prod` (PRODUCTION - LINUX/MACROS ONLY)

- **Purpose:** Production environment configuration
- **Security:** 🔒 **HIGHLY SENSITIVE** - Maximum protection
- **Platform:** Linux/macOS production servers only
- **Content:**
  - Production database credentials
  - Production API keys
  - Production service URLs
  - Security headers

**Protection Measures:**

- Store in secure vault on production server
- Restrict file permissions (600)
- Never download to local machine
- Rotate credentials regularly
- Enable audit logging

---

### `.env.production.example` (TEMPLATE)

- **Purpose:** Reference template for production config
- **Security:** ✅ Safe to share - no sensitive data
- **Use:** Guide for production setup

---

## 🗄️ Database Configuration

### `alembic.ini`

- **Purpose:** Database migration configuration
- **Tool:** Alembic (SQLAlchemy migrations)
- **Content:**
  - SQLAlchemy database URL
  - Migration script location
  - Logging configuration
  - Version control settings

**Common Commands:**

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Downgrade migration
alembic downgrade -1

# Check current version
alembic current
```

---

## 🧪 Testing Configuration

### `pytest.ini`

- **Purpose:** Python testing framework configuration
- **Tool:** pytest
- **Content:**
  - Test discovery patterns
  - Test markers
  - Coverage configuration
  - Output options
  - Plugin settings

**Key Settings:**

```ini
[pytest]
testpaths = tests/
python_files = test_*.py
addopts = -v --tb=short --cov=src
markers =
    unit: unit tests
    integration: integration tests
    smoke: smoke tests
```

**Common Commands:**

```bash
# Run all tests
pytest

# Run specific test
pytest tests/unit/test_auth.py

# Run with coverage
pytest --cov=src

# Run specific marker
pytest -m unit

# Run and show output
pytest -s

# Run with verbose output
pytest -vv
```

---

## 📊 Configuration Priority

**Environment variables are loaded in this order** (highest to lowest priority):

1. Runtime flags (e.g., `--env-file`)
2. `.env` (current environment)
3. `.env.staging` (if staging)
4. `.env.prod` (if production)
5. System environment variables
6. `.env.example` (fallback/reference)

**First match wins** - Use most specific to environment.

---

## 🔐 Security Best Practices

### DO ✅

- ✅ Keep `.env` private and not in version control
- ✅ Use strong, unique passwords
- ✅ Rotate credentials regularly
- ✅ Use separate configs per environment
- ✅ Enable audit logging in production
- ✅ Use secrets management system in production
- ✅ Encrypt sensitive data at rest

### DON'T ❌

- ❌ Commit `.env` to repository
- ❌ Share `.env` files via email or chat
- ❌ Use default/weak passwords
- ❌ Leave credentials in code comments
- ❌ Store multiple environments in one `.env`
- ❌ Log sensitive values to stdout
- ❌ Use production credentials in development

---

## 📝 Creating New Configurations

### For New Environment

1. **Copy template:**

   ```bash
   cp .env.example .env.new_environment
   ```

2. **Edit with actual values:**

   ```bash
   nano .env.new_environment  # or your editor
   ```

3. **Load when needed:**

   ```bash
   export $(cat .env.new_environment | xargs)
   ```

4. **Or use with Docker:**
   ```bash
   docker-compose --env-file .env.new_environment up
   ```

---

## 🔄 Configuration Rotation

### Regular Maintenance

**Weekly:**

- Review `.env` file
- Check for test credentials in production
- Verify audit logs

**Monthly:**

- Rotate API keys
- Update database passwords
- Review access logs
- Backup current `.env`

**Quarterly:**

- Full credential rotation
- Security audit
- Configuration review
- Update `.env.example` if needed

---

## 🆘 Troubleshooting

### Issue: Configuration Not Loading

**Solution:**

1. Verify `.env` exists in project root
2. Check file permissions
3. Verify environment variables are exported
4. Use `env | grep VAR_NAME` to check

### Issue: Wrong Configuration Used

**Solution:**

1. Check priority list above
2. Verify command-line flags
3. Check environment variables
4. Use `echo $VARIABLE` to debug

### Issue: Forgot Password

**Solution:**

1. Check `.env.backup` or `.env.example`
2. Use password recovery tools
3. Reset in database if needed
4. See `.scripts/utilities/` for PostgreSQL tools

---

## 📋 Configuration Checklist

Before deployment:

- [ ] `.env` file created from `.env.example`
- [ ] All required variables filled in
- [ ] Passwords are strong (12+ chars, mixed case, special chars)
- [ ] Database connection verified
- [ ] API keys are valid
- [ ] URLs are correct for environment
- [ ] `.env` is NOT committed to Git
- [ ] Backup created (`.env.backup`)
- [ ] File permissions restricted (600)
- [ ] Audit logging enabled

---

## 📞 For More Help

- **Environment Setup:** `.documentation/01_installation/INSTALLATION_GUIDE.md`
- **Secrets Management:** `.documentation/05_security/ITEM_4_SECRETS_MANAGEMENT_IMPLEMENTATION.md`
- **Database Hardening:** `.documentation/05_security/ITEM_3_DATABASE_HARDENING_IMPLEMENTATION.md`
- **Quick Fixes:** `.documentation/02_quick_start/QUICK_FIX_GUIDE.md`

---

**Last Updated:** October 25, 2025  
**Status:** ✅ Production Ready
