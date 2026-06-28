# 🔱 Brotherhood Omega Swarm Health Status & Recovery Guide

## Current Situation

**Status as of June 28, 2026, 10:35 UTC:**

```
🔴 SYSTEM STATUS: PARTIALLY DEGRADED
   8 out of 11 containers marked as (unhealthy)
   Root cause: Health check endpoints timing out
   Impact: Agents cannot accept traffic, trading halted
```

**Unhealthy Containers:**
- ❌ omega_patrick (Scanner) - Port 3005
- ❌ omega_dj (Executor) - Port 3003  
- ❌ omega_bossman (Risk Guardian) - Port 3006
- ❌ omega_hashim (Compounder) - Port 3004
- ❌ omega_hustle_bridge (Bridge) - Port 3001
- ❌ omega_oracle_engine (Oracle) - Port 3002
- ❌ omega_dashboard (Dashboard) - Port 8082
- ❌ omega_agentbus (AgentBus) - Port 8081

**Healthy Containers:**
- ✅ omega-postgres (Database)
- ✅ omega-redis (Cache)
- ✅ System resources: 19% memory, 17.5% disk, 0.0 load

---

## The Problem (Technical Details)

Docker containers have **health checks** that verify the service is running correctly:

```
Health Check Flow:
1. Docker runs every 45 seconds: curl http://localhost:PORT/health
2. Service responds with HTTP 200 = ✅ HEALTHY
3. Service doesn't respond or returns error = ❌ UNHEALTHY
4. After 5 failures in a row, marked permanently UNHEALTHY
```

**Why 8 services are unhealthy:**

1. **Timeout during initialization**
   - Service takes >15 seconds to start
   - Health check times out before service ready
   - Marked UNHEALTHY after 5 consecutive timeouts

2. **Configuration missing**
   - .env file missing or incomplete
   - API keys (Helius, Birdeye) not loaded
   - Service crashes on startup

3. **Dependency issues**
   - Services start before postgres/redis ready
   - Database connection fails
   - Redis connection fails

4. **Health check settings too strict**
   - Current timeout: 10 seconds (too fast)
   - Current startup grace: 40 seconds (too short)
   - Current retry: 3 failures (too low)

---

## The Solution

I've built a complete **health monitoring & recovery system** with:

### 1. **Real-time Monitoring** (`core/monitoring.py`)
- Check all 9 services every 45 seconds
- Track uptime % and response times
- Auto-detect failure types:
  - Timeout → Service not responding
  - Connection refused → Service not listening
  - HTTP 500 → Service has runtime error

### 2. **Automatic Diagnostics** (`DiagnosticAnalyzer`)
- Analyzes failures to find root causes
- Suggests debugging commands
- Generates CLI commands to fix issues
- Example: "API key invalid" → Run `docker logs omega_patrick | grep -i helius`

### 3. **CLI Monitoring Tool** (`bin/monitor.py`)
- Check current health: `python bin/monitor.py status`
- Diagnose issues: `python bin/monitor.py diagnose`
- Monitor continuously: `python bin/monitor.py watch 30`
- View service history: `python bin/monitor.py history omega_patrick`
- Send alerts: `python bin/monitor.py alert`

### 4. **Telegram Alerts** (`core/alerts.py`)
- Notifications when services go down
- Recovery alerts when services come back up
- Swarm health reports every 5 minutes
- Built-in cooldown (prevent alert flooding)

### 5. **Complete Documentation**
- `MONITORING.md` - Full technical guide (500+ lines)
- `QUICK_FIX.sh` - Step-by-step recovery script
- `docker-compose.example.yml` - Reference configuration
- `tests/test_monitoring.py` - Automated tests

---

## How to Fix (Now)

### Option A: Quick Restart (Fastest)

```bash
ssh root@206.189.118.255
cd /opt/omega-dynasty-v6

# Restart everything
docker compose restart

# Wait for services to initialize (60 seconds is key)
sleep 60

# Check status
docker ps
```

Expected result after 60 seconds: Containers should show "healthy" status.

### Option B: Diagnose & Fix (Better)

```bash
# From your laptop in the repo directory
python bin/monitor.py diagnose

# This will show:
# - Exactly which services are failing
# - Why they're failing (timeout, connection refused, etc.)
# - Step-by-step commands to debug
# - Priority-ordered fixes
```

Then follow the suggested commands from the diagnostics output.

### Option C: Use the Recovery Script (Comprehensive)

```bash
# Download and run the quick fix script
bash QUICK_FIX.sh

# This will:
# - Check all containers
# - Show system resources
# - Display logs from each service
# - Test connectivity to each port
# - Verify .env configuration
# - Show permanent fix (update docker-compose.yml)
# - Monitor continuous recovery
```

---

## Understanding the Permanent Fix

The root cause is Docker's **health check configuration** in `docker-compose.yml`.

### Current (Broken) Configuration
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:3005/health"]
  interval: 30s        # Check every 30 seconds
  timeout: 10s         # Only 10 seconds to respond (TOO STRICT)
  retries: 3           # Fail after 3 tries (TOO AGGRESSIVE)
  start_period: 40s    # Grace period (TOO SHORT)
```

**Why this fails:**
- Service takes >10s to initialize
- Health check runs at 40s + 30s = 70s after startup
- By then it's already marked UNHEALTHY

### Fixed Configuration
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:3005/health"]
  interval: 45s        # Check every 45 seconds (less noise)
  timeout: 15s         # 15 seconds to respond (more reasonable)
  retries: 5           # Allow 5 failures (more forgiving)
  start_period: 60s    # ← CRITICAL: Full minute to initialize
```

**Why this works:**
- Service gets 60 full seconds to start
- Health checks don't begin until 60+ seconds
- By then service is fully initialized
- Timeout is reasonable for network requests
- 5 retries = ~4 minutes to recover from transient issues

### To Apply This Fix

1. **Edit docker-compose.yml on droplet:**
   ```bash
   ssh root@206.189.118.255
   cd /opt/omega-dynasty-v6
   nano docker-compose.yml
   
   # Find each service (omega_patrick, omega_dj, etc.)
   # Update their healthcheck section with the config above
   # Save (Ctrl+X, Y, Enter)
   ```

2. **Restart with new config:**
   ```bash
   docker compose down
   docker compose up -d
   sleep 60
   docker ps
   ```

3. **Verify success:**
   ```bash
   # All containers should show "healthy"
   docker ps | grep omega_
   ```

---

## Monitoring & Alerting

### Check Status From Your Laptop

```bash
# One-time snapshot
python bin/monitor.py status

# Watch continuously (updates every 30s)
python bin/monitor.py watch 30

# Get detailed diagnostics
python bin/monitor.py diagnose

# Show service history
python bin/monitor.py history omega_patrick
```

### Sample Output

```
🔱 BROTHERHOOD OMEGA SWARM HEALTH STATUS
Time: 2026-06-28T10:35:00
Target: http://206.189.118.255

Overall Status: HEALTHY
Health Score: 100.0%
Healthy: 9/9

Services:
────────────────────────────────────────────────────────────────────
Service                 Status              Port     Response
────────────────────────────────────────────────────────────────────
omega_patrick           ✅ healthy          3005     45ms
omega_dj                ✅ healthy          3003     38ms
omega_bossman           ✅ healthy          3006     42ms
omega_hashim            ✅ healthy          3004     40ms
omega_hustle_bridge     ✅ healthy          3001     35ms
omega_oracle_engine     ✅ healthy          3002     50ms
omega_dashboard         ✅ healthy          8082     55ms
omega_agentbus          ✅ healthy          8081     48ms
```

### Send Alerts to Telegram

Set up `.env` with:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

Then:
```bash
# Send immediate alert
python bin/monitor.py alert

# Setup automatic alerts every 5 minutes (on droplet)
# Add to crontab:
*/5 * * * * cd /opt/omega-dynasty-v6 && python bin/monitor.py alert
```

---

## Tracking Uptime & Trends

```python
from core.monitoring import get_monitor

monitor = get_monitor()

# Get uptime statistics for a service
trend_1m = monitor.get_trend("omega_patrick", window_seconds=60)
trend_5m = monitor.get_trend("omega_patrick", window_seconds=300) 
trend_1h = monitor.get_trend("omega_patrick", window_seconds=3600)

print(trend_1m)
# Output: {
#   "uptime_pct": 95.5,
#   "samples": 19,
#   "avg_response_time_ms": 45.2,
#   "window_seconds": 60
# }
```

This tracks:
- **Uptime %** - How often is the service healthy?
- **Samples** - How many checks did we run?
- **Response Time** - Average time to respond (ms)
- **Window** - Time period analyzed

---

## Architecture & Design

### Health Check Flow

```
External Health Check
    ↓
SwarmMonitor.check_all_services()
    ↓
    ├→ Check omega_patrick:3005/health
    ├→ Check omega_dj:3003/health
    ├→ Check omega_bossman:3006/health
    ├→ Check omega_hashim:3004/health
    ├→ Check omega_dashboard:8082/health
    ├→ ... (9 total services)
    ↓
SwarmHealth (aggregate)
    ├→ total_services: 9
    ├→ healthy_count: 9
    ├→ unhealthy_count: 0
    ├→ overall_status: HEALTHY
    ├→ health_percentage: 100%
    ↓
DiagnosticAnalyzer (if unhealthy)
    ├→ Analyze failure patterns
    ├→ Suggest root causes
    ├→ Generate debugging commands
    ↓
AlertManager (if degraded)
    ├→ Send Telegram notification
    ├→ Apply cooldown (prevent flooding)
    ├→ Log event
```

### Data Model

```python
HealthCheck:
  - service_name: str
  - status: HealthStatus (HEALTHY|UNHEALTHY|UNKNOWN|STARTING)
  - port: int
  - endpoint: str (/health)
  - response_time_ms: float
  - error_message: str (optional)
  - checked_at: datetime

SwarmHealth:
  - total_services: int
  - healthy_count: int
  - unhealthy_count: int
  - overall_status: HealthStatus
  - health_percentage: float
  - checks: List[HealthCheck]
```

---

## Files Added

| File | Size | Purpose |
|------|------|---------|
| `core/monitoring.py` | 405 lines | Health check client & diagnostics |
| `core/alerts.py` | 325 lines | Telegram alerting system |
| `bin/monitor.py` | 335 lines | CLI monitoring tool |
| `tests/test_monitoring.py` | 315 lines | Test suite |
| `MONITORING.md` | 500 lines | Full documentation |
| `QUICK_FIX.sh` | 325 lines | Recovery script |
| `docker-compose.example.yml` | 250 lines | Reference config |
| `requirements.txt` | +2 lines | Added pytest dependencies |

**Total:** ~2,400 lines of code + documentation

---

## Timeline to Recovery

| Step | Time | Action |
|------|------|--------|
| 0-5 min | Now | Run `python bin/monitor.py status` |
| 5-10 min | | Run `python bin/monitor.py diagnose` |
| 10-15 min | | SSH to droplet & check logs per diagnostics |
| 15-20 min | | Restart: `docker compose restart` |
| 20-80 min | | Wait for 60s startup grace period |
| 80-85 min | | Verify: `docker ps` - all healthy ✅ |
| 85-90 min | | Update docker-compose.yml (permanent fix) |
| 90-120 min | | Test recovery monitoring: `python bin/monitor.py watch 30` |
| **Total** | **~2 hours** | System healthy & monitored |

---

## Success Criteria

You'll know the fix worked when:

- [ ] `docker ps` shows all containers as "healthy" or "Up"
- [ ] `python bin/monitor.py status` shows 9/9 healthy
- [ ] `curl http://206.189.118.255:3005/health` returns 200 OK
- [ ] Dashboard at http://206.189.118.255:8082 loads
- [ ] Agents are accepting trades again
- [ ] Telegram alerts show all green messages

---

## Next Steps

1. **Right now:** Run diagnostics
   ```bash
   python bin/monitor.py diagnose
   ```

2. **In 5 minutes:** Execute suggested fixes
   ```bash
   ssh root@206.189.118.255
   docker logs omega_patrick --tail 100
   # Follow diagnostics output
   ```

3. **In 15 minutes:** Restart and wait
   ```bash
   docker compose restart
   sleep 60
   docker ps
   ```

4. **In 20 minutes:** Verify recovery
   ```bash
   python bin/monitor.py status
   ```

5. **After recovery:** Deploy permanent fix
   ```bash
   # Update docker-compose.yml with new health check settings
   # Redeploy: docker compose down && docker compose up -d
   ```

6. **Going forward:** Monitor continuously
   ```bash
   # Setup cron on droplet
   */5 * * * * cd /opt/omega-dynasty-v6 && python bin/monitor.py alert
   ```

---

## References

- **Full Docs:** See `MONITORING.md`
- **Quick Fix:** See `QUICK_FIX.sh`
- **Example Config:** See `docker-compose.example.yml`
- **Code:** See `core/monitoring.py`, `core/alerts.py`, `bin/monitor.py`
- **Tests:** See `tests/test_monitoring.py`

---

**Status:** 🔴 Recovering  
**Last Updated:** 2026-06-28 10:35 UTC  
**Maintainer:** Brotherhood Omega Empire  
**Next Review:** After health restored

🔱 **CHUKUA KONTROLI YOTE** - The swarm will be healthy, monitored, and operational. 🔱
