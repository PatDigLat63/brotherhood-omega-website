# 🔱 QUICK START — BROTHERHOOD OMEGA MONITORING

## What's New

### 3 New Files Ready for Deployment

```
✅ core/telegram_bot.py       - Telegram bot command handlers
✅ bin/monitor_cron.py         - Cron-ready automated monitoring
✅ DEPLOYMENT_MONITORING.md    - Complete 5-phase deployment guide
✅ IMPLEMENTATION_SUMMARY.md   - What was built and how to use it
```

### Updated Files

```
✅ docker-compose.example.yml  - Health check fixes (90s start_period)
```

---

## 30-Second Overview

**Problem:** 8 containers marked unhealthy due to strict health checks during startup

**Solution:** 4-Phase Implementation
1. Fix health check timeout (90s grace period)
2. Add Telegram bot commands (/swarm, /agent, /metrics)
3. Create cron-ready monitoring (automatic alerts every 5 min)
4. Deploy with documentation

**Status:** ✅ Code Complete, Ready for Deployment

---

## Immediate Next Steps

### Step 1: Apply Health Check Fix (5 minutes)

```bash
ssh root@206.189.118.255
cd /opt/omega-dynasty-v6

# Edit docker-compose.yml
# Change start_period: 60s → 90s on ALL 9 agent services

docker compose down
docker compose up -d
sleep 90
docker ps
# All should show: (healthy)
```

### Step 2: Deploy Latest Code (1 minute)

```bash
git pull origin main
# Automatically includes:
# - core/telegram_bot.py
# - bin/monitor_cron.py
# - DEPLOYMENT_MONITORING.md
```

### Step 3: Setup Cron (1 minute)

```bash
crontab -e
# Add this line:
*/5 * * * * cd /opt/omega-dynasty-v6 && python bin/monitor_cron.py
```

### Step 4: Test (2 minutes)

```bash
python bin/monitor.py status        # Check health
python bin/monitor_cron.py          # Test cron script (sends alert)
# Check Telegram for health report
```

---

## Available Commands

### Via CLI (Manual)

```bash
python bin/monitor.py status          # Show swarm status
python bin/monitor.py diagnose        # Find issues
python bin/monitor.py watch 30        # Monitor continuously (30s interval)
python bin/monitor_cron.py            # Single check (for cron)
```

### Via Telegram Bot

```
/swarm              - Overall health and status
/agent NAME         - Specific agent status (e.g., /agent patrick)
/metrics            - Trading metrics and config
/alerts on|off      - Enable/disable alerts
/help               - Show all commands
```

### Via Cron (Automatic)

```bash
*/5 * * * * python bin/monitor_cron.py   # Every 5 minutes
```

---

## Architecture

```
Docker Swarm (11 containers)
    ↓
core/monitoring.py (health checks)
    ↓
    ├→ bin/monitor.py (CLI - manual)
    ├→ core/telegram_bot.py (Bot - interactive) [NEW]
    ├→ bin/monitor_cron.py (Cron - automatic) [NEW]
    ↓
core/alerts.py (Telegram API)
    ↓
Telegram Chat (alerts & commands)
```

---

## File Locations

```
/opt/omega-dynasty-v6/
├── bin/
│   ├── monitor.py             (existing - CLI tool)
│   └── monitor_cron.py        (NEW - cron monitoring)
├── core/
│   ├── monitoring.py          (existing - health checks)
│   ├── alerts.py              (existing - telegram alerts)
│   ├── telegram_bot.py        (NEW - bot commands)
│   └── config.py              (existing - settings)
├── logs/                       (will be created)
│   ├── monitor.log            (monitoring logs)
│   └── monitor_state.json     (state persistence)
├── docker-compose.yml         (production - needs 90s update)
├── docker-compose.example.yml (example with 90s - UPDATED)
├── MONITORING.md              (existing docs)
├── DEPLOYMENT_MONITORING.md   (NEW - deployment guide)
└── IMPLEMENTATION_SUMMARY.md  (NEW - this project summary)
```

---

## Commands to Execute on Droplet

### Health Check Fix
```bash
cd /opt/omega-dynasty-v6
nano docker-compose.yml
# Update start_period: 90s (9 agent services)
docker compose down && docker compose up -d && sleep 90 && docker ps
```

### Deploy Monitoring
```bash
git pull origin main
pip install -r requirements.txt
python bin/monitor.py status  # Test
```

### Setup Cron
```bash
crontab -e
# Add: */5 * * * * cd /opt/omega-dynasty-v6 && python bin/monitor_cron.py
crontab -l  # Verify
```

### Test Everything
```bash
python bin/monitor.py status          # Should show all ✅
python bin/monitor_cron.py            # Should send alert to Telegram
tail -f logs/monitor.log              # Check logs
```

---

## What Each File Does

### core/telegram_bot.py (472 lines)
- TelegramBotCommands class with 5 commands
- Async command handler
- Per-user alert control
- HTML formatting for Telegram

**Commands:**
- `/swarm` - Overall health
- `/agent NAME` - Specific agent status
- `/metrics` - Trading metrics
- `/alerts on|off` - Alert control
- `/help` - Command reference

### bin/monitor_cron.py (296 lines)
- CronMonitor class for automated checks
- State persistence (JSON file)
- Alert deduplication (only on changes)
- Single-check and continuous modes
- Logging to monitor.log

**Usage:**
- `python bin/monitor_cron.py` - Single check (for cron)
- `python bin/monitor_cron.py --interval=30` - Every 30 seconds
- `python bin/monitor_cron.py --daemon` - Background daemon

### DEPLOYMENT_MONITORING.md (516 lines)
- Complete deployment guide
- 5-phase implementation plan
- Troubleshooting guide
- Health check endpoint examples
- Architecture diagrams

---

## Telegram Bot Integration

If you have an existing bot handler, integrate like this:

```python
from core.telegram_bot import get_telegram_commands, CommandContext

# In your message handler:
commands = get_telegram_commands()

# Parse message
parts = message.text.split()
cmd = parts[0].lstrip('/')
args = parts[1:] if len(parts) > 1 else []

# Create context
ctx = CommandContext(
    command=cmd,
    args=args,
    user_id=str(message.from_user.id),
    chat_id=str(message.chat.id)
)

# Handle
result = await commands.handle_command(ctx)
```

---

## Success Criteria

After deployment, verify:

- [ ] `docker ps` shows all containers (healthy)
- [ ] `python bin/monitor.py status` shows all ✅
- [ ] `python bin/monitor_cron.py` sends alert to Telegram
- [ ] Cron job runs (check `crontab -l`)
- [ ] Telegram `/swarm` command works
- [ ] Telegram `/agent patrick` command works
- [ ] Telegram `/metrics` command works
- [ ] Alerts only send when status changes (no spam)

---

## Troubleshooting

### Services still unhealthy after 90s?
```bash
docker ps -a | grep omega_patrick
docker logs omega_patrick --tail 100
curl -v http://localhost:3005/health
```

### Telegram alerts not working?
```bash
grep TELEGRAM .env
python bin/monitor_cron.py  # Should fail with helpful error
```

### Cron not running?
```bash
crontab -l
systemctl status cron
grep CRON /var/log/syslog | tail
```

---

## Documentation Files

1. **MONITORING.md** (original)
   - Architecture and concepts
   - Quick start commands
   - Testing procedures

2. **DEPLOYMENT_MONITORING.md** (new)
   - Step-by-step 5-phase deployment
   - SSH commands for each phase
   - Troubleshooting guide
   - Integration examples

3. **IMPLEMENTATION_SUMMARY.md** (new)
   - What was built
   - How each component works
   - Deployment checklist
   - Success criteria

---

## Support & Questions

### Check These Files:
- Logs: `tail -f logs/monitor.log`
- State: `cat logs/monitor_state.json`
- Config: `grep TELEGRAM .env`
- Docker: `docker ps` and `docker logs SERVICE`

### Common Issues:
1. **Services unhealthy** → Check logs for startup errors
2. **Alerts not sending** → Verify TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
3. **Cron not running** → Check `crontab -l` and system syslog

---

## Summary

✅ **Phase 1: Health Check Fix** - Config example provided (update droplet manually)
✅ **Phase 2: Monitoring Deploy** - Code ready (git pull)
✅ **Phase 3: Telegram Commands** - Code ready (integrate with existing bot)
✅ **Phase 4: Cron Setup** - Script ready (crontab -e)

**Status:** Ready for immediate deployment. 🔱

---

## Next Phase (Bonus - Optional)

Once all phases working smoothly:

**Phase 5: Visual Dashboard (Optional)**
- Deploy Portainer: `docker run -d -p 9000:9000 portainer/portainer-ce`
- Deploy Prometheus + Grafana for advanced metrics
- Setup PagerDuty/OpsGenie for on-call alerts

For now, focus on Phases 1-4. Telegram + CLI tools are sufficient for 2GB droplet.

---

🔱 **CHUKUA KONTROLI YOTE** 🔱

Ready to deploy. Execute Phase 1 now and report results.
