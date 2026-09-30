#!/bin/bash

# Build all Flowlet Docker images

set -euo pipefail

echo "🐳 Building Flowlet Docker Images"

REGISTRY=${REGISTRY:-"flowlet"}
TAG=${TAG:-"latest"}
PUSH=${PUSH:-"false"}
PARALLEL=${PARALLEL:-"false"}

SERVICES=(
    "wallet-service"
    "payments-service"
    "card-service"
    "kyc-aml-service"
    "ledger-service"
    "api-gateway"
    "developer-portal"
    "auth-service"
    "notification-service"
    "ai-fraud-detection"
    "ai-chatbot"
)

build_service() {
    local service=$1
    local dockerfile_path="docker/$service/Dockerfile"
    local image_name="$REGISTRY/$service:$TAG"

    if [ -f "$dockerfile_path" ]; then
        echo "🔨 Building $service..."
        docker build \
            --tag "$image_name" \
            --file "$dockerfile_path" \
            --label "build.date=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
            --label "build.version=$TAG" \
            "docker/$service/"
        echo "✅ Built $image_name"

        if [ "$PUSH" = "true" ]; then
            echo "📤 Pushing $image_name..."
            docker push "$image_name"
            echo "✅ Pushed $image_name"
        fi
    else
        echo "⚠️  No Dockerfile at $dockerfile_path - skipping $service"
    fi
}

# Also build main backend and frontend
build_main_images() {
    echo "🔨 Building main backend image..."
    docker build \
        --tag "$REGISTRY/backend:$TAG" \
        --file "docker/Dockerfile.backend" \
        --label "build.date=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --label "build.version=$TAG" \
        "../../"
    echo "✅ Built $REGISTRY/backend:$TAG"

    echo "🔨 Building main frontend image..."
    docker build \
        --tag "$REGISTRY/frontend:$TAG" \
        --file "docker/Dockerfile.frontend" \
        --label "build.date=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --label "build.version=$TAG" \
        "../../"
    echo "✅ Built $REGISTRY/frontend:$TAG"
}

if [ "$PARALLEL" = "true" ]; then
    echo "⚡ Building in parallel..."
    pids=()
    for service in "${SERVICES[@]}"; do
        build_service "$service" &
        pids+=($!)
    done
    for pid in "${pids[@]}"; do
        wait "$pid" || { echo "❌ A parallel build failed"; exit 1; }
    done
else
    for service in "${SERVICES[@]}"; do
        build_service "$service"
    done
fi

build_main_images

echo ""
echo "🎉 All Docker images built successfully!"
echo ""
echo "📋 Built Images:"
for service in "${SERVICES[@]}"; do
    echo "  - $REGISTRY/$service:$TAG"
done
echo "  - $REGISTRY/backend:$TAG"
echo "  - $REGISTRY/frontend:$TAG"
echo ""
echo "💡 Usage:"
echo "  REGISTRY=myregistry.io TAG=v1.2.3 ./scripts/build-images.sh"
echo "  PUSH=true ./scripts/build-images.sh"
echo "  PARALLEL=true ./scripts/build-images.sh"
