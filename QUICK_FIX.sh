#!/bin/bash
# 🔱 BROTHERHOOD OMEGA SWARM HEALTH CHECK - QUICK REFERENCE
# Print this out and post it next to your monitor!
#
# CURRENT STATUS: 8 out of 11 containers marked (unhealthy)
# ROOT CAUSE: Health checks timing out or services not responding
# SOLUTION: This guide

# =============================================================================
# SECTION 1: IMMEDIATE DIAGNOSTICS (Run this first)
# =============================================================================

# SSH to droplet
ssh root@206.189.118.255

# Go to omega directory
cd /opt/omega-dynasty-v6

# Check which containers are unhealthy
echo "=== CONTAINER HEALTH ==="
docker ps --format "table {{.Names}}\t{{.Status}}"

# Check system resources
echo -e "\n=== SYSTEM RESOURCES ==="
docker stats --no-stream

# Get detailed health info
echo -e "\n=== HEALTH DETAILS ==="
docker ps --format "table {{.Names}}\t{{.Status}}" | grep unhealthy

# =============================================================================
# SECTION 2: CHECK SERVICE LOGS (Diagnose specific services)
# =============================================================================

# Patrick (Scanner)
echo "=== PATRICK LOGS (last 100 lines) ==="
docker logs omega_patrick --tail 100 | head -50

# Look for these error patterns:
# - "Unauthorized" or "invalid api key" → Fix .env HELIUS_API_KEY
# - "Connection refused" → Service not binding to port
# - "database" or "postgres" → Wait for DB to be ready
# - "error" or "panic" → Service crashed on startup

# DJ (Executor)
echo "=== DJ LOGS ==="
docker logs omega_dj --tail 100 | head -50

# Bossman (Risk Guardian)
echo "=== BOSSMAN LOGS ==="
docker logs omega_bossman --tail 100 | head -50

# Hashim (Compounder)
echo "=== HASHIM LOGS ==="
docker logs omega_hashim --tail 100 | head -50

# =============================================================================
# SECTION 3: TEST CONNECTIVITY (Can we reach the services?)
# =============================================================================

# Test each service's health endpoint
echo "=== CONNECTIVITY TEST ==="

echo "Testing PATRICK (3005)..."
curl -v http://localhost:3005/health

echo "Testing DJ (3003)..."
curl -v http://localhost:3003/health

echo "Testing BOSSMAN (3006)..."
curl -v http://localhost:3006/health

echo "Testing HASHIM (3004)..."
curl -v http://localhost:3004/health

echo "Testing Dashboard (8082)..."
curl -v http://localhost:8082/health

echo "Testing AgentBus (8081)..."
curl -v http://localhost:8081/health

# If you see "Connection refused" → Service not listening
# If you see "Timeout" → Service listening but not responding
# If you see "HTTP 500" → Service has runtime error

# =============================================================================
# SECTION 4: CHECK CONFIGURATION (Is .env correct?)
# =============================================================================

echo "=== CONFIGURATION CHECK ==="

# Check if .env exists
if [ -f .env ]; then
    echo "✅ .env file exists"
    echo "   Size: $(wc -c < .env) bytes"
else
    echo "❌ .env file MISSING - This is the problem!"
    echo "   Create it with all required API keys"
fi

# Check for required API keys (don't show values)
echo -e "\n=== API KEYS STATUS ==="
grep "HELIUS_API_KEY" .env && echo "✅ HELIUS_API_KEY set" || echo "❌ HELIUS_API_KEY missing"
grep "BIRDEYE_API_KEY" .env && echo "✅ BIRDEYE_API_KEY set" || echo "❌ BIRDEYE_API_KEY missing"
grep "TELEGRAM_BOT_TOKEN" .env && echo "✅ TELEGRAM_BOT_TOKEN set" || echo "❌ TELEGRAM_BOT_TOKEN missing"

# =============================================================================
# SECTION 5: FIX STEPS (In priority order)
# =============================================================================

echo -e "\n=== FIXING HEALTH CHECKS ==="
echo "Step 1: Restart all containers"
docker compose restart
echo "   ⏳ Waiting 60 seconds for services to initialize..."
sleep 60

echo "Step 2: Check health again"
docker ps | grep -E "omega_patrick|omega_dj|omega_bossman|omega_hashim|omega_dashboard"

echo "Step 3: If still unhealthy..."
echo "   a) Check logs for specific errors (scroll up)"
echo "   b) Check that .env has valid API keys"
echo "   c) Restart Docker daemon: systemctl restart docker"
echo "   d) Review docker-compose.yml healthcheck settings"

# =============================================================================
# SECTION 6: PERMANENT FIX (Update docker-compose.yml)
# =============================================================================

echo -e "\n=== PERMANENT FIX ==="
echo "Edit docker-compose.yml for each service and ensure this section:"
cat <<'EOF'

  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:PORT/health"]
    interval: 45s       # Check every 45 seconds
    timeout: 15s        # Wait 15 seconds for response
    retries: 5          # Allow 5 failures
    start_period: 60s   # ← THIS IS THE KEY FIX

EOF

# =============================================================================
# SECTION 7: MONITOR & VERIFY (From your laptop)
# =============================================================================

echo -e "\n=== MONITORING (Run from your laptop) ==="
echo "Check health from external monitoring:"
echo "  python bin/monitor.py status"
echo ""
echo "Continuous monitoring:"
echo "  python bin/monitor.py watch 30"
echo ""
echo "Diagnose issues:"
echo "  python bin/monitor.py diagnose"
echo ""
echo "Send alert to Telegram:"
echo "  python bin/monitor.py alert"

# =============================================================================
# SECTION 8: COMMON ISSUES & QUICK FIXES
# =============================================================================

echo -e "\n=== COMMON ISSUES & QUICK FIXES ==="

cat <<'EOF'

🔴 ISSUE: "Timeout (unreachable)"
   - Service not responding on port
   - Likely: Crashed or still initializing
   FIX:
   - Wait 60s after restart
   - Check logs: docker logs omega_patrick --tail 100
   - Increase start_period in docker-compose.yml

🔴 ISSUE: "Connection refused (service not listening)"
   - Service crashed immediately after start
   - Likely: Missing env var or API key
   FIX:
   - Check .env file has all required keys
   - Check logs for "error" or "panic"
   - docker restart omega_patrick

🔴 ISSUE: "HTTP 500"
   - Service running but health check failing
   - Likely: Database/Redis not ready, bad config
   FIX:
   - Check if postgres/redis are healthy: docker ps
   - Wait 30s more for databases to initialize
   - Check logs for connection errors

🔴 ISSUE: Multiple services unhealthy at once
   - System-wide issue, not individual service problem
   - Likely: API key invalid, database down, network issue
   FIX:
   1. Check system resources: docker stats
   2. Verify .env has valid credentials
   3. Check postgres/redis health: docker ps
   4. Restart everything: docker-compose restart

EOF

# =============================================================================
# SECTION 9: VALIDATE SUCCESS
# =============================================================================

echo -e "\n=== SUCCESS CRITERIA ==="
echo "✅ All containers show 'healthy' or 'Up' (not 'unhealthy')"
echo "✅ All agents respond to health checks: curl http://localhost:300X/health"
echo "✅ Dashboard loads: curl http://localhost:8082/health"
echo "✅ Logs show no 'error' or 'panic' messages"
echo "✅ Python monitoring shows all green: python bin/monitor.py status"

# =============================================================================
# SECTION 10: NEXT STEPS (After everything is healthy)
# =============================================================================

echo -e "\n=== NEXT STEPS ==="
cat <<'EOF'

1. Commit fixes to git
   git add docker-compose.yml .env
   git commit -m "Fix health checks - extend startup grace period"
   git push origin main

2. Deploy monitoring to droplet
   scp bin/monitor.py root@206.189.118.255:/opt/omega-dynasty-v6/
   scp core/monitoring.py root@206.189.118.255:/opt/omega-dynasty-v6/core/
   scp core/alerts.py root@206.189.118.255:/opt/omega-dynasty-v6/core/

3. Setup automatic alerts (cron)
   crontab -e
   # Add: */5 * * * * cd /opt/omega-dynasty-v6 && python bin/monitor.py alert

4. Monitor dashboard recovery
   python bin/monitor.py watch 30

5. Once stable for 24+ hours, consider enabling live trading

EOF

echo -e "\n=== END OF QUICK REFERENCE ==="
echo "🔱 CHUKUA KONTROLI YOTE - The swarm will be healthy"
