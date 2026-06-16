#!/usr/bin/env bash

# Flowlet Platform - Unified Deployment Script
# This script handles the deployment of the Flowlet application to a Kubernetes cluster.
# It supports deployment to staging or production environments.

# --- Security and Robustness ---
set -euo pipefail

# --- Configuration ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENV="staging"
NAMESPACE="flowlet-staging"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HELM_CHART_PATH="$PROJECT_ROOT/infrastructure/kubernetes/helm/flowlet-chart"
MANIFESTS_PATH="$PROJECT_ROOT/infrastructure/kubernetes/manifests"

# --- Helper Functions ---

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to display usage
usage() {
    echo -e "${BLUE}Usage: $0 [OPTION]${NC}"
    echo -e "  --env <staging|production>  The environment to deploy to (default: staging)."
    echo -e "  --namespace <name>          The Kubernetes namespace (default: flowlet-staging or flowlet-prod)."
    echo -e "  -h, --help                  Display this help message."
    exit 1
}

# Function to log error and exit
log_error() {
  echo -e "${RED}❌ ERROR: $1${NC}"
  exit 1
}

# --- Main Execution ---

# Check for required tools
if ! command_exists kubectl; then
    log_error "kubectl is required but not installed. Aborting."
fi
if ! command_exists helm; then
    echo -e "${YELLOW}Warning: Helm is not installed. The Helm step will be skipped; deployment will proceed via Kubernetes manifests only.${NC}"
fi

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --env)
      ENV="$2"
      shift
      shift
      ;;
    --namespace)
      NAMESPACE="$2"
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

# Set namespace based on environment if not explicitly set
if [ "$ENV" == "production" ] && [ "$NAMESPACE" == "flowlet-staging" ]; then
    NAMESPACE="flowlet-prod"
fi

echo -e "${BLUE}=========================================="
echo -e "Flowlet Deployment to ${ENV} (${NAMESPACE})"
echo -e "==========================================${NC}"

# 1. Ensure Namespace Exists
echo -e "${YELLOW}Ensuring Kubernetes namespace ${NAMESPACE} exists...${NC}"
kubectl get namespace "${NAMESPACE}" > /dev/null 2>&1 || kubectl create namespace "${NAMESPACE}"

# 2. Apply Kubernetes Manifests (e.g., Secrets, ConfigMaps, PVs)
echo -e "${YELLOW}Applying Kubernetes manifests from ${MANIFESTS_PATH}...${NC}"
kubectl apply -f "${MANIFESTS_PATH}" -n "${NAMESPACE}" || log_error "Failed to apply Kubernetes manifests."

# 3. Deploy Helm Chart (only if the chart is present in this repository)
if [ -d "${HELM_CHART_PATH}" ]; then
  echo -e "${YELLOW}Deploying Helm chart from ${HELM_CHART_PATH} for environment ${ENV}...${NC}"
  helm upgrade --install flowlet "${HELM_CHART_PATH}" \
    --namespace "${NAMESPACE}" \
    --set environment="${ENV}" \
    --values "${HELM_CHART_PATH}/values/${ENV}.yaml" \
    --atomic \
    --timeout 10m0s || log_error "Helm deployment failed."
else
  echo -e "${YELLOW}No Helm chart at ${HELM_CHART_PATH}; skipping Helm step (deployed via manifests above).${NC}"
fi

# 4. Verification
echo -e "${YELLOW}Verifying deployment status...${NC}"
kubectl rollout status deployment/flowlet-backend -n "${NAMESPACE}" --timeout=5m || log_error "Backend deployment failed to roll out."
kubectl rollout status deployment/flowlet-frontend -n "${NAMESPACE}" --timeout=5m || log_error "Frontend deployment failed to roll out."

echo -e "${GREEN}=========================================="
echo -e "Deployment to ${ENV} (${NAMESPACE}) complete!"
echo -e "==========================================${NC}"
