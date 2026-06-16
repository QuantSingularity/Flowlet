#!/usr/bin/env bash

# Flowlet Platform - Unified Setup Script
# This script handles the setup of the Flowlet environment, supporting both
# local development and Kubernetes prerequisites.

# --- Security and Robustness ---
set -euo pipefail

# --- Configuration ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# --- Helper Functions ---

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to display usage
usage() {
    echo -e "${BLUE}Usage: $0 [OPTION]${NC}"
    echo -e "  --dev-local    Setup local development environment (Docker, npm, .env.local)."
    echo -e "  --k8s-prereqs  Check and confirm Kubernetes prerequisites (kubectl, helm)."
    echo -e "  -h, --help     Display this help message."
    exit 1
}

# Function to check and install Kubernetes prerequisites
setup_k8s_prereqs() {
    echo -e "${BLUE}Checking Kubernetes prerequisites...${NC}"
    
    local missing_tools=0
    
    if ! command_exists kubectl; then
        echo -e "${RED}✗ kubectl not found. Please install kubectl to proceed.${NC}"
        missing_tools=1
    else
        echo -e "${GREEN}✓ kubectl found.${NC}"
    fi
    
    if ! command_exists helm; then
        echo -e "${RED}✗ Helm not found. Please install Helm to proceed.${NC}"
        missing_tools=1
    else
        echo -e "${GREEN}✓ Helm found.${NC}"
    fi
    
    if [ "$missing_tools" -eq 1 ]; then
        log_error "One or more Kubernetes prerequisites are missing."
    fi
    
    log_success "Kubernetes prerequisites check complete."
}

# Function to set up local development environment
setup_dev_local() {
    echo -e "${BLUE}Setting up local development environment...${NC}"
    
    # 1. Check critical tools
    if ! command_exists docker; then
        log_error "Docker is required but not installed. Aborting."
    fi
    if ! command_exists npm && ! command_exists pnpm; then
        log_error "Neither npm nor pnpm found. Node.js is required for frontend setup."
    fi
    
    # 2. Change to project root (assuming script is run from Flowlet/scripts/setup)
    # Use PWD to get the current directory and navigate to the project root
    local SCRIPT_DIR
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "${SCRIPT_DIR}/../.." || log_error "Failed to change to project root."
    
    # 3. Create local configuration
    if [ ! -f .env.local ]; then
      echo -e "${YELLOW}Creating local environment configuration...${NC}"
      cp .env.example .env.local
      echo -e "${YELLOW}Please update .env.local with your local configuration values.${NC}"
    else
      echo -e "${GREEN}✓ .env.local already exists. Skipping creation.${NC}"
    fi
    
    # 4. Install dependencies
    echo -e "${YELLOW}Installing dependencies...${NC}"
    if command_exists pnpm; then
        pnpm install
    elif command_exists npm; then
        npm install
    fi
    log_success "Dependencies installed."
    
    # 5. Start local services (Docker Compose)
    echo -e "${YELLOW}Starting local services via Docker Compose...${NC}"
    docker-compose -f infrastructure/docker/docker-compose.yml up -d
    log_success "Local services started."
    
    echo -e "${GREEN}=========================================="
    echo -e "Local Development Setup Complete!"
    echo -e "=========================================="
    echo -e "🚀 To start the development server, run: npm run dev"
    echo -e "🐳 To stop services, run: docker-compose down"
    echo -e "==========================================${NC}"
}

# --- Main Execution ---

# Default to showing usage if no arguments are provided
if [ $# -eq 0 ]; then
    usage
fi

while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --dev-local)
      setup_dev_local
      shift
      ;;
    --k8s-prereqs)
      setup_k8s_prereqs
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

# Clean up old scripts
rm -f Flowlet/scripts/setup/setup-dev.sh
rm -f Flowlet/scripts/setup/setup_k8s_prereqs.sh
