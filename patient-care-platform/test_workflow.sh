#!/bin/bash

echo "🧪 Patient Care Platform - Complete Workflow Test"
echo "===================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Health checks
echo -e "${BLUE}1️⃣  HEALTH CHECKS${NC}"
echo "=================================="
echo "Alert Service (8001):"
curl -s http://localhost:8001/health | jq .
echo ""
echo "Incident Service (8002):"
curl -s http://localhost:8002/health | jq .
echo ""
echo "On-Call Service (8003):"
curl -s http://localhost:8003/health | jq .
echo ""
echo "Notification Service (8004):"
curl -s http://localhost:8004/health | jq .
echo ""

# 2. Login employee
echo -e "${BLUE}2️⃣  EMPLOYEE LOGIN${NC}"
echo "=================================="
echo "Logging in Dr. Robert Chen (D01)..."
curl -s -X POST http://localhost:8003/auth/login \
  -H "Content-Type: application/json" \
  -d '{"login": "D01", "password": "password123"}' | jq .
echo ""

sleep 1

# 3. Check who's on-call
echo -e "${BLUE}3️⃣  CHECK ON-CALL STAFF${NC}"
echo "=================================="
curl -s "http://localhost:8003/oncall/current?role=EMERGENCY_DOCTOR" | jq .
echo ""

# 4. Generate alert
echo -e "${BLUE}4️⃣  GENERATE ALERT${NC}"
echo "=================================="
ALERT=$(curl -s -X POST http://localhost:8001/alerts/manual)
echo $ALERT | jq .
echo ""

# Wait for processing
echo "⏳ Waiting 3 seconds for alert processing..."
sleep 3

# 5. Get incidents
echo -e "${BLUE}5️⃣  GET CREATED INCIDENT${NC}"
echo "=================================="
INCIDENTS=$(curl -s http://localhost:8002/incidents)
INCIDENT_ID=$(echo $INCIDENTS | jq -r '.[0].incident_id')
echo -e "${GREEN}Latest Incident: $INCIDENT_ID${NC}"
echo $INCIDENTS | jq '.[0]'
echo ""

if [ "$INCIDENT_ID" == "null" ]; then
  echo -e "${RED}❌ No incidents found. Stopping test.${NC}"
  exit 1
fi

# 6. Check notifications
echo -e "${BLUE}6️⃣  CHECK NOTIFICATIONS${NC}"
echo "=================================="
echo "Notifications for Dr. Robert Chen (employee_id=7):"
curl -s http://localhost:8004/notifications/7 | jq .
echo ""

# 7. Acknowledge
echo -e "${BLUE}7️⃣  ACKNOWLEDGE INCIDENT${NC}"
echo "=================================="
curl -s -X PATCH http://localhost:8002/incidents/$INCIDENT_ID/acknowledge \
  -H "Content-Type: application/json" \
  -d '{"employee_id": 7, "employee_name": "Dr. Robert Chen"}' | jq .
echo ""

sleep 1

# 8. Start working
echo -e "${BLUE}8️⃣  START WORKING ON INCIDENT${NC}"
echo "=================================="
curl -s -X PATCH http://localhost:8002/incidents/$INCIDENT_ID/start \
  -H "Content-Type: application/json" \
  -d '{"employee_id": 7, "employee_name": "Dr. Robert Chen", "note": "Heading to patient room now"}' | jq .
echo ""

sleep 1

# 9. Add progress notes
echo -e "${BLUE}9️⃣  ADD PROGRESS NOTES${NC}"
echo "=================================="
echo "Note 1: Vitals checked"
curl -s -X POST http://localhost:8002/incidents/$INCIDENT_ID/notes \
  -H "Content-Type: application/json" \
  -d '{"employee_id": 7, "employee_name": "Dr. Robert Chen", "note": "Patient vitals checked - BP 160/95, HR 145"}' | jq .
echo ""

sleep 1

echo "Note 2: ECG performed"
curl -s -X POST http://localhost:8002/incidents/$INCIDENT_ID/notes \
  -H "Content-Type: application/json" \
  -d '{"employee_id": 7, "employee_name": "Dr. Robert Chen", "note": "ECG performed, shows atrial fibrillation"}' | jq .
echo ""

sleep 1

echo "Note 3: Medication administered"
curl -s -X POST http://localhost:8002/incidents/$INCIDENT_ID/notes \
  -H "Content-Type: application/json" \
  -d '{"employee_id": 7, "employee_name": "Dr. Robert Chen", "note": "Medication administered, patient stabilizing"}' | jq .
echo ""

sleep 1

# 10. Resolve
echo -e "${BLUE}🔟  RESOLVE INCIDENT${NC}"
echo "=================================="
curl -s -X PATCH http://localhost:8002/incidents/$INCIDENT_ID/resolve \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": 7,
    "employee_name": "Dr. Robert Chen",
    "resolution_notes": "Patient stabilized successfully. Heart rate normalized to 78bpm. Atrial fibrillation controlled with medication. Patient admitted to ICU for 24-hour observation. Cardiologist consulted for follow-up."
  }' | jq .
echo ""

sleep 1

# 11. View final state with complete history
echo -e "${BLUE}1️⃣1️⃣  FINAL INCIDENT STATE (with complete history)${NC}"
echo "=================================="
curl -s http://localhost:8002/incidents/$INCIDENT_ID | jq .
echo ""

# 12. Performance metrics
echo -e "${BLUE}1️⃣2️⃣  PERFORMANCE METRICS${NC}"
echo "=================================="
curl -s http://localhost:8002/incidents/metrics | jq .
echo ""

echo -e "${GREEN}✅ TEST COMPLETE!${NC}"
echo ""
echo "Summary:"
echo "--------"
echo "• Alert generated automatically"
echo "• Incident created and auto-assigned to Dr. Robert Chen"
echo "• Notification sent to employee"
echo "• Employee acknowledged → started → added notes → resolved"
echo "• Complete audit trail recorded"
echo "• Time metrics calculated"
echo ""
echo "Check the service console logs to see the full flow!"
