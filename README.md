# Flowlet - Embedded Finance Platform

![CI/CD Status](https://img.shields.io/github/actions/workflow/status/quantsingularity/Flowlet/cicd.yml?branch=main&label=CI/CD&logo=github)
![Test Coverage](https://img.shields.io/badge/coverage-91%25-green)
![License](https://img.shields.io/badge/license-MIT-blue)

![Flowlet HomePage](docs/images/homepage.bmp)

---

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Core Value Proposition](#core-value-proposition)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Technical Architecture](#technical-architecture)
- [Installation & Setup](#installation--setup)
- [Testing](#testing)
- [CI/CD Pipeline](#cicd-pipeline)
- [Documentation](#documentation)
- [Contributing Guidelines](#contributing-guidelines)
- [License](#license)

---

## Overview

Flowlet simplifies embedded finance by exposing payments, wallets, card issuance, and compliance through a single unified API. It is cloud-native and microservices-based, emphasizing scalability, security, and regulatory readiness while reducing operational overhead. Developer SDKs, documentation, and built-in AI for fraud detection and observability accelerate integration so teams can deliver auditable finance features without rebuilding core banking primitives.

## Key Features

Flowlet's strength lies in its comprehensive suite of embedded finance capabilities, meticulously implemented across its microservices architecture.

| Feature Domain                 | Core Functionality                                                                                    | Key Backend Modules                                                                          |
| :----------------------------- | :---------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------- |
| **Digital Wallet Management**  | Wallet creation, transaction processing, multi-currency support, real-time notifications.             | `backend/src/routes/wallet.py`, `backend/src/models/account.py`, `backend/src/currency/`     |
| **Payment Processing**         | Payment routing, external gateway integration (e.g., Stripe), bank transfers, transaction validation. | `backend/src/routes/payment.py`, `backend/src/integrations/payments/`                        |
| **Card Issuance & Management** | Card lifecycle events, transaction authorization, advanced card controls.                             | `backend/src/routes/card.py`, `backend/src/models/card.py`                                   |
| **KYC/AML Compliance**         | Identity verification, sanctions screening, regulatory compliance workflows, audit trails.            | `backend/src/routes/kyc_aml.py`, `backend/src/compliance/`                                   |
| **Ledger & Accounting**        | Meticulous recording of financial transactions, double-entry accounting, auditability.                | `backend/src/routes/ledger.py`, `backend/src/models/ledger.py`, `backend/src/utils/audit.py` |
| **AI-Enhanced Services**       | Real-time fraud detection, risk assessment, and intelligent support.                                  | `backend/src/ai/`, `backend/src/ml/fraud_detection/`                                         |
| **No-Code Workflow Engine**    | Configuration and execution of custom financial rules and workflows.                                  | `backend/src/nocode/`                                                                        |

---

## Project Structure

Flowlet utilizes a monorepo structure, separating the core backend services, frontend applications, and infrastructure configurations.

| Directory         | Description                                                                               |
| :---------------- | :---------------------------------------------------------------------------------------- |
| `code/`           | Contains the core Python microservices, shared libraries, and the main application logic. |
| `web-frontend/`   | The main web application built with React and TypeScript.                                 |
| `scripts/`        | Essential shell scripts for setup, building, and running the application.                 |
| `tests/`          | Comprehensive test suite covering unit, integration, performance, and security testing.   |
| `docs/`           | Documentation, including API reference and architecture specifications.                   |
| `infrastructure/` | Comprehensive DevOps and Infrastructure-as-Code (IaC) configurations.                     |
| `.github/`        | Configuration for GitHub Actions and repository templates.                                |

---

## Technology Stack

Flowlet is built on a modern, high-performance, and cloud-native stack.

| Category     | Component        | Technology                      | Detail                                                                              |
| :----------- | :--------------- | :------------------------------ | :---------------------------------------------------------------------------------- |
| **Backend**  | Languages        | Python                          | Primary language for all microservices.                                             |
|              | Frameworks       | Flask + flask-restx             | REST API framework with automatic OpenAPI/Swagger documentation.                    |
|              | Databases        | PostgreSQL, Redis               | PostgreSQL for transactional data; Redis for caching and session management.        |
|              | Messaging        | Kafka/RabbitMQ                  | Event-driven architecture for inter-service communication.                          |
| **Frontend** | Web              | React, TypeScript               | Main framework for the web dashboard.                                               |
|              | Styling          | Tailwind CSS                    | Utility-first CSS framework for rapid UI development.                               |
| **AI/ML**    | Frameworks       | scikit-learn, XGBoost, LightGBM | Ensemble fraud detection; see [ML Model Performance](docs/ML_MODEL_PERFORMANCE.md). |
| **DevOps**   | Containerization | Docker                          | For packaging services.                                                             |
|              | Orchestration    | Kubernetes, Helm                | For scalable deployment and management of microservices.                            |
|              | CI/CD            | GitHub Actions, Ansible         | Automated build, test, deployment pipelines, and configuration management.          |
|              | IaC              | Terraform                       | Infrastructure-as-Code for provisioning cloud resources.                            |

---

## Technical Architecture

Flowlet implements a **Microservices Architecture** with a strong focus on **Event-Driven Design** and **Security-by-Design**.

    Flowlet/
    ├── API Gateway (Authentication, Rate Limiting)
    ├── Frontend Application (Web)
    ├── Core Microservices
    │   ├── User Service (Auth, Profile)
    │   ├── Wallet Service (Accounts, Transactions)
    │   ├── Payment Service (Processing, Routing)
    │   ├── Card Service (Issuance, Controls)
    │   ├── Compliance Service (KYC/AML)
    │   └── Ledger Service (Accounting, Audit)
    ├── AI/ML Engine
    │   ├── Fraud Detection Service
    │   └── Risk Assessment Service
    ├── Infrastructure
    │   ├── Message Queue
    │   ├── Database Cluster
    │   └── Observability Stack (Prometheus, Grafana)
    └── Integrations Layer
        ├── Open Banking (Plaid, FDX)
        └── Payment Processors (Stripe)

---

## Installation & Setup

Flowlet supports two primary deployment environments: **Development** (local setup) and **Production** (Kubernetes/Helm).

### Prerequisites

| Requirement       | Detail                                                    |
| :---------------- | :-------------------------------------------------------- |
| **Python**        | 3.11+                                                     |
| **Node.js**       | 20+                                                       |
| **pnpm**          | Package manager for frontend dependencies.                |
| **Docker**        | Docker Engine and Docker Compose (for development setup). |
| **Kubectl, Helm** | Required for production setup.                            |

### Quick Start (Development)

The `setup.sh` script is the primary tool for environment configuration. Use the `--env development` flag for a local setup.

```bash
# Clone the repository
git clone https://github.com/quantsingularity/Flowlet.git
cd Flowlet

# Run the setup script for the development environment
./scripts/setup.sh --env development

# To start all services (backend and frontend)
./dev-start.sh
```

### Production Deployment (Kubernetes)

For production, Flowlet is designed to be deployed using Helm charts to a Kubernetes cluster.

```bash
# Run the setup script for the production environment
# This will check for kubectl/helm, create secrets, and deploy via Helm
./scripts/setup.sh --env production --namespace flowlet-prod

# To check the status of the deployment
kubectl get pods -n flowlet-prod
```

---

## AI/ML Performance

The fraud detection ensemble (XGBoost + LightGBM + Random Forest stacking) achieves:

| Metric                  | Value     |
| ----------------------- | --------- |
| AUC-ROC                 | **0.987** |
| Precision               | **97.3%** |
| Recall                  | **96.1%** |
| F1 Score                | **96.7%** |
| Inference latency (p50) | **8 ms**  |

See **[docs/ML_MODEL_PERFORMANCE.md](docs/ML_MODEL_PERFORMANCE.md)** for full tearsheets, confusion matrices, walk-forward validation, fairness analysis, and operational benchmarks.

---

## Testing

Flowlet maintains a high standard of code quality with **91% test coverage**. The testing framework is comprehensive and covers all layers of the application.

| Test Type             | Location             | Purpose                                                               |
| :-------------------- | :------------------- | :-------------------------------------------------------------------- |
| **Unit Tests**        | `tests/unit/`        | Isolated testing of individual functions and classes.                 |
| **Integration Tests** | `tests/integration/` | Validating inter-service communication and external API integrations. |
| **Functional Tests**  | `tests/functional/`  | Testing core business logic and user flows.                           |
| **Performance Tests** | `tests/performance/` | Benchmarking API response times and system throughput.                |
| **Security Tests**    | `tests/security/`    | Automated checks for common security vulnerabilities.                 |

---

## CI/CD Pipeline

AlphaMind uses GitHub Actions for continuous integration and deployment:

| Stage                | Control Area                    | Institutional-Grade Detail                                                              |
| :------------------- | :------------------------------ | :-------------------------------------------------------------------------------------- |
| **Formatting Check** | Change Triggers                 | Enforced on all `push` and `pull_request` events to `main` and `develop`                |
|                      | Manual Oversight                | On-demand execution via controlled `workflow_dispatch`                                  |
|                      | Source Integrity                | Full repository checkout with complete Git history for auditability                     |
|                      | Python Runtime Standardization  | Python 3.10 with deterministic dependency caching                                       |
|                      | Backend Code Hygiene            | `autoflake` to detect unused imports/variables using non-mutating diff-based validation |
|                      | Backend Style Compliance        | `black --check` to enforce institutional formatting standards                           |
|                      | Non-Intrusive Validation        | Temporary workspace comparison to prevent unauthorized source modification              |
|                      | Node.js Runtime Control         | Node.js 18 with locked dependency installation via `npm ci`                             |
|                      | Web Frontend Formatting Control | Prettier checks for web-facing assets                                                   |
|                      | Mobile Frontend Formatting      | Prettier enforcement for mobile application codebases                                   |
|                      | Documentation Governance        | Repository-wide Markdown formatting enforcement                                         |
|                      | Infrastructure Configuration    | Prettier validation for YAML/YML infrastructure definitions                             |
|                      | Compliance Gate                 | Any formatting deviation fails the pipeline and blocks merge                            |

## Documentation

For detailed documentation, please refer to the following resources:

| Document                    | Path                 | Description                                                 |
| :-------------------------- | :------------------- | :---------------------------------------------------------- |
| **README**                  | `README.md`          | High-level overview, project scope, and quickstart          |
| **API Reference**           | `API.md`             | Detailed documentation for all API endpoints                |
| **CLI Reference**           | `CLI.md`             | Command-line interface usage, commands, and examples        |
| **Installation Guide**      | `INSTALLATION.md`    | Step-by-step installation and environment setup             |
| **User Guide**              | `USAGE.md`           | Comprehensive guide for end-users, workflows, and examples  |
| **Contributing Guidelines** | `CONTRIBUTING.md`    | Contribution process, coding standards, and PR requirements |
| **Architecture Overview**   | `ARCHITECTURE.md`    | System architecture, components, and design rationale       |
| **Configuration Guide**     | `CONFIGURATION.md`   | Configuration options, environment variables, and tuning    |
| **Feature Matrix**          | `FEATURE_MATRIX.md`  | Feature capabilities, coverage, and roadmap alignment       |
| **Troubleshooting**         | `TROUBLESHOOTING.md` | Common issues, diagnostics, and remediation steps           |

## Contributing Guidelines

We welcome contributions to Flowlet. Please follow the organization's standard contribution process:

1.  **Open an Issue:** Discuss your proposed feature or bug fix before starting work.
2.  **Fork and Branch:** Fork the repository and create a new branch for your changes.
3.  **Code Standards:** Adhere to the existing code style and ensure all tests pass.
4.  **Documentation:** Update the relevant documentation for any new features or changes.
5.  **Pull Request:** Submit a pull request with a clear description of your changes and reference the related issue.

---

## License

Flowlet is released under the **MIT License**. For full details, see the [LICENSE](LICENSE) file in the repository root.
