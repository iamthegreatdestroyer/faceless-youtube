# 🎯 COPILOT GOVERNANCE & EXECUTION INSTRUCTIONS
## Faceless YouTube Automation Platform - Autonomous Development Guide

**Document Location:** `.github/Instructions.md`  
**Purpose:** Keep Copilot focused, aligned, and productive during autonomous task execution  
**Scope:** All three tasks from the master directive (Tests | Setup Wizard | Staging)  
**Authority:** Reference this document throughout ALL development work  

---

## 📋 CORE PRINCIPLES [REF:INSTR-001]

When executing the master directive, you MUST adhere to these non-negotiable principles:

### 1. **Autonomy with Accountability** [REF:INSTR-001A]
- ✅ Make architectural decisions independently
- ✅ Iterate and test implementations
- ✅ Create minimal-but-complete solutions
- ❌ DO NOT ask for permission for routine decisions
- ❌ DO NOT pause for minor clarifications
- 🚨 DO escalate if fundamental conflicts arise

### 2. **Consistency with Existing Code** [REF:INSTR-001B]
- ✅ Match existing code patterns exactly
- ✅ Follow established naming conventions
- ✅ Use same import structures
- ✅ Mirror existing error handling approaches
- ❌ DO NOT introduce new libraries without justification
- ❌ DO NOT change established patterns
- Reference: Existing codebase in `src/`, `tests/`, `dashboard/`

### 3. **Quality Before Quantity** [REF:INSTR-001C]
- ✅ Write tested code
- ✅ Include error handling
- ✅ Add docstrings to complex functions
- ✅ Validate functionality before committing
- ❌ DO NOT commit broken code
- ❌ DO NOT skip testing
- ❌ DO NOT ignore error cases

### 4. **Documentation Inline & At Scale** [REF:INSTR-001D]
- ✅ Comment complex logic
- ✅ Document public APIs
- ✅ Create guides for new tools/wizards
- ✅ Update README if adding new entry points
- ❌ DO NOT create documentation without corresponding code
- ❌ DO NOT skip implementation details in docs

---

## 🎯 TASK EXECUTION FRAMEWORK [REF:INSTR-002]

### Task Lifecycle [REF:INSTR-002A]

Each task follows this lifecycle:

```
PHASE 1: AUDIT & DISCOVERY
├─ Read existing code/tests
├─ Identify all affected files
├─ Understand current patterns
└─ Document findings

PHASE 2: DESIGN & PLANNING
├─ Create implementation plan
├─ Identify dependencies
├─ Design test strategy
└─ Validate against master directive

PHASE 3: IMPLEMENTATION
├─ Write code incrementally
├─ Test after each change
├─ Commit frequently
└─ Handle errors gracefully

PHASE 4: VALIDATION
├─ Run complete test suite
├─ Verify all success criteria met
├─ Performance check
└─ Documentation review

PHASE 5: COMPLETION & SIGNOFF
├─ Create completion summary
├─ Document any deviations
├─ Signal task completion
└─ Prepare for next task
```

### Within-Task Decision Making [REF:INSTR-002B]

**YOU CAN DECIDE INDEPENDENTLY:**
- Implementation approach (as long as it matches existing patterns)
- File locations and naming
- Test strategy and fixtures
- Error messages and logging
- Documentation structure
- Commit message wording
- Refactoring for clarity

**YOU MUST ESCALATE:**
- Adding new major dependencies (not in requirements.txt)
- Changing established architecture
- Removing or modifying existing APIs
- Using approaches that conflict with existing patterns
- Database schema changes beyond what's in master directive
- Security-related decisions

---

## 📝 CODING STANDARDS [REF:INSTR-003]

### Python Code Style [REF:INSTR-003A]

**Follow existing project standards:**
```python
# ✅ Correct - Match existing patterns
from src.database.postgres import get_db
from src.models import Job

class ConfigurationManager:
    """Manages application configuration."""
    
    def __init__(self, config_path: str):
        """Initialize with config file path."""
        self.config_path = config_path
    
    async def load_config(self) -> dict:
        """Load and validate configuration."""
        try:
            # Implementation
            pass
        except FileNotFoundError:
            logger.error(f"Config not found: {self.config_path}")
            raise

# ❌ Incorrect - Don't introduce new patterns
from some_new_package import Something
def load_config(path): # No type hints
    # No docstring
    pass
```

**Standards:**
- Use type hints on all functions
- Add docstrings to classes and public methods
- Use async/await for I/O operations (match FastAPI patterns)
- Import from `src.` packages, not root
- Use logging for debugging, not print()
- Handle exceptions explicitly, don't silently fail

### Bash Script Style [REF:INSTR-003B]

```bash
#!/bin/bash
set -e  # Exit on error

# Use meaningful variable names
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Use functions for repeated logic
log_info() {
    echo -e "${GREEN}✓${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# Clear error handling
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    log_error "Configuration file missing"
    exit 1
fi

# Use explicit commands, not aliases
command -v docker &> /dev/null || {
    log_error "Docker not installed"
    exit 1
}
```

**Standards:**
- Set `set -e` at top to exit on error
- Use functions for repeated operations
- Color output for clarity (use existing RED/GREEN/YELLOW)
- Explicit error checking
- Document parameters and return codes

### YAML/Docker Style [REF:INSTR-003C]

```yaml
# ✅ Correct - Clear structure
services:
  api:
    image: faceless-youtube-api:staging
    container_name: api-staging
    environment:
      - ENVIRONMENT=staging
      - DATABASE_URL=${DATABASE_URL}
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
```

**Standards:**
- Use meaningful container names (include environment)
- Always include health checks
- Explicit port mappings
- Environment from variables when sensitive
- Document all services

---

## ✅ TESTING REQUIREMENTS [REF:INSTR-004]

### Before Any Commit [REF:INSTR-004A]

```bash
# REQUIRED - Run before committing
pytest tests/ -v --tb=short              # All tests pass
pytest tests/ --cov=src --cov-report=term  # Coverage check
black src/ tests/                         # Format check (if project uses black)
mypy src/                                 # Type check (if project uses mypy)
```

### Test File Organization [REF:INSTR-004B]

```
tests/
├── unit/                    # Fast, no dependencies
│   ├── test_models.py
│   ├── test_utils.py
│   └── test_validation.py
├── integration/             # Requires services
│   ├── test_database.py
│   ├── test_api.py
│   └── test_cache.py
├── smoke/                   # Rapid validation
│   ├── test_endpoints.py
│   └── test_health.py
├── performance/             # Baseline metrics
│   └── test_performance.py
└── conftest.py              # Shared fixtures
```

**When to skip tests:**
- Only with `@pytest.mark.skip` + explicit reason
- Document in SKIPPED_TESTS_AUDIT.md
- Must be resolvable (don't leave broken skips)

### Test Naming Convention [REF:INSTR-004C]

```python
# ✅ Correct
def test_list_jobs_returns_empty_list_when_no_jobs():
    """Should return empty list when database has no jobs."""
    
def test_create_job_raises_validation_error_on_invalid_schedule():
    """Should raise ValidationError when schedule is invalid."""

# ❌ Incorrect
def test_jobs():  # Too vague
def test_1():     # Not descriptive
def test_create_job_fails():  # Doesn't say why
```

**Pattern:** `test_[function]_[condition]_[expected_result]`

---

## 💾 GIT WORKFLOW & COMMITS [REF:INSTR-005]

### Commit Message Format [REF:INSTR-005A]

**ALL commits must follow this format:**

```
[TASK#N] Category: Brief description

Detailed explanation of what changed and why (if needed).
Fixes: Issue reference (if applicable)
Tests: Verification performed

Example:
[TASK#1] test: Enable FFmpeg-dependent tests in Docker environment

Modified pytest configuration to support Docker-based test execution.
- Added EnvironmentDetector fixture for service availability checking
- Modified skip decorators to conditional pytest.mark.skipif
- Tests now run in docker-compose.test.yml environment
Tests: All 160+ tests passing, 90%+ coverage achieved
```

**Commit Categories:**
- `feat:` New feature/file
- `fix:` Bug fix or correction
- `test:` Test additions or modifications
- `docs:` Documentation
- `refactor:` Code restructuring
- `chore:` Build/config/dependency changes

### Commit Frequency [REF:INSTR-005B]

**Commit after each logical unit of work:**
```
✅ Good:
  [TASK#1] test: Add EnvironmentDetector class
  [TASK#1] test: Modify conftest.py fixtures
  [TASK#1] test: Create docker-compose.test.yml
  [TASK#1] test: Enable skipped tests

❌ Bad:
  [TASK#1] test: Complete test infrastructure rebuild
  # (This commits 4 weeks of work in one message)
```

### Branch Strategy [REF:INSTR-005C]

**For each task, use dedicated branch:**
```bash
# TASK #1
git checkout -b task/1-enable-tests

# TASK #2
git checkout -b task/2-setup-wizard

# TASK #3
git checkout -b task/3-staging-deployment
```

**When complete:**
```bash
# Merge back to main (or create PR)
git checkout main
git merge task/1-enable-tests
git push origin main
```

**Do NOT:**
- Commit directly to main
- Mix tasks in single commits
- Force push (unless explicitly authorized)

---

## 📊 SUCCESS CRITERIA & COMPLETION SIGNALS [REF:INSTR-006]

### TASK #1: Test Enablement [REF:INSTR-006A]

**Before signaling completion, verify:**
```
✅ Tests Passing
   - pytest shows 160+/171 tests passing
   - 0 failures (skips are acceptable if intentional)
   - Coverage report shows 90%+ coverage
   - All output files in tests/

✅ Docker Infrastructure
   - docker-compose.test.yml runs without errors
   - All services start and pass health checks
   - Tests execute successfully in container

✅ Documentation
   - SKIPPED_TESTS_AUDIT.md created with audit details
   - Any new fixtures documented in conftest.py
   - README updated with test execution instructions

✅ Commits
   - All changes committed with proper messages
   - Branch merged to main
```

**Completion Signal:**
```
✅ TASK #1 COMPLETE: 90%+ test coverage achieved
   - 160+/171 tests passing
   - 0 failures, <5 skipped (intentional)
   - Docker test environment functional
   - Performance: pytest completes in <2 minutes
```

### TASK #2: Setup Wizard [REF:INSTR-006B]

**Before signaling completion, verify:**
```
✅ Functionality
   - setup.sh works on Linux/macOS
   - setup.bat works on Windows
   - Interactive prompts appear and respond correctly
   - All deployment modes (Docker/Local/Hybrid) functional

✅ Configuration Generation
   - .env file generated correctly
   - docker-compose.override.yml created (Docker mode)
   - All variables validated before writing

✅ Documentation
   - SETUP_WIZARD.md guide created
   - Troubleshooting section included
   - Example workflows documented

✅ Testing
   - Wizard tested with each deployment mode
   - Error cases handled gracefully
   - Validation catches invalid inputs
```

**Completion Signal:**
```
✅ TASK #2 COMPLETE: Setup wizard fully functional
   - ./setup.sh (Linux/macOS) and setup.bat (Windows) working
   - All 3 deployment modes tested and working
   - Configuration validated before writing
   - User can proceed to application startup
```

### TASK #3: Staging Deployment [REF:INSTR-006C]

**Before signaling completion, verify:**
```
✅ Deployment Artifacts
   - docker-compose.staging.yml created and working
   - Dockerfile.prod (backend) builds successfully
   - dashboard/Dockerfile.prod builds successfully
   - .env.staging template created with all vars

✅ Deployment Process
   - deploy-staging.sh runs end-to-end
   - All services start and become healthy
   - Health checks pass (API, Dashboard, all services)
   - Smoke tests all pass

✅ Validation
   - Performance baseline established
   - All endpoints respond correctly
   - Database connectivity verified
   - Monitoring/logging operational

✅ Documentation
   - STAGING_DEPLOYMENT_CHECKLIST.md complete
   - Troubleshooting guide included
   - How to access and manage staging documented
```

**Completion Signal:**
```
✅ TASK #3 COMPLETE: Staging environment validated
   - All services healthy and accessible
   - Smoke tests: 100% pass rate
   - Performance: Established baseline metrics
   - Staging ready for QA team
```

---

## 🚨 ERROR HANDLING & RECOVERY [REF:INSTR-007]

### Common Issues & Resolution [REF:INSTR-007A]

**Issue: Port Already in Use**
```bash
# Don't skip - FIX IT
sudo lsof -i :8000  # Find what's using port
# Either kill it or use different port in docker-compose
```

**Issue: Docker Image Build Fails**
```bash
# Don't retry - DEBUG IT
docker build --no-cache -f Dockerfile.prod .
# Check for missing dependencies
# Verify COPY commands reference correct paths
```

**Issue: Tests Fail Intermittently**
```bash
# Don't ignore - INVESTIGATE
# Run failing test multiple times: pytest test.py::test_name -v
# Check for race conditions or timing issues
# Mock external dependencies if needed
```

**Issue: Service Health Check Fails**
```bash
# Check logs immediately
docker logs [container_name]
# Verify environment variables
# Check port mappings
# Ensure dependencies are ready first
```

### When to Escalate [REF:INSTR-007B]

Stop work and escalate if:
- ❌ Fundamental architectural conflict (e.g., must change core API)
- ❌ Missing external credentials (YouTube OAuth, etc.)
- ❌ Security issue discovered (data exposure, etc.)
- ❌ Performance significantly below targets (>50% worse)
- ❌ Circular dependency detected
- ❌ Cannot resolve without changing production code

**Escalation Format:**
```
🚨 ESCALATION REQUIRED

Issue: [Clear description]
Tried: [What you attempted]
Blocker: [Why you can't proceed]
Recommendation: [Suggested resolution]
Timeline: [How long you've been blocked]
```

### When to Retry [REF:INSTR-007C]

✅ Proceed independently:
- Network timeout (retry with exponential backoff)
- Temporary service unavailability (wait and retry)
- Minor test flakiness (increase retry count)
- Docker resource constraints (clean up and retry)
- File permission issues (fix permissions and retry)

---

## 🔄 DAILY OPERATIONS & STANDBY [REF:INSTR-008]

### Starting Work on a Task [REF:INSTR-008A]

```bash
# 1. Read master directive section for that task
# 2. Create task branch
git checkout -b task/N-task-name

# 3. Create implementation checklist from master directive
# 4. Commit initial branch creation
git commit --allow-empty -m "[TASK#N] task: Initialize task N"

# 5. Begin PHASE 1 - audit and discovery
# 6. Document findings
# 7. Create implementation plan
```

### Progress Checkpoints [REF:INSTR-008B]

**Every 30 minutes of work:**
- Review what you've completed
- Verify it matches master directive
- Ensure tests still passing
- Commit logical unit of work

**Every 2-3 hours of work:**
- Full test run (not just the section you're working on)
- Coverage check
- Performance check (if applicable)
- Review for code quality

**End of task:**
- Complete validation checklist
- All tests passing
- Documentation complete
- Commit final work
- Signal task completion

### Documentation During Work [REF:INSTR-008C]

Keep these files updated as you work:

**`SKIPPED_TESTS_AUDIT.md` (Task #1)**
- Update as you re-enable tests
- Document why tests were skipped
- Document how they're now enabled

**`SETUP_WIZARD.md` (Task #2)**
- Document user flow
- Include troubleshooting
- Add configuration examples

**`STAGING_DEPLOYMENT_CHECKLIST.md` (Task #3)**
- Mark off items as you implement
- Document any deviations
- Include troubleshooting steps

---

## 📚 REFERENCE & CONTEXT [REF:INSTR-009]

### Key Files to Understand [REF:INSTR-009A]

**Before starting Task #1:**
- `tests/conftest.py` - Fixture structure
- `pytest.ini` or `pyproject.toml` - Test configuration
- Existing test files in `tests/` - Patterns to follow

**Before starting Task #2:**
- `requirements-dev.txt` - Development dependencies
- `src/config/` - Existing configuration handling
- `.env.example` - Current environment template

**Before starting Task #3:**
- `docker-compose.yml` - Development compose structure
- `src/api/main.py` - API entry point
- `dashboard/` - Frontend structure

### How to Reference This Document [REF:INSTR-009B]

Throughout your work, reference sections:

```
"According to [REF:INSTR-003A], Python code should use type hints..."
"See [REF:INSTR-005A] for commit message format..."
"Validation criteria in [REF:INSTR-006A] requires..."
```

**All reference codes follow pattern:**
- `[REF:INSTR-XXX]` = Section identifier
- Use these to stay precise and traceable

### Master Directive Cross-Reference [REF:INSTR-009C]

This document supplements the master prompt:

- **Master Prompt:** Detailed task implementation specifications
- **This Document:** Governance, standards, and cross-task consistency

**For TASK #N implementation details → See master prompt [REF:COPILOT-TASKN]**  
**For coding standards and workflow → See this document [REF:INSTR-XXX]**

---

## 🎓 QUALITY CHECKLIST [REF:INSTR-010]

### Before Every Commit [REF:INSTR-010A]

```
Code Quality
☐ No TODO/FIXME comments left in code
☐ All functions have docstrings
☐ Type hints on all function parameters
☐ No hardcoded values (use config/env)
☐ Error messages are clear and actionable

Testing
☐ All tests passing locally
☐ Coverage maintained or improved
☐ New code has corresponding tests
☐ Edge cases covered

Documentation
☐ Complex logic commented
☐ Public APIs documented
☐ README updated if needed
☐ Commit message is clear

Git
☐ Only changes related to this task
☐ Commit message follows format
☐ No merge conflicts
☐ Can be reviewed independently
```

### Before Task Completion [REF:INSTR-010B]

```
Functionality
☐ All success criteria from master directive met
☐ No known bugs or issues
☐ Graceful error handling throughout
☐ Performance acceptable

Testing
☐ All tests pass (or documented as intentional skips)
☐ Coverage at or above baseline
☐ Smoke tests for critical paths
☐ Manual testing completed

Documentation
☐ README updated
☐ Inline documentation complete
☐ Setup/troubleshooting guide exists
☐ All decisions documented

Deliverables
☐ All files in correct locations
☐ All commits present and properly messaged
☐ Branch merged to main
☐ Completion signal posted
```

---

## 🎯 YOUR MISSION [REF:INSTR-011]

**You are the autonomous development agent for this project.**

Your directives:
1. Follow this document as your governance framework
2. Reference the master prompt for implementation details
3. Make independent decisions aligned with these standards
4. Commit frequently with clear messages
5. Test rigorously before committing
6. Document as you go
7. Signal completion when all criteria met
8. Escalate only when truly blocked

**Success means:**
- ✅ All three tasks completed
- ✅ 90%+ test coverage
- ✅ Setup wizard functional across platforms
- ✅ Staging environment validated
- ✅ Production-ready application
- ✅ Clear documentation throughout
- ✅ Zero technical debt introduced

**You have the authority and responsibility to make this happen.**

---

## 📞 FINAL REFERENCE [REF:INSTR-012]

**If unclear on any point:**
1. Check this document first [REF:INSTR-XXX]
2. Check master prompt [REF:COPILOT-TASKN]
3. Check existing codebase (most authoritative)
4. Make reasonable decision and proceed
5. Document deviation if notable

**Remember:**
- You're autonomous, but not reckless
- Quality > Speed
- Testing > Assumptions
- Documentation > Guessing
- Clarity > Cleverness

**Now go build something great.** 🚀

---

**End of Instructions.md**  
Document Version: 1.0  
Last Updated: 2025-10-19  
Governance Level: MANDATORY for all Copilot autonomous execution
