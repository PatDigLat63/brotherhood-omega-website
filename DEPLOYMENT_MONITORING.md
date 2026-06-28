# 🔱 BROTHERHOOD OMEGA SWARM MONITORING — DEPLOYMENT GUIDE

Complete guide to deploy Docker Swarm monitoring with Telegram bot commands and automatic cron alerts.

## Overview

This setup provides:
- ✅ Real-time health checks for all 11 containers
- ✅ Telegram bot commands (`/swarm`, `/agent`, `/metrics`, `/alerts`)
- ✅ Automatic alerts every 5 minutes via cron
- ✅ Alert cooldown (prevents alert flooding)
- ✅ Lightweight (runs on 2GB droplet)

## Prerequisites

Before starting, ensure on your droplet (`206.189.118.255`):
- Docker and docker-compose installed
- Python 3.8+ with pip
- SSH access to droplet as root
- Telegram bot token (from @BotFather)
- Telegram chat ID (your user ID or channel ID)

## Phase 1: Update Docker Compose (Health Check Fix)

### Step 1: SSH to droplet

```bash
ssh root@206.189.118.255
cd /opt/omega-dynasty-v6
```

### Step 2: Update docker-compose.yml

Edit your `docker-compose.yml` and ensure EVERY agent service has:

```yaml
services:
  omega_patrick:
    # ... other config ...
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3005/health"]
      interval: 45s         # Check every 45s
      timeout: 15s          # Wait 15s for response
      retries: 5            # Allow 5 failures
      start_period: 90s     # ⭐ CRITICAL: 90 second grace period
    
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
```

**Apply to these services:**
- omega_patrick (port 3005)
- omega_dj (port 3003)
- omega_bossman (port 3006)
- omega_hashim (port 3004)
- omega_hustle_bridge (port 3001)
- omega_oracle_engine (port 3002)
- omega_dashboard (port 8082)
- omega_agentbus (port 8081)
- omega_telegram_bot (port 8083)

**Why 90s start_period?**
- Services need time to: load config, connect to DB, validate API keys
- Strict health checks prevent initialization → mark unhealthy
- 90s gives enough time without being too loose

### Step 3: Restart containers

```bash
docker compose down
docker compose up -d --remove-orphans

# Wait for services to initialize
sleep 90

# Verify all healthy
docker ps
# All should show: Up 1 min (healthy)
```

### Step 4: Test the monitoring locally

```bash
cd /opt/omega-dynasty-v6

# Install Python dependencies (if not already installed)
pip install -r requirements.txt

# Test status command
python bin/monitor.py status

# Test diagnostics
python bin/monitor.py diagnose

# Expected output:
# ✅ All services healthy - no issues found
```

## Phase 2: Deploy Monitoring Infrastructure

### Step 1: Pull latest code

```bash
cd /opt/omega-dynasty-v6
git pull origin main
```

This brings in:
- `core/telegram_bot.py` - Telegram bot command handlers
- `bin/monitor_cron.py` - Lightweight cron-ready monitoring
- Updated `docker-compose.example.yml` with 90s health checks

### Step 2: Install dependencies

Ensure all Python dependencies are installed:

```bash
pip install -r requirements.txt

# Required packages:
# - httpx (for HTTP health checks)
# - pydantic (for config)
# - python-telegram-bot (for Telegram integration)
```

### Step 3: Verify environment variables

Ensure `.env` on droplet has all required variables:

```bash
# On droplet:
cat .env | grep TELEGRAM

# Should output:
# TELEGRAM_BOT_TOKEN=<your_bot_token>
# TELEGRAM_CHAT_ID=<your_chat_id>
```

**If missing, add them:**

```bash
echo "TELEGRAM_BOT_TOKEN=your_token_here" >> .env
echo "TELEGRAM_CHAT_ID=your_chat_id_here" >> .env
```

## Phase 3: Telegram Bot Commands Setup

The monitoring system now exposes these commands:

### Available Commands

```
/swarm              - Overall swarm health and status
/agent NAME         - Specific agent status (e.g., /agent patrick)
/metrics            - Trading metrics and configuration
/alerts on|off      - Enable/disable monitoring alerts
/help               - Show all commands
```

### Testing Commands

Test each command locally first:

```bash
cd /opt/omega-dynasty-v6

# Test all commands (will send to your Telegram chat)
python bin/monitor.py alert          # Send health report

# Test monitoring (continuous)
python bin/monitor.py watch 30       # Check every 30s
```

### Integration with Existing Bot

If you have an existing Telegram bot handler, integrate like this:

```python
from core.telegram_bot import get_telegram_commands, CommandContext

# In your message handler:
commands = get_telegram_commands()

# Parse command from message
parts = message.text.split()
command = parts[0].lstrip('/')
args = parts[1:] if len(parts) > 1 else []

# Create context
context = CommandContext(
    command=command,
    args=args,
    user_id=str(message.from_user.id),
    chat_id=str(message.chat.id)
)

# Handle command
result = await commands.handle_command(context)
```

## Phase 4: Setup Automatic Cron Alerts

### Option 1: Every 5 Minutes (Recommended)

```bash
# On droplet, edit crontab:
crontab -e

# Add this line:
*/5 * * * * cd /opt/omega-dynasty-v6 && python bin/monitor_cron.py >> /tmp/monitor.log 2>&1
```

This sends a health report to Telegram every 5 minutes (only if status changes).

### Option 2: Every 10 Minutes

```bash
*/10 * * * * cd /opt/omega-dynasty-v6 && python bin/monitor_cron.py
```

### Option 3: Every Minute (Aggressive)

```bash
* * * * * cd /opt/omega-dynasty-v6 && python bin/monitor_cron.py
```

### Option 4: Every 30 Seconds (Very Aggressive)

```bash
# Edit: `crontab -e`
# (Cron doesn't support sub-minute intervals, use systemd timer instead)

# Create `/etc/systemd/system/omega-monitor.service`:
[Unit]
Description=Brotherhood Omega Swarm Monitor
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/omega-dynasty-v6/bin/monitor_cron.py --interval=30
Restart=always
RestartSec=5
User=root
WorkingDirectory=/opt/omega-dynasty-v6

[Install]
WantedBy=multi-user.target

# Enable and start:
systemctl daemon-reload
systemctl enable omega-monitor
systemctl start omega-monitor
```

### Verify Cron Setup

```bash
# Check crontab
crontab -l

# Manually test monitoring script
python /opt/omega-dynasty-v6/bin/monitor_cron.py

# Expected: Sends health report to Telegram and logs to:
# /opt/omega-dynasty-v6/logs/monitor.log
```

## Phase 5: Monitor the Monitor

### View Monitoring Logs

```bash
# Real-time log tail
tail -f /opt/omega-dynasty-v6/logs/monitor.log

# Or via docker
docker logs -f omega_telegram_bot
```

### Check State File

The monitor keeps state in `/opt/omega-dynasty-v6/logs/monitor_state.json`:

```bash
cat /opt/omega-dynasty-v6/logs/monitor_state.json | python -m json.tool
```

Shows:
- Last check timestamp
- Last overall status
- Per-service status history

### Manual Health Check Anytime

```bash
# Full status report
python bin/monitor.py status

# Verbose diagnostics
python bin/monitor.py diagnose

# Send alert immediately
python bin/monitor.py alert
```

## Troubleshooting

### Services Still Marked Unhealthy After 90s

```bash
# 1. Check if service is actually running
docker ps | grep omega_patrick

# 2. Check logs for errors
docker logs omega_patrick --tail 100 | head -50

# 3. Test health endpoint manually
curl -v http://localhost:3005/health

# 4. Check port binding
netstat -tlnp | grep 3005

# 5. Restart service
docker restart omega_patrick
```

### Telegram Alerts Not Sending

```bash
# 1. Verify bot token and chat ID are correct
grep TELEGRAM .env

# 2. Test sending manually
python -c "
import asyncio
from core.alerts import get_alerter
alerter = get_alerter()
asyncio.run(alerter.send_message('Test message'))
"

# 3. Check logs for errors
grep -i telegram /opt/omega-dynasty-v6/logs/monitor.log
```

### Cron Not Running

```bash
# 1. Verify cron syntax
crontab -l

# 2. Check cron service
systemctl status cron

# 3. Test manually
cd /opt/omega-dynasty-v6 && python bin/monitor_cron.py

# 4. Check system cron log
grep CRON /var/log/syslog | tail -20
```

## Health Check Endpoints Required

Each service must implement a `/health` endpoint that returns:

**Go Example:**
```go
http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
    // Quick health checks
    if !isConnectedToDatabase() {
        w.WriteHeader(http.StatusServiceUnavailable)
        return
    }
    if !isValidAPIKey() {
        w.WriteHeader(http.StatusForbidden)
        return
    }
    
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(http.StatusOK)
    json.NewEncoder(w).Encode(map[string]string{"status": "healthy"})
})
```

**Python/FastAPI Example:**
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health():
    # Do health checks
    if not await db.is_connected():
        return {"status": "unhealthy"}, 503
    
    return {"status": "healthy"}, 200
```

## Architecture Summary

```
┌─────────────────────────────────────────────────────────┐
│                  Docker Swarm                            │
│  11 Containers (9 agents + postgres + redis)            │
└──────────────────────┬──────────────────────────────────┘
                       │ Health checks every 45s
                       ↓
┌─────────────────────────────────────────────────────────┐
│         core/monitoring.py (SwarmMonitor)               │
│  - Checks all services in parallel                       │
│  - Tracks history (uptime, response time)                │
│  - Calculates health percentage                          │
└──────────────────────┬──────────────────────────────────┘
                       │
       ┌───────────────┼───────────────┐
       ↓               ↓               ↓
  CLI Tool        Telegram         Cron
  monitor.py      Bot Commands     monitor_cron.py
  (manual)        (interactive)    (automatic)
       │               │               │
       └───────────────┼───────────────┘
                       ↓
               core/alerts.py
                 (Telegram API)
                       │
                       ↓
            Telegram Chat/Channel
```

## Next Steps

1. **Immediate:** Apply health check fix (Phase 1)
2. **Short-term:** Deploy monitoring infrastructure (Phase 2)
3. **Medium-term:** Setup Telegram commands (Phase 3)
4. **Long-term:** Enable cron alerts (Phase 4)

Once all phases complete:
- ✅ Monitor swarm anytime with `/swarm` command
- ✅ Check specific agents with `/agent patrick`
- ✅ View metrics with `/metrics`
- ✅ Automatic alerts every 5 minutes
- ✅ Instant notifications on service failures

## Support

For issues, check:
1. Monitoring logs: `/opt/omega-dynasty-v6/logs/monitor.log`
2. Docker logs: `docker logs -f omega_service_name`
3. Telegram configuration: `grep TELEGRAM .env`
4. Docker health: `docker ps` (check health status)

🔱 **CHUKUA KONTROLI YOTE** 🔱

The swarm is fully observable and recoverable. Execute the phases now.
