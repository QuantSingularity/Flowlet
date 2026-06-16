#!/usr/bin/env bash

# Flowlet Platform Setup Script
# This script automates the installation process for Flowlet platform, supporting
# both 'development' and 'production' environments.

# --- Security and Robustness ---
set -euo pipefail

# --- Configuration ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# --- Configuration ---
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/code/backend"
WEB_FRONTEND_DIR="$PROJECT_ROOT/web-frontend"

# Default values
ENV="development"
NAMESPACE="flowlet-dev"
SECRET_KEY=$(openssl rand -base64 32)
JWT_SECRET_KEY=$(openssl rand -base64 32)

# --- Helper Functions ---

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to display usage
usage() {
    echo -e "${BLUE}Usage: $0 [--env <development|production>] [--namespace <k8s-namespace>]${NC}"
    echo -e "  --env:       The environment to set up (default: development)"
    echo -e "  --namespace: The Kubernetes namespace for production setup (default: flowlet-dev)"
    exit 1
}

# Function to install Python dependencies
install_python_deps() {
    echo -e "${BLUE}Installing Python dependencies...${NC}"
    
    # Use the updated requirements file if it exists, otherwise fall back
    REQ_FILE="$BACKEND_DIR/requirements_updated.txt"
    if [ ! -f "$REQ_FILE" ]; then
        REQ_FILE="$BACKEND_DIR/requirements.txt"
    fi

    if [ -f "$REQ_FILE" ]; then
        # Use sudo for sandbox compatibility, suppress output
        sudo pip install -r "$REQ_FILE" > /dev/null
    fi

    if [ "$ENV" == "development" ]; then
        # Install development dependencies
        sudo pip install pytest pytest-cov pytest-html pytest-mock bandit flake8 black isort > /dev/null
    fi

    echo -e "${GREEN}✓ Python dependencies installed${NC}"
}

# Function to install Node.js dependencies
install_node_deps() {
    echo -e "${BLUE}Installing Node.js dependencies...${NC}"

    # Install web-frontend dependencies
    if [ -d "$WEB_FRONTEND_DIR" ]; then
        cd "$WEB_FRONTEND_DIR"
        if command_exists pnpm; then
            pnpm install
        elif command_exists npm; then
            npm install
        else
            echo -e "${RED}Neither pnpm nor npm found. Please install Node.js and npm.${NC}"
            exit 1
        fi
        cd "$PROJECT_ROOT"
        echo -e "${GREEN}✓ web-frontend dependencies installed${NC}"
    fi
}

# Function to setup database for development (SQLite)
setup_dev_database() {
    echo -e "${BLUE}Setting up development database (SQLite)...${NC}"

    cd "$BACKEND_DIR"
    mkdir -p data

    # Initialize database using Python script
    python3 -c "
from run_server import app
from src.models.database import db

with app.app_context():
    db.create_all()
    print('Database initialized successfully')
"
    cd "$PROJECT_ROOT"
    echo -e "${GREEN}✓ Development database setup completed${NC}"
}

# Function to setup environment files for development
setup_dev_env_files() {
    echo -e "${BLUE}Setting up development environment files...${NC}"

    # Backend environment file
    if [ ! -f "$BACKEND_DIR/.env" ]; then
        cat > "$BACKEND_DIR/.env" << EOF
# Flowlet Backend Environment Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=${SECRET_KEY}
DATABASE_URL=sqlite:///data/flowlet_dev.db
REDIS_URL=redis://localhost:6379/0

# API Keys (replace with actual values)
PLAID_CLIENT_ID=your_plaid_client_id
PLAID_SECRET=your_plaid_secret
PLAID_ENV=sandbox
STRIPE_SECRET_KEY=your_stripe_secret_key

# Security Settings
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
JWT_SECRET_KEY=${JWT_SECRET_KEY}

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/flowlet.log

# Performance Settings
SQLALCHEMY_POOL_SIZE=10
SQLALCHEMY_MAX_OVERFLOW=20
REDIS_POOL_SIZE=10
EOF
        echo -e "${GREEN}✓ Backend .env file created${NC}"
    else
        echo -e "${YELLOW}⚠ Backend .env file already exists. Skipping creation.${NC}"
    fi

    # web-frontend environment file
    if [ ! -f "$WEB_FRONTEND_DIR/.env" ]; then
        cat > "$WEB_FRONTEND_DIR/.env" << EOF
# Flowlet web-frontend Environment Configuration
VITE_API_BASE_URL=http://localhost:5000
VITE_APP_NAME=Flowlet
VITE_APP_VERSION=2.0.0
VITE_ENVIRONMENT=development

# Feature Flags
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_CHAT=true
VITE_ENABLE_FRAUD_DETECTION=true

# External Services
VITE_STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
EOF
        echo -e "${GREEN}✓ web-frontend .env file created${NC}"
    else
        echo -e "${YELLOW}⚠ web-frontend .env file already exists. Skipping creation.${NC}"
    fi
}

# Function to create development scripts
create_dev_scripts() {
    echo -e "${BLUE}Creating development scripts...${NC}"

    # Backend development script
    cat > "$BACKEND_DIR/dev.sh" << 'EOF'
#!/usr/bin/env bash
# Backend Development Server

set -euo pipefail

# Load environment variables
if [ -f .env ]; then
    # Use a more secure and robust way to load .env variables
    while IFS='=' read -r key value; do
        if [[ ! "$key" =~ ^# ]] && [[ -n "$key" ]]; then
            export "$key"="$value"
        fi
    done < .env
fi

# Create logs directory
mkdir -p logs

# Start the development server
# run_server.py is the canonical entry point (sets up sys.path and Flask app).
python3 run_server.py
EOF
    chmod +x "$BACKEND_DIR/dev.sh"

    # Combined development start script
    cat > "$PROJECT_ROOT/dev-start.sh" << 'EOF'
#!/usr/bin/env bash
# Start both backend and web-frontend development servers

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Starting Flowlet development environment...${NC}"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${BLUE}Shutting down development servers...${NC}"
    # Use pkill to kill processes started by the script
    pkill -P $$ || true
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Start backend server
echo -e "${GREEN}Starting backend server...${NC}"
(cd code/backend && ./dev.sh) &
BACKEND_PID=$!

# Start web-frontend server
echo -e "${GREEN}Starting web-frontend server...${NC}"
(cd web-frontend && (command -v pnpm >/dev/null 2>&1 && pnpm run dev --host || npm run dev -- --host)) &
FRONTEND_PID=$!

echo -e "${GREEN}=========================================="
echo -e "Development servers started!"
echo -e "Backend:  http://localhost:5000"
echo -e "web-frontend: http://localhost:5173"
echo -e "Press Ctrl+C to stop all servers"
echo -e "==========================================${NC}"

# Wait for background processes
wait
EOF
    chmod +x "$PROJECT_ROOT/dev-start.sh"

    echo -e "${GREEN}✓ Development scripts created${NC}"
}

# Function for production setup (Kubernetes/Helm)
setup_production() {
    echo -e "${BLUE}Starting Production Setup (Kubernetes/Helm)...${NC}"

    if ! command_exists kubectl || ! command_exists helm; then
        echo -e "${RED}✗ kubectl or helm not found. Please install them to proceed with production setup.${NC}"
        exit 1
    fi

    # Create namespace if it doesn't exist
    echo -e "${YELLOW}Ensuring Kubernetes namespace ${NAMESPACE} exists...${NC}"
    kubectl get namespace "${NAMESPACE}" > /dev/null 2>&1 || kubectl create namespace "${NAMESPACE}"

    # Set up configuration secrets
    echo -e "${YELLOW}Setting up configuration secrets...${NC}"
    # Use --dry-run=client -o yaml | kubectl apply -f - for idempotent secret creation
    kubectl create secret generic flowlet-secrets \
      --from-literal=db-password="$(openssl rand -base64 20)" \
      --from-literal=api-key="$(openssl rand -base64 32)" \
      --from-literal=secret-key="${SECRET_KEY}" \
      --from-literal=jwt-secret-key="${JWT_SECRET_KEY}" \
      --namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

    # Deploy core services
    echo -e "${YELLOW}Deploying core Flowlet services via Helm...${NC}"
    helm dependency update ./kubernetes/helm/flowlet
    helm upgrade --install flowlet ./kubernetes/helm/flowlet \
      --namespace "${NAMESPACE}" \
      --set environment="${ENV}" \
      --values ./kubernetes/helm/flowlet/values/"${ENV}".yaml

    # Configure networking (assuming ingress.yaml is correct)
    echo -e "${YELLOW}Configuring networking (Ingress)...${NC}"
    kubectl apply -f ./kubernetes/manifests/ingress.yaml -n "${NAMESPACE}"

    # Initialize database schemas
    echo -e "${YELLOW}Initializing database schemas (Job)...${NC}"
    # Use --force to ensure the job is recreated if it already exists
    kubectl apply -f ./kubernetes/jobs/init-system.yaml -n "${NAMESPACE}" --force
    kubectl wait --for=condition=complete job/flowlet-init -n "${NAMESPACE}" --timeout=300s

    echo -e "${GREEN}✓ Production setup complete!${NC}"
}

# --- Main Execution ---

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

echo -e "${BLUE}=========================================="
echo -e "Flowlet Platform Setup - Environment: ${ENV}"
echo -e "==========================================${NC}"

# Check system requirements (Python, Node.js)
echo -e "${BLUE}Checking system requirements...${NC}"
if ! command_exists python3; then
    echo -e "${RED}✗ Python 3 not found. Please install Python 3.11+${NC}"
    exit 1
fi
if ! command_exists node; then
    echo -e "${RED}✗ Node.js not found. Please install Node.js 20+${NC}"
    exit 1
fi
echo -e "${GREEN}✓ System requirements met.${NC}"

# Install dependencies (common for both envs)
install_python_deps
install_node_deps

if [ "$ENV" == "development" ]; then
    setup_dev_env_files
    setup_dev_database
    create_dev_scripts

    echo -e "${GREEN}=========================================="
    echo -e "Development environment setup complete!"
    echo -e "=========================================="
    echo -e "🚀 To start development:"
    echo -e "   ./dev-start.sh"
    echo -e "📚 Review the generated backend/.env for API keys."
    echo -e "==========================================${NC}"

elif [ "$ENV" == "production" ]; then
    setup_production

    echo -e "${GREEN}=========================================="
    echo -e "Production environment setup complete!"
    echo -e "=========================================="
    echo -e "🚀 Services deployed to Kubernetes namespace: ${NAMESPACE}"
    echo -e "🔑 Secrets are stored in 'flowlet-secrets' in that namespace."
    echo -e "==========================================${NC}"

else
    echo -e "${RED}Invalid environment specified: ${ENV}. Use 'development' or 'production'.${NC}"
    usage
fi

# Clean up the old setup-dev.sh if it exists
    # Clean up the old setup-dev.sh if it exists
    if [ -f "$PROJECT_ROOT/setup-dev.sh" ]; then
        rm "$PROJECT_ROOT/setup-dev.sh"
    fi
