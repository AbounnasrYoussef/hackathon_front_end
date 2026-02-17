#!/bin/bash

echo "🏥 Initializing HealthGuard Ops Project Structure..."

# 1. Create Directory Structure
mkdir -p services/alert-ingestion/app/tests
mkdir -p services/incident-management
mkdir -p services/oncall-service/app/tests
mkdir -p services/notification-service
mkdir -p services/web-ui/src
mkdir -p database
mkdir -p monitoring/prometheus
mkdir -p monitoring/grafana-dashboards
mkdir -p scripts
mkdir -p init-scripts

# 2. Create Placeholder Files if they don't exist
touch monitoring/prometheus/prometheus.yml
touch monitoring/prometheus/alert.rules.yml

# 3. Set Permissions (Crucial for Linux/Docker volumes)
chmod -R 755 scripts/
mkdir -p .docker-data/postgres .docker-data/redis .docker-data/prometheus .docker-data/grafana
chmod -R 777 .docker-data/

echo "Project structure created!"