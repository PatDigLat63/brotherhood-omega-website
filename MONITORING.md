# 🔱 Brotherhood Omega Swarm Health Monitoring System

Complete health monitoring, diagnostics, and alerting system for the distributed agent swarm.

## Current Issue: Unhealthy Containers

**Status:** 8 out of 11 containers marked **(unhealthy)** on droplet `206.189.118.255`

```
❌ omega_dashboard         (unhealthy)
❌ omega_bossman           (unhealthy)
❌ omega_dj                (unhealthy)
❌ omega_hashim            (unhealthy)
❌ omega_hustle_bridge     (unhealthy)
❌ omega_patrick           (unhealthy)
❌ omega_oracle_engine     (unhealthy)
❌ omega_agentbus          (unhealthy)

✅ redis:7-alpine          (healthy)
✅ postgres:15             (healthy)
```

**Root Cause:** Services are running but their health check endpoints are either:
- Timing out (not responding within timeout window)
- Returning non-200 HTTP status
- Not listening on expected ports
- Crashing during initialization

---

## Quick Start

### 1. Monitor Current Health

```bash
cd /home/runner/work/brotherhood-omega-website/brotherhood-omega-website

# Show current swarm status
python bin/monitor.py status
```

**Output:**
```
🔱 BROTHERHOOD OMEGA SWARM HEALTH STATUS
Time: 2026-06-28T10:35:00.000000
Target: http://206.189.118.255

Services:
────────────────────────────────────────────────────────────────────────────────
Service                       Status          Port     Response       Error
────────────────────────────────────────────────────────────────────────────────
omega_patrick                 ✅ healthy      3005     45ms           -
omega_dj                      ❌ unhealthy    3003     10000ms        Timeout (unreachable)
...
```

### 2. Diagnose Issues

```bash
python bin/monitor.py diagnose
```

Automatically analyzes failures and provides:
- Root cause analysis
- Per-service debugging steps
- Recommended fixes in priority order

### 3. Continuous Monitoring

```bash
# Monitor every 30 seconds
python bin/monitor.py watch

# Monitor every 10 seconds
python bin/monitor.py watch 10
```

### 4. Send Alert to Telegram

```bash
python bin/monitor.py alert
```

Sends current health status to your Telegram channel.

---

## Modules

### `core/monitoring.py`

Main health check and monitoring logic.

**Classes:**
- `HealthStatus` - Enum: HEALTHY, UNHEALTHY, UNKNOWN, STARTING
- `HealthCheck` - Result of single service health check
- `SwarmHealth` - Aggregate health across all services
- `SwarmMonitor` - Main monitoring client
  - `check_all_services()` - Check all 9 services
  - `check_service_health(name, port)` - Check single service
  - `get_trend(service_name, window_seconds)` - Get uptime % over time window
- `DiagnosticAnalyzer` - Analyze failures
  - `diagnose_failures(swarm_health)` - Get root cause analysis
  - `_diagnose_service(check)` - Per-service diagnosis
  - `_suggest_fixes(check)` - Generate fix commands

**Usage:**
```python
from core.monitoring import get_monitor, DiagnosticAnalyzer

# Get monitor instance
monitor = get_monitor(base_url="http://206.189.118.255")

# Check all services
health = await monitor.check_all_services()

# Analyze failures
diagnostics = DiagnosticAnalyzer.diagnose_failures(health)

# Get trend for a service
trend = monitor.get_trend("omega_patrick", window_seconds=300)
```

### `core/alerts.py`

Telegram alerting system.

**Classes:**
- `AlertLevel` - Enum: INFO, WARNING, CRITICAL, SUCCESS
- `Alert` - Single alert message
- `TelegramAlerter` - Send alerts to Telegram
  - `send_alert(alert)` - Send formatted alert
  - `send_swarm_health_report(health)` - Send health status
  - `send_service_down_alert(check)` - Alert for service failure
  - `send_service_recovered_alert(check)` - Alert for recovery
- `AlertManager` - Manage alerts with cooldown to prevent flooding
  - `alert_service_unhealthy(check)` - Alert with 5min cooldown
  - `alert_service_recovered(check)` - Alert recovery with cooldown
  - `alert_swarm_unhealthy(health)` - Alert overall swarm status

**Usage:**
```python
from core.alerts import get_alerter, get_alert_manager

# Get alerter
alerter = get_alerter()

# Send health report
await alerter.send_swarm_health_report(health)

# Use alert manager to prevent flooding
manager = get_alert_manager()
await manager.alert_swarm_unhealthy(health)
```

### `bin/monitor.py`

CLI tool for monitoring.

**Commands:**
```bash
python bin/monitor.py status              # Current health snapshot
python bin/monitor.py watch [interval]    # Continuous monitoring (default 30s)
python bin/monitor.py history SERVICE     # Show service history
python bin/monitor.py diagnose            # Analyze failures
python bin/monitor.py alert               # Send to Telegram
```

---

## Health Check Architecture

### Service Ports

Each service exposes a health check endpoint:

| Service | Port | Endpoint | Expected Response |
|---------|------|----------|-------------------|
| PATRICK (Scanner) | 3005 | `/health` | 200 OK |
| DJ (Executor) | 3003 | `/health` | 200 OK |
| BOSSMAN (Risk) | 3006 | `/health` | 200 OK |
| HASHIM (Compounder) | 3004 | `/health` | 200 OK |
| Hustle Bridge | 3001 | `/health` | 200 OK |
| Oracle Engine | 3002 | `/health` | 200 OK |
| Dashboard | 8082 | `/health` | 200 OK |
| AgentBus | 8081 | `/health` | 200 OK |
| Telegram Bot | 8083 | `/health` | 200 OK |

### Health Check Logic

```
For each service:
  1. Try to GET http://droplet_ip:port/health
  2. If response 200-299: HEALTHY ✅
  3. If response 300+: UNHEALTHY ❌
  4. If timeout (10s): UNHEALTHY ❌
  5. If connection refused: UNHEALTHY ❌
  6. Other error: UNKNOWN ❓

Aggregate: If ANY unhealthy → Overall UNHEALTHY
```

---

## Diagnosing Failures

### Common Failure Patterns

#### 1. "Timeout (unreachable)"
**Meaning:** Service took >10s to respond or didn't respond at all

**Possible causes:**
- Service crashed or failed to start
- Service not binding to port
- Network firewall blocking
- Service hanging/deadlocked

**Debug steps:**
```bash
# Check if container is running
docker ps | grep omega_patrick

# Check startup logs
docker logs omega_patrick --tail 100 | head -50

# Check if listening on port
netstat -tlnp | grep 3005
# or
ss -tlnp | grep 3005

# Manually test connection
curl -v http://206.189.118.255:3005/health
```

#### 2. "Connection refused (service not listening)"
**Meaning:** Port is open but nothing listening on it

**Possible causes:**
- Service hasn't started yet
- Service binding to wrong port
- Service crashed immediately after start
- Container startup delay >40s

**Debug steps:**
```bash
# Check container status
docker ps -a | grep omega_patrick

# Check last 200 lines of logs
docker logs omega_patrick --tail 200

# Check error during startup
docker logs omega_patrick | grep -i "error\|fatal\|panic"

# Restart container
docker restart omega_patrick

# Wait 60s and recheck
sleep 60
curl http://206.189.118.255:3005/health
```

#### 3. "HTTP 500" or other 4xx/5xx
**Meaning:** Service is running but health check endpoint returned error

**Possible causes:**
- Service not initialized (database/redis not ready)
- Missing configuration/environment variables
- API key or authentication failure
- Service dependency failed

**Debug steps:**
```bash
# Get detailed response
curl -v http://206.189.118.255:3005/health

# Check environment variables
docker inspect omega_patrick | grep -A 10 "Env"

# Check for config errors in logs
docker logs omega_patrick | grep -i "config\|env\|error"

# Check database connectivity
docker logs omega_patrick | grep -i "database\|postgres\|connection"

# Check API key validation
docker logs omega_patrick | grep -i "api\|helius\|birdeye"
```

---

## Fixing Unhealthy Containers

### Step 1: Restart Containers

```bash
ssh root@206.189.118.255

cd /opt/omega-dynasty-v6

# Restart all containers
docker compose restart

# Wait 60 seconds for services to start
sleep 60

# Check status
docker ps
```

### Step 2: Fix Health Check Configuration

If containers still unhealthy after restart, update `docker-compose.yml`:

```yaml
services:
  omega_patrick:
    image: your-image:latest
    ports:
      - "3005:3005"
    
    # IMPORTANT: These health check settings
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3005/health"]
      interval: 45s       # Check every 45 seconds (not too aggressive)
      timeout: 15s        # Wait 15s for response (not too strict)
      retries: 5          # Allow 5 failures before marking unhealthy
      start_period: 60s   # Grace period for startup (important!)
    
    # Ensure environment variables are loaded
    env_file: .env
    environment:
      - HELIUS_API_KEY=${HELIUS_API_KEY}
      - BIRDEYE_API_KEY=${BIRDEYE_API_KEY}
      # ... other required env vars
    
    # Ensure database/redis are ready
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
```

**Key settings:**
- `start_period: 60s` - Give services 60s to initialize before marking unhealthy
- `interval: 45s` - Don't check too frequently (causes system noise)
- `timeout: 15s` - Allow reasonable response time
- `retries: 5` - Don't mark unhealthy after just 1 failure
- `env_file: .env` - Ensure config loaded
- `depends_on: condition: service_healthy` - Wait for dependencies

### Step 3: Verify .env Configuration

On the droplet:

```bash
ssh root@206.189.118.255

cd /opt/omega-dynasty-v6

# Check .env exists
ls -la .env

# Verify it has required API keys (don't display them)
grep -E "HELIUS|BIRDEYE|TELEGRAM|PATRICK" .env | wc -l
# Should output: 8+ (multiple env vars found)

# If .env missing or incomplete, update it:
# See GitHub Secrets: OMEGA_ENV_FILE
```

### Step 4: Verify Service Health Endpoint

Each service needs a `/health` endpoint in its code:

**Example (Go):**
```go
import "net/http"

func main() {
    // ... other setup ...
    
    // Health check endpoint
    http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
        // Do basic health checks here
        // Check database connection, API keys, etc.
        
        w.Header().Set("Content-Type", "application/json")
        w.WriteHeader(http.StatusOK)
        fmt.Fprint(w, `{"status": "healthy"}`)
    })
    
    // Start server
    http.ListenAndServe(":3005", nil)
}
```

**Example (Python/FastAPI):**
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health():
    # Do basic health checks
    return {"status": "healthy"}
```

### Step 5: Monitor Recovery

```bash
# Run continuous monitoring
python bin/monitor.py watch 30

# Watch for "Status change" messages indicating recovery
```

Once services return to **HEALTHY**, trading will resume.

---

## Permanent Configuration

### Deploy Monitoring to Droplet

Copy monitoring system to droplet for local use:

```bash
# From droplet
cd /opt/omega-dynasty-v6

# Option 1: Pull from git
git pull origin main

# Option 2: Manual copy
scp -r core root@206.189.118.255:/opt/omega-dynasty-v6/
scp -r bin root@206.189.118.255:/opt/omega-dynasty-v6/
scp -r requirements.txt root@206.189.118.255:/opt/omega-dynasty-v6/
```

Then on droplet:

```bash
cd /opt/omega-dynasty-v6

# Install dependencies
pip install -r requirements.txt

# Run monitoring
python bin/monitor.py status
```

### Setup Automatic Monitoring

Create a cron job to check health every 5 minutes:

```bash
# On droplet
crontab -e

# Add this line:
*/5 * * * * cd /opt/omega-dynasty-v6 && python bin/monitor.py alert 2>/dev/null
```

This sends health report to Telegram every 5 minutes.

### Setup Telegram Alerts

Ensure `.env` has:

```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

Once configured, bot will send:
- ✅ Green alerts when services recover
- 🚨 Red alerts when services go down
- 📊 Health reports every 5 minutes

---

## Testing

### Run Monitoring Tests

```bash
pip install pytest pytest-asyncio

pytest tests/test_monitoring.py -v
```

### Manual Testing

```bash
# Test against local services
python bin/monitor.py status

# Test with custom droplet
BASE_URL=http://your-ip python bin/monitor.py status

# Test alert to Telegram
python bin/monitor.py alert
```

---

## Architecture Decisions

### Why Health Checks Fail

1. **Startup Race Conditions**
   - Services start before database/Redis ready
   - Health checks run before initialization complete
   - **Solution:** `start_period: 60s` grace period

2. **Timeout Configuration**
   - Default 10s timeout too strict for slow services
   - HTTP clients have separate timeout
   - **Solution:** `timeout: 15s` health check, async endpoints

3. **Missing Environment Variables**
   - API keys not loaded → service crashes → health check fails
   - **Solution:** Verify `.env` has all required keys

4. **Port Binding Issues**
   - Service binding to 0.0.0.0 vs localhost
   - Container network namespacing
   - **Solution:** Test with `curl` from outside container

### Why 8 Containers Show Unhealthy

**Pattern:** All agent services unhealthy = system-wide issue

**Likely causes (in priority order):**
1. API key authentication failure (Helius, Birdeye)
2. Database initialization delay (postgres not ready)
3. Redis connection failure
4. Docker health check timeout too strict
5. Service code missing `/health` endpoint

### Solution Priority

1. ✅ **Immediate:** Restart containers + verify health checks pass
2. ✅ **Short-term:** Fix docker-compose.yml health check settings
3. ✅ **Medium-term:** Add `/health` endpoints to services if missing
4. ✅ **Long-term:** Implement distributed health monitoring (Prometheus)

---

## Metrics & Observability

### Health Metrics Tracked

For each service, we track:
- **Uptime %** - Percentage of checks that passed
- **Response Time** - Average ms per request
- **Error Rate** - % of failed checks
- **Last Failure** - When it last failed
- **Consecutive Failures** - How many checks in a row failed

### Trend Analysis

Get uptime over time windows:

```python
monitor = get_monitor()

# 1-minute uptime
trend_1m = monitor.get_trend("omega_patrick", window_seconds=60)
# {"uptime_pct": 95.5, "samples": 19, "avg_response_time_ms": 45.2}

# 5-minute uptime
trend_5m = monitor.get_trend("omega_patrick", window_seconds=300)

# 1-hour uptime
trend_1h = monitor.get_trend("omega_patrick", window_seconds=3600)
```

---

## Next Steps

1. **Run diagnostics now:**
   ```bash
   python bin/monitor.py diagnose
   ```

2. **SSH to droplet and check logs:**
   ```bash
   docker logs omega_patrick --tail 100 | grep -i error
   ```

3. **Apply fixes from diagnostic output**

4. **Restart containers:**
   ```bash
   docker compose restart
   docker ps
   ```

5. **Monitor recovery:**
   ```bash
   python bin/monitor.py watch 30
   ```

6. **Once healthy, commit fixes to repo:**
   ```bash
   git add docker-compose.yml .env
   git commit -m "Fix health checks - extend timeout & grace period"
   git push origin main
   ```

---

## Questions?

- **What's a health check?** Simple HTTP GET that returns 200 if service is ready
- **Why multiple services failing?** Usually system-wide issue (API key, database, env var)
- **How long to fix?** Usually 5-10 minutes (restart + config update)
- **Will trading resume?** Once services return to HEALTHY status ✅

🔱 **CHUKUA KONTROLI YOTE** 🔱

The swarm will be healthy and operational.
