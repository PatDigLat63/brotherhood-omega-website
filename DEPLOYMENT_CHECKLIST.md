# 🔱 DEPLOYMENT CHECKLIST — BROTHERHOOD OMEGA MONITORING

## Pre-Deployment Verification ✅

- [x] PR #20 created and ready to merge
- [x] All Python code syntax validated
- [x] Module imports verified
- [x] No circular dependencies
- [x] Documentation complete (4 files)
- [x] Backwards compatible with existing tools
- [x] Production-ready code

## Deployment Steps

### Step 1: Health Check Configuration (5-10 minutes)

**On Droplet (206.189.118.255):**

```bash
ssh root@206.189.118.255
cd /opt/omega-dynasty-v6
```

**Edit docker-compose.yml for ALL 9 agent services:**

Find each service and update the health check:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:PORT/health"]
  interval: 45s
  timeout: 15s
  retries: 5
  start_period: 90s    # ← Change from 60s to 90s
```

**Services to update:**
- [ ] omega_patrick (port 3005)
- [ ] omega_dj (port 3003)
- [ ] omega_bossman (port 3006)
- [ ] omega_hashim (port 3004)
- [ ] omega_hustle_bridge (port 3001)
- [ ] omega_oracle_engine (port 3002)
- [ ] omega_dashboard (port 8082)
- [ ] omega_agentbus (port 8081)
- [ ] omega_telegram_bot (port 8083)

**Restart containers:**

```bash
docker compose down
docker compose up -d --remove-orphans
sleep 90
docker ps
```

**Verify:** All services show `(healthy)` status

### Step 2: Deploy Latest Code (1-2 minutes)

```bash
cd /opt/omega-dynasty-v6
git pull origin main
pip install -r requirements.txt
```

**Verify:** No errors during installation

### Step 3: Test Monitoring (3-5 minutes)

```bash
# Test CLI monitoring
python bin/monitor.py status

# Expected: All ✅ HEALTHY
```

### Step 4: Test Cron Script (2-3 minutes)

```bash
# Test cron monitoring
python bin/monitor_cron.py

# Expected: 
# - Sends health report to Telegram
# - Creates logs/monitor_state.json
# - Logs to logs/monitor.log
```

**Check Telegram:** Should receive health report

### Step 5: Setup Cron Alerts (1-2 minutes)

```bash
crontab -e

# Add this line at the end:
*/5 * * * * cd /opt/omega-dynasty-v6 && python bin/monitor_cron.py >> /tmp/monitor.log 2>&1

# Save and exit
```

**Verify cron entry:**

```bash
crontab -l
```

Should show the new line.

### Step 6: Monitor the Monitor (5 minutes)

```bash
# Watch logs in real-time
tail -f /opt/omega-dynasty-v6/logs/monitor.log

# Should see entries every 5 minutes after cron runs
# Or entries every 30 seconds if continuous monitoring
```

## Post-Deployment Verification

### Immediate Checks (First 5 minutes)

- [ ] `docker ps` - All services (healthy)
- [ ] `python bin/monitor.py status` - All ✅ HEALTHY
- [ ] Monitoring logs: `tail -f logs/monitor.log` - No errors
- [ ] State file: `cat logs/monitor_state.json` - Valid JSON

### Cron Verification (First 10 minutes)

- [ ] Wait for next cron run (within 5 minutes)
- [ ] Check Telegram for health report
- [ ] Verify state file updated: `stat logs/monitor_state.json`
- [ ] Check system cron logs: `grep CRON /var/log/syslog | tail`

### Telegram Bot Testing (If integrated)

- [ ] Send `/swarm` command → Receive swarm status
- [ ] Send `/agent patrick` → Receive agent status
- [ ] Send `/metrics` → Receive trading metrics
- [ ] Send `/alerts on` → Receive confirmation
- [ ] Send `/help` → Receive command reference

### 24-Hour Stability Check

- [ ] Review logs: `tail -100 logs/monitor.log`
- [ ] Check state file history
- [ ] Verify no alert spam (only on status changes)
- [ ] Confirm cron ran ~288 times (5 min intervals × 24 hours)

## Troubleshooting During Deployment

### Issue: Services Still Unhealthy After 90s

**Solution:**
```bash
docker logs omega_patrick --tail 100
curl -v http://localhost:3005/health
docker ps -a | grep omega_patrick
```

Check for:
- API key errors in logs
- Database connection issues
- Port binding problems

### Issue: Health Check Fix Not Applied

**Verify:**
```bash
docker inspect omega_patrick | grep -A 5 "Health"
```

Should show: `"StartPeriod": 90000000000` (90 seconds in nanoseconds)

### Issue: Telegram Alerts Not Sending

**Verify:**
```bash
grep TELEGRAM .env
python -c "from core.alerts import get_alerter; asyncio.run(get_alerter().send_message('Test'))"
```

Check:
- TELEGRAM_BOT_TOKEN is valid
- TELEGRAM_CHAT_ID is correct
- Telegram API is accessible

### Issue: Cron Not Running

**Verify:**
```bash
crontab -l
systemctl status cron
grep CRON /var/log/syslog | tail -20
```

Solutions:
- Check crontab syntax: `crontab -l`
- Verify path is absolute: Use full paths in cron
- Check permissions on bin/monitor_cron.py
- Verify Python path: `which python`

## Success Criteria

After all deployment steps, verify:

- [ ] `docker ps` shows all services (healthy)
- [ ] `python bin/monitor.py status` shows all ✅ HEALTHY  
- [ ] `python bin/monitor_cron.py` sends alert to Telegram
- [ ] `crontab -l` shows */5 entry
- [ ] Telegram `/swarm` command works (if bot integrated)
- [ ] Telegram `/agent NAME` command works (if bot integrated)
- [ ] Monitoring logs show no errors
- [ ] State file updates every 5 minutes
- [ ] No excessive alert spam

## Rollback Procedure

If anything goes wrong:

```bash
# Restore original health check (60s start_period)
git checkout docker-compose.yml

# Restart containers
docker compose down
docker compose up -d

# Remove cron job
crontab -e
# Delete the monitoring line

# Remove new files (optional)
rm core/telegram_bot.py bin/monitor_cron.py
```

## Support Files

Reference these if issues arise:

- `DEPLOYMENT_MONITORING.md` - Complete deployment guide
- `IMPLEMENTATION_SUMMARY.md` - What was built
- `QUICK_START_MONITORING.md` - Quick reference
- `MONITORING.md` - Original architecture docs

## Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Phase 1: Health Checks | 5-10 min | Execute now |
| Phase 2: Deploy Code | 1-2 min | After Phase 1 ✓ |
| Phase 3: Test CLI | 3-5 min | After Phase 2 ✓ |
| Phase 4: Test Cron | 2-3 min | After Phase 3 ✓ |
| Phase 5: Setup Cron | 1-2 min | After Phase 4 ✓ |
| Phase 6: Verify | 5 min | Ongoing ✓ |

**Total Time: ~20-30 minutes**

## Automation Script (Optional)

Save as `deploy_monitoring.sh`:

```bash
#!/bin/bash
set -e

cd /opt/omega-dynasty-v6

echo "🔱 Starting monitoring deployment..."

# Phase 2: Deploy code
echo "📥 Pulling latest code..."
git pull origin main
pip install -r requirements.txt

# Phase 3: Test CLI
echo "✅ Testing CLI monitoring..."
python bin/monitor.py status

# Phase 4: Test cron
echo "📨 Testing cron script..."
python bin/monitor_cron.py

# Phase 5: Setup cron
echo "⏰ Setting up cron job..."
(crontab -l 2>/dev/null; echo "*/5 * * * * cd /opt/omega-dynasty-v6 && python bin/monitor_cron.py") | crontab -

# Phase 6: Verify
echo "✅ Verifying setup..."
crontab -l | grep monitor_cron.py

echo ""
echo "🎉 Deployment complete!"
echo "   • Code deployed"
echo "   • CLI tools tested"
echo "   • Cron job enabled"
echo ""
echo "Monitor logs with: tail -f logs/monitor.log"
```

Usage:
```bash
chmod +x deploy_monitoring.sh
./deploy_monitoring.sh
```

## Final Notes

- Phase 1 (health check fix) must be done manually (requires docker-compose.yml edit)
- Phases 2-6 can be automated with the script above
- After deployment, monitoring runs automatically every 5 minutes
- Logs are saved to: `/opt/omega-dynasty-v6/logs/monitor.log`
- State file location: `/opt/omega-dynasty-v6/logs/monitor_state.json`

---

🔱 **CHUKUA KONTROLI YOTE** 🔱

Start Phase 1 now. The system is fully configured and ready.
