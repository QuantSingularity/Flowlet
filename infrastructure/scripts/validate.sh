#!/bin/bash

# Flowlet Infrastructure Validation Script

set -euo pipefail

mkdir -p ../validation_logs
LOG_DIR="../validation_logs"
VALIDATION_LOG="${LOG_DIR}/validation_$(date +%Y%m%d_%H%M%S).log"

# Tee all output to both terminal and log file
exec > >(tee -a "$VALIDATION_LOG") 2>&1

echo "🔍 Validating Flowlet Infrastructure"
echo "📝 Logging to: $VALIDATION_LOG"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

print_status() {
    local status=$1
    local message=$2
    case $status in
        "SUCCESS") echo -e "${GREEN}✅ $message${NC}" ;;
        "WARNING") echo -e "${YELLOW}⚠️  $message${NC}"; WARNINGS=$((WARNINGS+1)) ;;
        "ERROR")   echo -e "${RED}❌ $message${NC}";   ERRORS=$((ERRORS+1)) ;;
        "INFO")    echo -e "ℹ️  $message" ;;
    esac
}

check_file() {
    local file=$1
    local description=$2
    if [ -f "$file" ]; then
        print_status "SUCCESS" "$description: $file"
        return 0
    else
        print_status "ERROR" "$description missing: $file"
        return 1
    fi
}

check_directory() {
    local dir=$1
    local description=$2
    if [ -d "$dir" ]; then
        print_status "SUCCESS" "$description: $dir"
        return 0
    else
        print_status "ERROR" "$description missing: $dir"
        return 1
    fi
}

validate_yaml() {
    local file=$1
    if command -v yamllint &> /dev/null; then
        if yamllint -c .yamllint.yaml "$file" &> /dev/null; then
            print_status "SUCCESS" "YAML valid: $file"
        else
            print_status "ERROR" "YAML invalid: $file"
            yamllint -c .yamllint.yaml "$file" || true
        fi
    else
        print_status "WARNING" "yamllint not installed - skipping YAML lint for $file"
    fi
}

check_k8s_manifest() {
    local file=$1
    if command -v kubectl &> /dev/null; then
        if kubectl apply --dry-run=client -f "$file" &> /dev/null; then
            print_status "SUCCESS" "K8s manifest valid: $file"
        else
            print_status "ERROR" "K8s manifest invalid: $file"
        fi
    else
        print_status "WARNING" "kubectl not available - skipping K8s dry-run for $file"
    fi
}

echo ""
echo "📁 Checking directory structure..."
check_directory "terraform"            "Terraform directory"
check_directory "kubernetes"           "Kubernetes directory"
check_directory "docker"               "Docker directory"
check_directory "scripts"              "Scripts directory"
check_directory "ansible"              "Ansible directory"
check_directory "kubernetes/namespaces"  "K8s namespaces"
check_directory "kubernetes/databases"   "K8s databases"
check_directory "kubernetes/messaging"   "K8s messaging"
check_directory "kubernetes/services"    "K8s services"
check_directory "kubernetes/ingress"     "K8s ingress"
check_directory "kubernetes/monitoring"  "K8s monitoring"
check_directory "kubernetes/security"    "K8s security"

echo ""
echo "📄 Checking essential files..."
check_file "README.md"                           "Main README"
check_file "terraform/main.tf"                   "Terraform main"
check_file "scripts/deploy.sh"                   "Deploy script"
check_file "scripts/build-images.sh"             "Build script"
check_file "scripts/cleanup.sh"                  "Cleanup script"
check_file "docker/docker-compose.yml"           "Docker Compose"
check_file "docker/.env.example"                 ".env example"
check_file "docker/Dockerfile.backend"           "Backend Dockerfile"
check_file "docker/Dockerfile.frontend"          "Frontend Dockerfile"
check_file "docker/monitoring/alertmanager.yml"  "Alertmanager config"
check_file "docker/monitoring/prometheus.yml"    "Prometheus config (docker)"
check_file "docker/monitoring/alert.rules.yml"   "Alert rules"

echo ""
echo "🗄️  Checking database configs..."
for db in postgresql mongodb redis influxdb; do
    check_file "kubernetes/databases/${db}.yaml" "${db} config"
done

echo ""
echo "📨 Checking messaging configs..."
check_file "kubernetes/messaging/kafka.yaml"    "Kafka config"
check_file "kubernetes/messaging/rabbitmq.yaml" "RabbitMQ config"

echo ""
echo "🔧 Checking service configs..."
SERVICES=(wallet-service payments-service card-service kyc-aml-service
          ledger-service api-gateway developer-portal auth-service
          notification-service ai-fraud-detection ai-chatbot)
for svc in "${SERVICES[@]}"; do
    check_file "kubernetes/services/${svc}.yaml" "$svc"
done

echo ""
echo "📊 Checking monitoring configs..."
check_file "kubernetes/monitoring/prometheus.yaml"   "Prometheus (K8s)"
check_file "kubernetes/monitoring/grafana.yaml"      "Grafana (K8s)"
check_file "kubernetes/monitoring/alertmanager.yaml" "Alertmanager (K8s)"

echo ""
echo "🔒 Checking security configs..."
check_file "kubernetes/security/security-policies.yaml"  "Security policies"
check_file "kubernetes/security/rbac.yaml"               "RBAC"
check_file "kubernetes/security/network-policies.yaml"   "Network policies"
check_file "kubernetes/ingress/ingress.yaml"             "Ingress"

echo ""
echo "✅ Validating YAML syntax..."
while IFS= read -r -d '' file; do
    validate_yaml "$file"
done < <(find kubernetes/ docker/ -name "*.yaml" -o -name "*.yml" -type f -print0)

echo ""
echo "🔍 Validating Kubernetes manifests (dry-run)..."
while IFS= read -r -d '' file; do
    check_k8s_manifest "$file"
done < <(find kubernetes/ -name "*.yaml" -type f -print0)

echo ""
echo "📋 Checking script permissions..."
for script in scripts/deploy.sh scripts/build-images.sh scripts/cleanup.sh scripts/validate.sh; do
    if [ -x "$script" ]; then
        print_status "SUCCESS" "Executable: $script"
    else
        print_status "WARNING" "Not executable: $script (run: chmod +x $script)"
    fi
done

echo ""
echo "🔐 Checking for secrets accidentally committed..."
if [ -f "kubernetes/secrets/secret.yaml" ]; then
    print_status "WARNING" "kubernetes/secrets/secret.yaml exists - ensure it is in .gitignore!"
fi
if [ -f "docker/.env" ]; then
    print_status "WARNING" "docker/.env exists - ensure it is in .gitignore!"
fi

echo ""
echo "============================================"
echo "📊 Validation Summary"
echo "============================================"
echo "  Errors:   $ERRORS"
echo "  Warnings: $WARNINGS"
echo ""
if [ "$ERRORS" -eq 0 ]; then
    print_status "SUCCESS" "All critical checks passed!"
else
    print_status "ERROR" "$ERRORS critical issue(s) found - fix before deploying."
fi
echo ""
print_status "INFO" "Full log: $VALIDATION_LOG"
echo ""
print_status "INFO" "To deploy: ./scripts/deploy.sh"
print_status "INFO" "To monitor: kubectl get pods --all-namespaces"
