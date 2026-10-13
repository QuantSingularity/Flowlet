#!/usr/bin/env bash

# Flowlet Backend - Comprehensive Test Suite
# This script runs all automated tests and generates reports.
# Designed for robust execution in CI/CD environments.

# --- Security and Robustness ---
# -e: Exit immediately if a command exits with a non-zero status.
# -u: Treat unset variables as an error.
# -o pipefail: Exit status of a pipeline is the status of the last command to exit with a non-zero status.
set -euo pipefail

# --- Configuration ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

TEST_RESULTS_DIR="test_results"
UNIT_TEST_FILES="tests/unit"
INTEGRATION_TEST_FILES="tests/integration"
PERFORMANCE_TEST_FILES="tests/performance"

# --- Helper Functions ---

# Function to check if a command exists
command_exists () {
  command -v "$1" >/dev/null 2>&1
}

# Function to run a test suite
run_test_suite() {
    local name="$1"
    local files="$2"
    local report_name="$3"
    local cov_append="$4"
    local exit_on_fail="$5"

    echo -e "${BLUE}Running ${name} tests...${NC}"

    # Check for pytest
    if ! command_exists pytest; then
        echo -e "${RED}Pytest not found. Skipping ${name} tests.${NC}"
        return 1
    fi

    # Build pytest command
    PYTEST_CMD="pytest ${files} \
        --cov=src \
        --cov-report=html:${TEST_RESULTS_DIR}/coverage/${report_name} \
        --cov-report=xml:${TEST_RESULTS_DIR}/coverage/${report_name}_coverage.xml \
        --html=${TEST_RESULTS_DIR}/reports/${report_name}_tests.html \
        --self-contained-html \
        -v \
        --tb=short"

    if [ "${cov_append}" = "true" ]; then
        PYTEST_CMD="${PYTEST_CMD} --cov-append"
    fi

    # Execute pytest
    if eval "${PYTEST_CMD}"; then
        echo -e "${GREEN}${name} tests passed${NC}"
        return 0
    else
        echo -e "${RED}${name} tests failed${NC}"
        if [ "${exit_on_fail}" = "true" ]; then
            return 1 # Return 1 to trigger the main script's exit logic
        fi
        return 1
    fi
}

# --- Setup ---

echo "=========================================="
echo "Flowlet Backend - Comprehensive Test Suite"
echo "=========================================="
echo -e "${BLUE}Setting up test environment...${NC}"

# Create and clean test results directory
rm -rf "${TEST_RESULTS_DIR}"
mkdir -p "${TEST_RESULTS_DIR}/coverage/unit"
mkdir -p "${TEST_RESULTS_DIR}/coverage/integration"
mkdir -p "${TEST_RESULTS_DIR}/reports"

# Install/Upgrade necessary tools (using sudo for sandbox compatibility)
echo -e "${YELLOW}Installing/Upgrading dependencies...${NC}"
sudo pip install --upgrade pip > /dev/null
sudo pip install -q pytest pytest-cov pytest-html pytest-xdist pytest-mock coverage bandit flake8 > /dev/null

# Set environment variables for testing
# NOTE: In a production environment, SECRET_KEY and other sensitive variables
# should be loaded securely from a secret manager (e.g., Vault, AWS Secrets Manager).
export FLASK_ENV=testing
export DATABASE_URL=sqlite:///:memory:
export SECRET_KEY="CI_TEST_SECRET_KEY_MUST_BE_SECURELY_LOADED"
export REDIS_URL=redis://localhost:6379/1

# --- Test Execution ---

# 1. Unit Tests (Critical)
run_test_suite "Unit" "${UNIT_TEST_FILES}" "unit" "false" "true"
UNIT_TEST_STATUS=$?

# 2. Integration Tests (Critical)
run_test_suite "Integration" "${INTEGRATION_TEST_FILES}" "integration" "true" "true"
INTEGRATION_TEST_STATUS=$?

# 3. Performance Tests (Non-critical, should not exit on failure)
run_test_suite "Performance" "${PERFORMANCE_TEST_FILES}" "performance" "false" "false"
PERFORMANCE_TEST_STATUS=$?

# --- Post-Test Analysis ---

echo -e "${BLUE}Generating comprehensive coverage report...${NC}"

# Generate combined coverage report
if command_exists coverage; then
    coverage combine
    coverage html -d "${TEST_RESULTS_DIR}/coverage/combined" > /dev/null
    coverage xml -o "${TEST_RESULTS_DIR}/coverage/combined_coverage.xml"
    coverage report --show-missing > "${TEST_RESULTS_DIR}/coverage/coverage_summary.txt"
    echo -e "${GREEN}Coverage reports generated.${NC}"
else
    echo -e "${YELLOW}Coverage tool not found. Skipping coverage reports.${NC}"
fi

# 4. Security Scan (Bandit)
echo -e "${BLUE}Running security tests (Bandit)...${NC}"
if command_exists bandit; then
    # The '|| true' ensures the script doesn't exit if bandit finds issues (which is expected)
    bandit -r src/ -f json -o "${TEST_RESULTS_DIR}/reports/security_report.json" || true
    echo -e "${GREEN}Security scan completed.${NC}"
else
    echo -e "${YELLOW}Bandit not installed. Skipping security scan.${NC}"
fi

# 5. Code Quality Checks (Flake8)
echo -e "${BLUE}Running code quality checks (Flake8)...${NC}"
if command_exists flake8; then
    # The '|| true' ensures the script doesn't exit if flake8 finds issues (which is expected)
    flake8 src/ --output-file="${TEST_RESULTS_DIR}/reports/flake8_report.txt" --tee || true
    echo -e "${GREEN}Code quality check completed.${NC}"
else
    echo -e "${YELLOW}Flake8 not installed. Skipping code quality check.${NC}"
fi

# --- Final Summary ---

echo -e "${GREEN}=========================================="
echo -e "Test execution completed!"
echo -e "=========================================="

# Display coverage summary
if [ -f "${TEST_RESULTS_DIR}/coverage/coverage_summary.txt" ]; then
    echo -e "${BLUE}Coverage Summary:${NC}"
    cat "${TEST_RESULTS_DIR}/coverage/coverage_summary.txt" | tail -n 5
fi

# Final Exit Status: Only exit 0 if all critical tests passed
if [ "${UNIT_TEST_STATUS}" -eq 0 ] && [ "${INTEGRATION_TEST_STATUS}" -eq 0 ]; then
    echo -e "${GREEN}All critical tests passed! Ready for deployment.${NC}"
    exit 0
else
    echo -e "${RED}Some critical tests failed. Please review and fix before deployment.${NC}"
    exit 1
fi
