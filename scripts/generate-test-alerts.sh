#!/bin/bash
# ==============================================================================
# HealthGuard Ops - Test Alert Generator
# ==============================================================================
# Generates continuous test alerts for demo/testing purposes

echo "🚀 Starting Test Alert Generator"
echo "Press Ctrl+C to stop"
echo ""

count=0

while true; do
  # Generate random alert
  response=$(curl -s -X POST http://localhost:8001/alerts/manual)

  if echo "$response" | grep -q "alert_id"; then
    count=$((count + 1))
    alert_id=$(echo "$response" | grep -o '"alert_id":"[^"]*"' | cut -d'"' -f4)
    severity=$(echo "$response" | grep -o '"severity":"[^"]*"' | cut -d'"' -f4)
    echo "✅ Alert #$count: $alert_id ($severity)"
  else
    echo "❌ Failed to create alert"
  fi

  # Wait 3-10 seconds between alerts (random)
  sleep_time=$((3 + RANDOM % 8))
  sleep $sleep_time
done
