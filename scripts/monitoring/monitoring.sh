#!/usr/bin/env bash

# Flowlet Platform - Unified Monitoring Script
# This script handles both the setup and the operational monitoring of the
# Flowlet application's observability stack (Prometheus, Grafana, Loki, Jaeger).

# --- Security and Robustness ---
set -euo pipefail

# --- Configuration ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
APP_NAMESPACE="flowlet"
MONITORING_NAMESPACE="monitoring"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HELM_PROMETHEUS_REPO="prometheus-community"
HELM_GRAFANA_REPO="grafana"

# --- Helper Functions ---

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to display usage
usage() {
    echo -e "${BLUE}Usage: $0 [COMMAND] [OPTION]${NC}"
    echo -e "Commands:"
    echo -e "  setup        Install the full monitoring stack (Prometheus, Loki, Jaeger)."
    echo -e "  status       Display the current status of the Flowlet application and monitoring pods."
    echo -e "Options:"
    echo -e "  --app-namespace <name>      The application's Kubernetes namespace (default: flowlet)."
    echo -e "  --mon-namespace <name>      The monitoring stack's Kubernetes namespace (default: monitoring)."
    echo -e "  -h, --help                  Display this help message."
    exit 1
}

# Function to log error and exit
log_error() {
  echo -e "${RED}❌ ERROR: $1${NC}"
  exit 1
}

# Function to set up the monitoring stack
setup_monitoring() {
    echo -e "${BLUE}Setting up monitoring stack in namespace ${MONITORING_NAMESPACE}...${NC}"

    if ! command_exists kubectl || ! command_exists helm; then
        log_error "kubectl and helm are required but not installed."
    fi

    # 1. Add Helm Repositories
    echo -e "${YELLOW}Adding Helm repositories...${NC}"
    helm repo add "${HELM_PROMETHEUS_REPO}" https://prometheus-community.github.io/helm-charts
    helm repo add "${HELM_GRAFANA_REPO}" https://grafana.github.io/helm-charts
    helm repo update

    # 2. Install Prometheus stack (includes Grafana)
    echo -e "${YELLOW}Installing Prometheus stack...${NC}"
    helm upgrade --install prometheus "${HELM_PROMETHEUS_REPO}/kube-prometheus-stack" \
      --namespace "${MONITORING_NAMESPACE}" \
      --create-namespace \
      --set grafana.adminPassword=admin \
      --values ../../kubernetes/monitoring/prometheus-values.yaml \
      --atomic \
      --timeout 10m0s || log_error "Prometheus stack installation failed."

    # 3. Install Loki for log aggregation
    echo -e "${YELLOW}Installing Loki for log aggregation...${NC}"
    helm upgrade --install loki "${HELM_GRAFANA_REPO}/loki-stack" \
      --namespace "${MONITORING_NAMESPACE}" \
      --set grafana.enabled=false \
      --set prometheus.enabled=false \
      --set loki.persistence.enabled=true \
      --set loki.persistence.size=10Gi \
      --atomic \
      --timeout 10m0s || log_error "Loki stack installation failed."

    # 4. Install Jaeger for distributed tracing
    echo -e "${YELLOW}Installing Jaeger operator for distributed tracing...${NC}"
    # Use kubectl apply -f with a specific version URL for security and stability
    kubectl apply -f https://github.com/jaegertracing/jaeger-operator/releases/download/v1.35.0/jaeger-operator.yaml || log_error "Jaeger operator installation failed."
    kubectl wait --for=condition=available deployment/jaeger-operator -n observability --timeout=300s || log_error "Jaeger operator failed to become available."

    # 5. Apply custom dashboards (only if the directory exists in this repository)
    DASHBOARDS_DIR="$PROJECT_ROOT/infrastructure/kubernetes/monitoring/dashboards"
    if [ -d "$DASHBOARDS_DIR" ]; then
        echo -e "${YELLOW}Applying custom dashboards...${NC}"
        kubectl apply -f "$DASHBOARDS_DIR/" -n "${MONITORING_NAMESPACE}" || log_error "Applying custom dashboards failed."
    else
        echo -e "${YELLOW}No custom dashboards directory at ${DASHBOARDS_DIR}; skipping.${NC}"
    fi

    echo -e "${GREEN}=========================================="
    echo -e "Monitoring setup complete!"
    echo -e "==========================================${NC}"
}

# Function to display monitoring status
monitoring_status() {
    echo -e "${BLUE}Displaying Flowlet application and monitoring status...${NC}"

    echo -e "\n${YELLOW}--- Flowlet Application Status (${APP_NAMESPACE}) ---${NC}"
    kubectl get pods -l app=flowlet -n "${APP_NAMESPACE}"
    kubectl get svc -l app=flowlet -n "${APP_NAMESPACE}"
    kubectl get ingress flowlet-ingress -n "${APP_NAMESPACE}" || echo -e "${YELLOW}Ingress 'flowlet-ingress' not found.${NC}"

    echo -e "\n${YELLOW}--- Monitoring Stack Status (${MONITORING_NAMESPACE}) ---${NC}"
    kubectl get pods -l app.kubernetes.io/instance=prometheus -n "${MONITORING_NAMESPACE}"
    kubectl get pods -l app.kubernetes.io/instance=loki -n "${MONITORING_NAMESPACE}"
    kubectl get pods -l app.kubernetes.io/name=jaeger-operator -n observability

    echo -e "\n${GREEN}Monitoring status check complete.${NC}"
}

# --- Main Execution ---

# Check for command argument
if [ $# -eq 0 ]; then
    usage
fi

COMMAND="$1"
shift

# Parse options
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --app-namespace)
      APP_NAMESPACE="$2"
      shift
      shift
      ;;
    --mon-namespace)
      MONITORING_NAMESPACE="$2"
      shift
      shift
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      usage
      ;;
  esac
done

case "${COMMAND}" in
    setup)
        setup_monitoring
        ;;
    status)
        monitoring_status
        ;;
    *)
        echo -e "${RED}Invalid command: ${COMMAND}${NC}"
        usage
        ;;
esac

# Clean up old scripts
rm -f Flowlet/scripts/monitoring/monitor.sh
rm -f Flowlet/scripts/monitoring/setup-monitoring.sh
