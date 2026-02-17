#!/usr/bin/env python3
"""
Script to add Prometheus metrics to incident-management service.
This adds MTTA and MTTR histogram metrics as required by the hackathon.
"""

import os
import sys

# Prometheus metrics code to add to incident-management/app/main.py

METRICS_IMPORTS = """from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST"""

METRICS_DEFINITIONS = """
# Prometheus Metrics
incidents_total = Counter('incidents_total', 'Total incidents', ['status'])
incident_mtta_seconds = Histogram('incident_mtta_seconds', 'Mean Time To Acknowledge in seconds', buckets=[30, 60, 120, 300, 600, 1800, 3600])
incident_mttr_seconds = Histogram('incident_mttr_seconds', 'Mean Time To Resolve in seconds', buckets=[300, 600, 1800, 3600, 7200, 14400, 28800])
"""

METRICS_ENDPOINT = """
@app.route('/metrics', methods=['GET'])
def metrics():
    \"\"\"Prometheus metrics endpoint.\"\"\"
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
"""

def main():
    print("✅ Prometheus metrics definitions created")
    print("\nAdd these to incident-management/app/main.py:")
    print("\n1. Add to imports:")
    print(METRICS_IMPORTS)
    print("\n2. Add after app initialization:")
    print(METRICS_DEFINITIONS)
    print("\n3. Add metrics endpoint:")
    print(METRICS_ENDPOINT)
    print("\n4. Increment incidents_total when creating incidents:")
    print("   incidents_total.labels(status='open').inc()")
    print("\n5. Record MTTA when acknowledging:")
    print("   mtta = (acknowledged_at - created_at).total_seconds()")
    print("   incident_mtta_seconds.observe(mtta)")
    print("\n6. Record MTTR when resolving:")
    print("   mttr = (resolved_at - created_at).total_seconds()")
    print("   incident_mttr_seconds.observe(mttr)")

if __name__ == '__main__':
    main()
