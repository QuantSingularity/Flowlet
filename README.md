# Flowlet

![CI/CD Status](https://img.shields.io/github/actions/workflow/status/quantsingularity/Flowlet/cicd.yml?branch=main&label=CI%2FCD&logo=github)

## Embedded Finance Platform

Flowlet is an embedded finance platform: a single Flask application exposing wallets, payments, card issuance, KYC/AML compliance, a double-entry ledger, and a no-code workflow engine through one REST API, paired with a React web dashboard. A dedicated `ml_services` package provides real-time fraud detection (a stacked ML ensemble plus a rule engine), user risk assessment, transaction categorization and spending analysis, and a support chatbot. It is wired into the live API and the payment flow rather than sitting disconnected.

<div align="center">
  <img src="docs/images/homepage.bmp" alt="Flowlet HomePage" width="100%">
</div>

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Feature Status](#feature-status)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Installation and Setup](#installation-and-setup)
- [Running the Stack](#running-the-stack)
- [API Surface](#api-surface)
- [Testing](#testing)
- [CI/CD Pipeline](#cicd-pipeline)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## Overview

Flowlet demonstrates an embedded finance workflow across a real, runnable codebase. What's structured as a "microservices architecture" in earlier descriptions of this project is, in the current code, a single Flask application with around 18 blueprints registered under one `/api/v1` prefix, plus an in-process performance layer handling caching, circuit breakers, and rate limiting. The ML package is a genuine exception to the usual disconnected-research-library pattern: payments are screened by it before funds move, fraud alerts are stored in the database, analysts resolve alerts and feed labels back into the models, and the `/ai/*` and `/fraud/*` endpoints expose it to the dashboard.

## Project Structure

```
Flowlet/
├── code/
│   ├── backend/                          # Flask application (single process)
│   │   ├── src/routes/                   # ~18 blueprints: user, auth, wallet, payment,
│   │   │                                 # ledger, compliance, fraud, card, kyc, and more
│   │   ├── src/gateway/                  # In-process caching, circuit breakers, rate limiting
│   │   ├── src/integrations/             # Stripe, ACH, Plaid, FDX
│   │   ├── src/nocode/                   # Workflow builder, config engine, rule engine
│   │   ├── src/services/                 # Payment, ledger, compliance logic, ml_gateway (ML bridge)
│   │   ├── src/models/                   # SQLAlchemy models
│   │   └── tests/                        # unit, integration, functional, performance, security, api
│   └── ml_services/
│       ├── config/                       # Environment driven settings
│       ├── core/                         # Enums, exceptions, signed and versioned model registry
│       ├── data/                         # Transaction validation, synthetic data generators
│       ├── features/                     # Feature engineering, history stores (memory, Redis)
│       ├── fraud_detection/              # Rule engine, anomaly and supervised models, stacked ensemble,
│       │                                 # detector, explainer, lifecycle service
│       ├── risk_assessment/              # Multi-category user risk scoring
│       ├── transaction_intelligence/     # Categorizer, recurring payments, spending analysis
│       ├── support_chatbot/              # Intent routing, retrieval, grounded answers, PII redaction
│       ├── training/                     # Training pipeline and CLI
│       ├── evaluation/                   # Metrics, fairness report, walk-forward validation
│       ├── monitoring/                   # Drift, latency tracking, Prometheus exporter
│       ├── serving/                      # Service container consumed by the backend
│       └── tests/                        # unit, integration, performance
├── web-frontend/                         # React (Vite) dashboard
├── infrastructure/                       # Docker, Kubernetes manifests, Terraform, Ansible, monitoring
├── scripts/                              # Setup, start, stop, backup, deployment, monitoring scripts
├── docs/                                 # Documentation (this directory)
└── README.md
```

## Feature Status

### Application tier (wired and tested)

| Component                   | Details                                                                                                                                                                                                                                                                        |
| :-------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **API**                     | A single Flask application exposing `/api/v1` blueprints for users, auth, wallets, payments, ledger, analytics, compliance, KYC/AML, cards, monitoring, security, banking integrations, and an AI service.                                                                     |
| **In-process gateway**      | A `PerformanceOptimizedGateway` class handling Redis-backed caching, connection pooling, circuit breakers, and rate limiting inside the same process, rather than as a separate gateway service.                                                                               |
| **Payments**                | A real Stripe SDK integration, an ACH integration, and a payment-provider factory pattern for routing between them.                                                                                                                                                            |
| **Open banking**            | Plaid and FDX integration modules for linking external bank accounts.                                                                                                                                                                                                          |
| **Fraud detection**         | A stacked ensemble (Isolation Forest, One-Class SVM, autoencoder, Random Forest, XGBoost, LightGBM, neural network) combined with a rule engine. Payments are screened before funds move, flagged transactions create persisted alerts, and analyst decisions feed retraining. |
| **AI services**             | Risk assessment, transaction categorization, recurring payment detection, spending analysis with forecast, and a support chatbot grounded in the user's own account data, exposed under `/api/v1/ai`.                                                                          |
| **No-code workflow engine** | A workflow builder, configuration engine, and rule engine for defining custom financial rules without writing code.                                                                                                                                                            |
| **Ledger and compliance**   | Double-entry ledger recording, plus KYC/AML routes and a compliance service module.                                                                                                                                                                                            |
| **Data layer**              | SQLAlchemy over PostgreSQL, with Redis for caching, and Alembic-style migrations under `code/backend/migrations`.                                                                                                                                                              |
| **Web dashboard**           | React 19 and TypeScript app (Vite, Redux Toolkit, Tailwind CSS v4, axios).                                                                                                                                                                                                     |

## Technology Stack

| Area           | Technology                                                                                         |
| :------------- | :------------------------------------------------------------------------------------------------- |
| Backend API    | Python 3.11+, Flask, Flask-RESTX (OpenAPI/Swagger), Gunicorn                                       |
| Data layer     | SQLAlchemy 2, PostgreSQL, Redis                                                                    |
| Payments       | Stripe SDK, a custom ACH integration                                                               |
| Open banking   | Plaid and FDX integration modules                                                                  |
| ML services    | scikit-learn, XGBoost, LightGBM, pandas, SciPy                                                     |
| Web frontend   | React 19, TypeScript, Vite, Redux Toolkit, Tailwind CSS v4, axios                                  |
| Infrastructure | Docker, Docker Compose, Kubernetes manifests, Terraform, Ansible                                   |
| Monitoring     | Prometheus, Grafana, Alertmanager, Postgres and Redis exporters                                    |
| CI/CD          | GitHub Actions                                                                                     |
| Testing        | pytest across six suites (unit, integration, functional, performance, security, api); Vitest (web) |

Kubernetes manifests for Kafka and RabbitMQ exist under `infrastructure/kubernetes/messaging`, but neither is a dependency of the backend, and no producer or consumer code calls them; Celery is a declared dependency but isn't instantiated anywhere in the current codebase.

## Architecture

```
Client
  └── web-frontend (React)               ── HTTP/JSON ──┐
                                                        ▼
Backend (single Flask process, /api/v1)
  ├── Gateway layer   caching, circuit breakers, rate limiting (in-process)
  ├── Blueprints       user, auth, wallet, payment, ledger, compliance, kyc,
  │                    card, fraud, analytics, monitoring, security, banking
  ├── Integrations      Stripe, ACH, Plaid, FDX
  ├── No-code engine     workflow builder, config engine, rule engine
  └── Data layer          PostgreSQL (SQLAlchemy), Redis

ML services (code/ml_services, imported in-process through src/services/ml_gateway.py)
  fraud_detection            rule engine + stacked ensemble, model registry, drift, retraining
  risk_assessment            credit, fraud, liquidity, operational, compliance scoring
  transaction_intelligence   categorization, recurring payments, spending analysis
  support_chatbot            grounded answers, escalation, PII redaction

Payment flow
  transfer or deposit request -> fraud screening -> allow, review alert, or block (HTTP 403)
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detail.

## Installation and Setup

Prerequisites: Python 3.11+, Node.js 20+, and Docker (for the full local stack).

```bash
git clone https://github.com/quantsingularity/Flowlet.git
cd Flowlet

# Backend (requirements include the ml_services dependencies)
cd code/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Web frontend
cd ../../web-frontend
npm install
```

For an automated setup:

```bash
git clone https://github.com/quantsingularity/Flowlet.git
cd Flowlet
./scripts/setup.sh --env development
./scripts/start.sh
```

`scripts/setup.sh --env development` generates a `dev-start.sh` wrapper at the repo root; `scripts/start.sh` checks for it and runs it, and will tell you to re-run setup if it's missing.

Full, environment-specific instructions are in [docs/INSTALLATION.md](docs/INSTALLATION.md).

## Running the Stack

```bash
# Full local stack (from infrastructure/docker, Docker required)
docker compose up -d

# Or run components individually:

# Backend (from code/backend, venv active)
python app.py                      # serves http://0.0.0.0:5000

# Web dashboard (from web-frontend)
npm run dev
```

### ML configuration

The most relevant environment variables are listed below; the full table is in [code/ml_services/README.md](code/ml_services/README.md).

| Variable                  | Default                   | Purpose                                                                |
| :------------------------ | :------------------------ | :--------------------------------------------------------------------- |
| `ML_ENABLED`              | `true`                    | Master switch for ML services                                          |
| `ML_MODEL_DIR`            | system temp directory     | Model registry location (use a persistent volume in production)        |
| `ML_ARTIFACT_SIGNING_KEY` | `SECRET_KEY`              | HMAC key that verifies stored model artifacts (required in production) |
| `ML_BOOTSTRAP_ON_START`   | `true` outside production | Train a synthetic development model when none is stored                |
| `ML_BLOCK_IN_PAYMENTS`    | `true`                    | Reject payments scored critical                                        |
| `ML_FAIL_OPEN`            | `true`                    | Allow payments if fraud scoring itself errors                          |

Without a trained model the service runs in rules-only mode, reported by `/health` and the model status endpoint. Train a production model on real labeled data with `python -m ml_services.training.cli` (run from `code/`) or `POST /api/v1/fraud/model/train`.

Production deployment is documented as a Kubernetes and Helm rollout (`scripts/setup.sh --env production`), but the referenced Helm chart directory isn't included in this repository; the raw manifests under `infrastructure/kubernetes` are the deployable artifacts currently present.

See [docs/USAGE.md](docs/USAGE.md) and [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

## API Surface

Base URL `http://localhost:5000/api/v1`.

| Group                  | Highlights                                                                                                                                                                                                          |
| :--------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Auth / User            | Registration, login, profile management                                                                                                                                                                             |
| Wallet                 | Wallet creation, balances, transaction history                                                                                                                                                                      |
| Payment                | Payment initiation, routing, `/payment/{wallet_id}/send` P2P alias                                                                                                                                                  |
| Ledger                 | Double-entry transaction recording                                                                                                                                                                                  |
| Card                   | Card issuance, lifecycle, controls                                                                                                                                                                                  |
| KYC / KYC-AML          | Identity verification, sanctions screening                                                                                                                                                                          |
| Fraud                  | `detect`, `detect/batch`, `analyze`, `anomalies`, `velocity`, `model/train`, `model/retrain`, `model/status`, `model/drift`, `alerts`, `statistics`, `feedback`                                                     |
| AI                     | `ai/fraud-detection/analyze`, `ai/fraud-detection/alerts` (with `respond` and `resolve`), `ai/risk/assess`, `ai/risk/report`, `ai/transactions/categorize`, `ai/spending/analysis`, `ai/chatbot/query`, `ai/health` |
| Compliance / Analytics | Regulatory workflows and reporting                                                                                                                                                                                  |
| Banking integrations   | Plaid and FDX account linking                                                                                                                                                                                       |
| Monitoring / Security  | Health, metrics, security checks                                                                                                                                                                                    |

All `/fraud` and `/ai` endpoints require a bearer token. Regular users can only score and view their own data; model training, retraining, statistics, feedback, and alert resolution are admin only. A payment rejected by fraud screening returns HTTP 403 with code `FRAUD_BLOCKED`.

Full request and response shapes are in [docs/API.md](docs/API.md).

## Testing

```bash
# Backend, from code/backend, all suites
pytest

# Backend, a single suite
pytest tests/unit
pytest tests/integration
pytest tests/functional
pytest tests/performance
pytest tests/security
pytest tests/api

# ML services (from code/ml_services)
pip install -r requirements-dev.txt
pytest tests/unit tests/integration tests/performance

# Web (from web-frontend)
npm test
```

The backend has 17 test modules spread across six categories (unit, integration, functional, performance, security, api), including an integration suite that exercises the ML endpoints, alert persistence, and payment blocking end to end. The ML services have their own unit, integration, and performance suites (7 modules), and the web dashboard has 19 test files.

## CI/CD Pipeline

GitHub Actions (`.github/workflows/cicd.yml`) runs three jobs on push, pull request, and manual dispatch:

| Job                       | Depends on          | What it does                                                                       |
| :------------------------ | :------------------ | :--------------------------------------------------------------------------------- |
| Code Quality Checks       | -                   | Python formatter checks (autoflake, black) and a repository-wide Prettier check    |
| Backend Tests             | Code Quality Checks | Runs the pytest suite with coverage and uploads the coverage report as an artifact |
| Web-Frontend Test & Build | Code Quality Checks | Runs the frontend test suite and produces the production web build                 |

## Documentation

| Document                                                     | Contents                               |
| :----------------------------------------------------------- | :------------------------------------- |
| [docs/README.md](docs/README.md)                             | Documentation index                    |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)                 | System architecture                    |
| [docs/API.md](docs/API.md)                                   | REST API reference                     |
| [docs/INSTALLATION.md](docs/INSTALLATION.md)                 | Setup for all components               |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md)               | Environment variables and config       |
| [docs/USAGE.md](docs/USAGE.md)                               | Running and using the platform         |
| [docs/CLI.md](docs/CLI.md)                                   | Helper scripts reference               |
| [docs/FEATURE_MATRIX.md](docs/FEATURE_MATRIX.md)             | Feature status, implemented vs planned |
| [docs/ML_MODEL_PERFORMANCE.md](docs/ML_MODEL_PERFORMANCE.md) | Model evaluation methodology           |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)           | Common issues and fixes                |
| [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)                 | Contribution guide                     |
| [docs/examples/](docs/examples/)                             | Worked examples                        |

## Contributing

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
