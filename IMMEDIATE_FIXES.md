# IMMEDIATE FIXES REQUIRED

## Security and Stability Patches

**Priority:** HIGH  
**Estimated Time:** 30 minutes  
**Required Before:** Production deployment

---

## FIX 1: Replace MD5 with SHA256 (HIGH PRIORITY)

### Issue

MD5 hash used for cache key generation - weak cryptographic hash that fails security compliance.

### Location

- **File:** `src/utils/cache.py`
- **Line:** 456

### Current Code

```python
cache_key = hashlib.md5(key.encode()).hexdigest()
```

### Fixed Code

```python
cache_key = hashlib.sha256(key.encode(), usedforsecurity=False).hexdigest()
```

### Why This Fix?

- SHA256 is cryptographically stronger
- `usedforsecurity=False` parameter tells Python this is for non-security purposes (cache keys)
- Maintains backward compatibility with cache invalidation

### Apply Fix

```bash
# Navigate to file
code src/utils/cache.py

# Manual edit at line 456:
# Replace: hashlib.md5(key.encode()).hexdigest()
# With: hashlib.sha256(key.encode(), usedforsecurity=False).hexdigest()
```

---

## FIX 2: Replace Hardcoded /tmp/ Paths (MEDIUM PRIORITY)

### Issue

Hardcoded `/tmp/` paths cause cross-platform incompatibility and security risks.

### Location 1: Video Creation Endpoint

- **File:** `src/api/main.py`
- **Line:** 557

### Current Code

```python
temp_path = f"/tmp/video_{video_id}.mp4"
```

### Fixed Code

```python
import tempfile

# In the function:
with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False, dir=None) as tmp:
    temp_path = tmp.name
```

### Location 2: Video Timeline Assembly

- **File:** `src/services/video_assembler/timeline.py`
- **Line:** 255

### Current Code

```python
output_path = f"/tmp/timeline_{timeline_id}.mp4"
```

### Fixed Code

```python
import tempfile

# In the function:
with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False, dir=None) as tmp:
    output_path = tmp.name
```

### Why This Fix?

- `tempfile` module handles platform-specific temp directories
- Works on Windows (`C:\Users\...\AppData\Local\Temp\`), Linux/Mac (`/tmp/`)
- More secure (proper permissions, automatic cleanup if needed)
- No hardcoded paths

### Apply Fix

```bash
# Fix location 1
code src/api/main.py
# Add import at top: import tempfile
# Replace hardcoded path at line 557 with tempfile.NamedTemporaryFile

# Fix location 2
code src/services/video_assembler/timeline.py
# Add import at top: import tempfile
# Replace hardcoded path at line 255 with tempfile.NamedTemporaryFile
```

---

## FIX 3: Add Missing Dependency (MEDIUM PRIORITY)

### Issue

`pythonjsonlogger` package missing from requirements.txt, causing 16 test failures.

### Error Message

```
ModuleNotFoundError: No module named 'pythonjsonlogger'
```

### Fix

Add package to `requirements.txt`:

```bash
# Option 1: Append to requirements.txt
echo "python-json-logger==2.0.7" >> requirements.txt

# Option 2: Manual edit
code requirements.txt
# Add line: python-json-logger==2.0.7
```

### Install Package

```bash
pip install python-json-logger==2.0.7
```

### Why This Fix?

- Required for structured JSON logging in `src/utils/logging_config.py`
- Currently imported but not in dependencies
- Causes 16 API integration tests to fail

---

## VERIFICATION STEPS

After applying all fixes, run these commands to verify:

### 1. Verify Syntax

```bash
# Check Python syntax
python -m py_compile src/utils/cache.py
python -m py_compile src/api/main.py
python -m py_compile src/services/video_assembler/timeline.py
```

### 2. Run Security Scan

```bash
# Should reduce from 7 to 4 issues (all LOW severity false positives)
bandit -r src/
```

Expected output:

```
Issue: [B404:blacklist] Consider possible security implications associated with the subprocess module.
   Severity: Low   Confidence: High
   (4 occurrences - all false positives in database backup scripts)
```

### 3. Run Test Suite

```bash
# Should pass 164/164 tests (up from 162/164)
pytest --cov=src --cov-report=term-missing

# Expected:
# - 164 passed
# - 0 failed
# - Coverage: 76%
```

### 4. Test Cache Functionality

```bash
# Quick manual test
python -c "
from src.utils.cache import generate_cache_key
key = generate_cache_key('test_key')
print(f'Generated cache key: {key}')
print(f'Length: {len(key)} characters')
# Should print 64-character SHA256 hash
"
```

### 5. Test Temp File Creation

```bash
# Quick manual test
python -c "
import tempfile
with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
    print(f'Created temp file: {tmp.name}')
    print(f'Exists: {tmp.name}')
# Should print platform-appropriate temp path
"
```

---

## POST-FIX VALIDATION

### Expected Outcomes

- ✅ Bandit security issues reduced from 7 to 4 (LOW severity false positives only)
- ✅ Test suite: 164/164 passing (100%)
- ✅ No cross-platform compatibility issues
- ✅ All dependencies installed correctly

### Re-run Full Audit

```bash
# Security scan
bandit -r src/ -o security_report.txt

# Test suite with coverage
pytest --cov=src --cov-report=html

# Linting
black --check src/
ruff check src/
mypy src/

# All should pass with no errors
```

---

## ROLLBACK PLAN

If any fix causes issues:

### 1. Git Revert

```bash
# If using git
git checkout src/utils/cache.py
git checkout src/api/main.py
git checkout src/services/video_assembler/timeline.py
git checkout requirements.txt
```

### 2. Manual Rollback

Keep backups of original files:

```bash
# Before applying fixes
cp src/utils/cache.py src/utils/cache.py.backup
cp src/api/main.py src/api/main.py.backup
cp src/services/video_assembler/timeline.py src/services/video_assembler/timeline.py.backup
cp requirements.txt requirements.txt.backup

# To rollback
cp src/utils/cache.py.backup src/utils/cache.py
# etc.
```

---

## TIMELINE

### Immediate (Next 30 minutes)

- [ ] Fix 1: MD5 → SHA256 (5 minutes)
- [ ] Fix 2: Hardcoded paths → tempfile (15 minutes)
- [ ] Fix 3: Add missing dependency (1 minute)
- [ ] Run verification tests (10 minutes)

### Next Steps (After Fixes)

- [ ] Deploy to staging environment
- [ ] Run smoke tests
- [ ] Perform load testing
- [ ] Deploy to production

---

## SUPPORT

If you encounter issues applying these fixes:

1. **Syntax Errors:** Run `python -m py_compile <file>` to identify exact issues
2. **Import Errors:** Ensure `tempfile` is imported at top of file
3. **Test Failures:** Check logs with `pytest -v` for detailed output
4. **Dependency Issues:** Try `pip install --upgrade python-json-logger`

---

**Document Created:** October 8, 2025  
**Audit Reference:** AUDIT_REPORT.md  
**Priority:** HIGH - Required before production deployment
