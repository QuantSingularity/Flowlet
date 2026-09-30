#!/bin/bash

# Flowlet Infrastructure Cleanup Script

set -euo pipefail

echo "🧹 Starting Flowlet Infrastructure Cleanup"

SKIP_CONFIRM=${SKIP_CONFIRM:-"false"}
if [ "$SKIP_CONFIRM" != "true" ]; then
    echo ""
    echo "⚠️  WARNING: This will delete ALL Flowlet infrastructure from the cluster."
    echo "   Persistent volumes and data may be lost!"
    echo ""
    read -r -p "Type 'yes' to confirm: " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Aborted."
        exit 0
    fi
fi

delete_k8s_file() {
    local file=$1
    if [ -f "$file" ]; then
        echo "Deleting resources from $file..."
        kubectl delete -f "$file" --ignore-not-found=true --timeout=120s || true
        echo "✅ Processed $file"
    else
        echo "⚠️  $file not found - skipping"
    fi
}

delete_resource() {
    local resource_type=$1
    local name=$2
    local namespace=${3:-}
    if [ -n "$namespace" ]; then
        kubectl delete "$resource_type" "$name" -n "$namespace" --ignore-not-found=true --timeout=120s || true
    else
        kubectl delete "$resource_type" "$name" --ignore-not-found=true --timeout=120s || true
    fi
    echo "✅ Processed $resource_type/$name"
}

echo "⚙️  Uninstalling Istio..."
if command -v istioctl &> /dev/null; then
    istioctl uninstall --purge -y || true
    for ns in flowlet-core flowlet-data flowlet-messaging flowlet-monitoring; do
        kubectl label namespace "$ns" istio-injection- 2>/dev/null || true
    done
else
    echo "⚠️  istioctl not found - skipping Istio removal"
fi

echo "📈 Removing autoscaling..."
delete_k8s_file kubernetes/autoscaling/hpa.yaml

echo "🌍 Removing ingress..."
delete_k8s_file kubernetes/ingress/ingress.yaml

echo "🔒 Removing security and secrets..."
delete_k8s_file kubernetes/secrets/external-secret-store.yaml
delete_k8s_file kubernetes/security/security-policies.yaml
delete_k8s_file kubernetes/security/rbac.yaml
delete_k8s_file kubernetes/security/network-policies.yaml
delete_k8s_file kubernetes/security/resource-quotas.yaml
delete_k8s_file kubernetes/security/pod-disruption-budgets.yaml

echo "📊 Removing monitoring..."
delete_k8s_file kubernetes/monitoring/grafana.yaml
delete_k8s_file kubernetes/monitoring/prometheus.yaml
delete_k8s_file kubernetes/monitoring/alertmanager.yaml
delete_k8s_file kubernetes/monitoring/fluent-bit.yaml
delete_k8s_file kubernetes/monitoring/elasticsearch.yaml
delete_k8s_file kubernetes/monitoring/kibana.yaml
delete_k8s_file kubernetes/monitoring/jaeger.yaml

echo "🔧 Removing core services..."
for svc in ai-chatbot ai-fraud-detection notification-service developer-portal \
            api-gateway ledger-service kyc-aml-service card-service \
            payments-service wallet-service auth-service; do
    delete_k8s_file "kubernetes/services/${svc}.yaml"
done

echo "📨 Removing messaging..."
delete_k8s_file kubernetes/messaging/rabbitmq.yaml
delete_k8s_file kubernetes/messaging/kafka.yaml

echo "🗄️  Removing databases..."
for db in influxdb redis mongodb postgresql; do
    delete_k8s_file "kubernetes/databases/${db}.yaml"
done

echo "📁 Removing namespaces (this deletes all remaining resources within them)..."
for ns in flowlet-security flowlet-monitoring flowlet-messaging flowlet-data flowlet-core; do
    delete_resource namespace "$ns"
done

echo ""
echo "🎉 Flowlet Infrastructure cleanup complete!"
echo ""
echo "⚠️  Persistent volumes may still exist:"
echo "   kubectl get pv"
echo "   kubectl delete pv <name>  # only if data is no longer needed"
