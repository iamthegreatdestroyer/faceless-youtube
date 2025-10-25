# 🚀 FACELESS YOUTUBE - QUICK START GUIDE

Get Faceless YouTube running in less than 5 minutes!

---

## ⚡ 30-Second Quick Start

### For Docker (Easiest)

```bash
# Windows
setup.bat
docker-start.bat

# Linux/macOS
bash setup.sh
bash docker-start.sh
```

**Then open:** http://localhost:3000

---

## 📋 5-Minute Setup Walkthrough

### Step 1: Initial Setup (2 minutes)

```bash
# Windows
setup.bat

# Linux/macOS
bash setup.sh
```

**What you'll see:**

- ✅ System requirements check
- ✅ Environment setup
- ✅ Dependency installation
- ❓ Configuration wizard asking for API keys

**When prompted:**

1. Choose deployment mode:

   - **Docker** (recommended - simpler)
   - **Local** (advanced - direct control)

2. Enter API keys (or skip and use defaults for testing):
   - YouTube API Key
   - OpenAI API Key
   - ElevenLabs API Key

### Step 2: Start Services (1 minute)

**For Docker:**

```bash
# Windows
docker-start.bat

# Linux/macOS
bash docker-start.sh
```

**For Local (Advanced):**

```bash
# Terminal 1 - API
# Windows
run-api.bat

# Linux/macOS
bash run-api.sh

# Terminal 2 - Dashboard
# Windows
run-dashboard.bat

# Linux/macOS
bash run-dashboard.sh
```

### Step 3: Access Application (1 minute)

```
Dashboard:    http://localhost:3000
API Docs:     http://localhost:8000/docs
Swagger UI:   http://localhost:8000/swagger
```

---

## 🎯 Common Startup Scenarios

### Scenario 1: First Time Setup (Complete)

```bash
# Step 1: Run full setup
setup.bat           # Windows
bash setup.sh       # Linux/macOS

# Step 2: Start with Docker
docker-start.bat    # Windows
bash docker-start.sh # Linux/macOS

# Step 3: Open browser
# http://localhost:3000
```

**Time:** ~3-5 minutes

### Scenario 2: Restart After Closing

```bash
# Just run the startup script
docker-start.bat    # Windows
bash docker-start.sh # Linux/macOS

# Or for local:
run-api.bat         # Windows
bash run-api.sh     # Linux/macOS
```

**Time:** ~10 seconds

### Scenario 3: Local Development (Debug Mode)

```bash
# Terminal 1 - API with hot reload
run-api.bat         # Windows
bash run-api.sh     # Linux/macOS

# Terminal 2 - Dashboard with hot reload
run-dashboard.bat   # Windows
bash run-dashboard.sh # Linux/macOS

# Edit code - changes auto-apply!
```

**Time:** ~5 seconds between changes

### Scenario 4: Stop Everything

```bash
# Docker
docker-compose down

# Local
# Ctrl+C in both terminals
```

---

## 🔧 Configuration

### First-Time Configuration

The setup wizard will ask for:

1. **Deployment Mode**

   - `docker` - All services in containers
   - `local` - Services on host machine

2. **API Keys**

   - YouTube API Key (get from: https://console.cloud.google.com)
   - OpenAI API Key (get from: https://platform.openai.com/api-keys)
   - ElevenLabs API Key (get from: https://elevenlabs.io)

3. **Database**
   - PostgreSQL connection string (auto-configured)
   - Database name (default: faceless_youtube)
   - Username (default: faceless_user)

### Edit Configuration Later

**Edit the .env file:**

```bash
# Windows (Notepad)
notepad .env

# Linux/macOS (nano)
nano .env

# Or use your editor (VSCode, Sublime, etc.)
```

**Common settings to change:**

```env
# Change port if 8000 is already used
API_PORT=8000

# Change database URL
DATABASE_URL=postgresql://user:password@localhost:5432/faceless_youtube

# Add your API keys
YOUTUBE_API_KEY=sk-...
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=...
```

**After editing, restart services:**

```bash
docker-compose restart  # Docker
# Or Ctrl+C and re-run startup scripts  # Local
```

---

## ✅ Verification Checklist

After startup, verify everything works:

```bash
# ✓ Check Docker services (if using Docker)
docker-compose ps
# Should show all services as "Up"

# ✓ Check API health
curl http://localhost:8000/health
# Should return: {"status": "healthy", "timestamp": "..."}

# ✓ Check API docs
# Open browser to: http://localhost:8000/docs
# Should see Swagger documentation

# ✓ Check Dashboard
# Open browser to: http://localhost:3000
# Should see Faceless YouTube dashboard

# ✓ Check database
docker-compose exec postgres psql -U faceless_user -d faceless_youtube -c "\dt"
# Should list database tables
```

---

## 🔄 Basic Commands

### Docker Commands

```bash
# View all services status
docker-compose ps

# View service logs
docker-compose logs -f          # All services
docker-compose logs -f api      # Just API
docker-compose logs -f dashboard # Just Dashboard

# Stop all services
docker-compose down

# Restart services
docker-compose restart

# View real-time logs
docker-compose logs -f

# Access database shell
docker-compose exec postgres psql -U faceless_user

# Backup database
docker-compose exec postgres pg_dump -U faceless_user faceless_youtube > backup.sql

# Restore database
docker-compose exec -T postgres psql -U faceless_user faceless_youtube < backup.sql
```

### Local Commands

```bash
# Activate Python environment
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install/update Python dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install/update Node dependencies
cd dashboard
npm install
npm update

# Run tests
pytest tests/ -v

# Build React for production
cd dashboard
npm run build

# Format code
black src/
```

---

## 🐛 Quick Troubleshooting

### Issue: Port Already in Use

**Symptom:** "Port 8000 already in use"

**Fix:**

```bash
# Find process using port
lsof -i :8000        # Linux/macOS
netstat -ano | grep :8000  # Windows

# Kill the process
kill -9 <PID>        # Linux/macOS
taskkill /PID <PID> /F  # Windows

# Or use different port - edit docker-compose.yml or .env
```

### Issue: Docker Won't Start

**Symptom:** "Cannot connect to Docker daemon"

**Fix:**

1. Make sure Docker Desktop is running
2. Restart Docker Desktop
3. Run: `docker ps` to verify

### Issue: API Returns Error

**Symptom:** "Internal Server Error" or API won't start

**Fix:**

```bash
# Check API logs
docker-compose logs api

# Or if local:
bash run-api.sh  # See error output

# Verify .env file
cat .env | grep DATABASE_URL
```

### Issue: Dashboard Blank

**Symptom:** Dashboard page loads but shows nothing

**Fix:**

1. Open browser Developer Tools (F12)
2. Check Console tab for errors
3. Check Network tab - API calls failing?
4. Clear browser cache: Ctrl+Shift+Delete
5. Hard refresh: Ctrl+Shift+R

### Issue: Out of Memory

**Symptom:** Services crash with OOM error

**Fix (Docker):**

1. Open Docker Desktop Settings
2. Go to Resources
3. Increase Memory to 8GB+
4. Click Apply & Restart

**Fix (Local):**

- Ensure you have 4GB+ RAM free
- Close other applications
- Check system resources: `docker stats`

### Issue: Can't Connect to Database

**Symptom:** "Cannot connect to PostgreSQL"

**Fix:**

```bash
# Check if PostgreSQL is running
docker-compose ps postgres  # Should show "Up"

# Check credentials in .env
cat .env | grep DATABASE_URL

# Try connecting directly
docker-compose exec postgres psql -U faceless_user -d faceless_youtube

# Check PostgreSQL logs
docker-compose logs postgres
```

---

## 📊 Performance Tips

### For Development

```bash
# Use local API + local dashboard (faster hot reload)
bash run-api.sh    # Terminal 1
bash run-dashboard.sh  # Terminal 2
```

### For Production

```bash
# Use Docker Compose (optimized, isolated)
docker-compose -f docker-compose.yml up -d
```

### Monitor Performance

```bash
# Watch resource usage
docker stats

# Check API response time
curl -w "\nTotal time: %{time_total}s\n" http://localhost:8000/health

# Check database query time
docker-compose exec postgres psql -U faceless_user -d faceless_youtube -c "\timing"
```

---

## 📱 Accessing From Other Machines

### From Another Computer on Same Network

**Find your machine's IP:**

```bash
# Windows
ipconfig | findstr "IPv4 Address"

# Linux/macOS
ifconfig | grep "inet " | grep -v "127.0.0.1"
```

**Access from other machine:**

```
http://<YOUR_IP>:3000    # Dashboard
http://<YOUR_IP>:8000    # API
```

**Update .env if needed:**

```env
# Change localhost to your IP or domain
REACT_APP_API_URL=http://<YOUR_IP>:8000
```

---

## 🚀 Next Steps After Startup

1. **Log In**

   - Navigate to http://localhost:3000
   - Create first user account
   - Change default password

2. **Configure API Keys**

   - Go to Settings → API Configuration
   - Add YouTube API Key
   - Add OpenAI API Key
   - Test connections

3. **Explore Features**

   - Create first project
   - Try transformation engine
   - Test video generation

4. **Set Up Backups**

   ```bash
   # Regular backups
   docker-compose exec postgres pg_dump -U faceless_user faceless_youtube > backup-$(date +%Y%m%d).sql
   ```

5. **Enable Monitoring**
   - Check API docs: http://localhost:8000/docs
   - Monitor logs: `docker-compose logs -f`

---

## 📞 Quick Help

### Get Full Installation Guide

See `INSTALLATION_GUIDE.md` in the project root

### Common Commands Reference

| Task                     | Command                                                 |
| ------------------------ | ------------------------------------------------------- |
| **Initial setup**        | `setup.bat` or `bash setup.sh`                          |
| **Start all services**   | `docker-start.bat` or `bash docker-start.sh`            |
| **Start just API**       | `run-api.bat` or `bash run-api.sh`                      |
| **Start just Dashboard** | `run-dashboard.bat` or `bash run-dashboard.sh`          |
| **View logs**            | `docker-compose logs -f`                                |
| **Stop services**        | `docker-compose down`                                   |
| **Check status**         | `docker-compose ps`                                     |
| **Backup database**      | `docker-compose exec postgres pg_dump ... > backup.sql` |
| **View API docs**        | http://localhost:8000/docs                              |
| **Access Dashboard**     | http://localhost:3000                                   |

---

## ⏱️ Typical Timings

| Action                   | Time          |
| ------------------------ | ------------- |
| First-time setup         | 3-5 minutes   |
| Service startup          | 10-15 seconds |
| Hot reload (code change) | 2-5 seconds   |
| Database migration       | 5-10 seconds  |
| Building for production  | 1-2 minutes   |

---

## ✨ That's It!

You should now have Faceless YouTube running!

**Next:** Configure your API keys and start transforming shows.

**Need help?** Check `INSTALLATION_GUIDE.md` for detailed troubleshooting.
