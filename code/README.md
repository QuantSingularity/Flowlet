# Flowlet Code

This directory contains the core application code for Flowlet, an embedded finance platform that exposes payments, wallets, card issuance, and compliance through a unified API. The code is organized into two primary areas: the Python Flask backend services and the machine learning services that power AI-enhanced financial intelligence.

## Directory Structure

```
code/
├── backend/           # Core Python microservices and API layer
└── ml_services/       # Machine learning models and AI services
```

## Backend

The `backend/` directory houses the main application server built with Python and Flask. It follows a modular architecture organized by domain, with clear separation between routes, models, services, and integrations.

### Key Components

| Directory           | Purpose                                                                                                    |
| ------------------- | ---------------------------------------------------------------------------------------------------------- |
| `app.py`            | Application entry point with the `create_app()` factory function                                           |
| `src/routes/`       | Flask Blueprints defining REST API endpoints for auth, payments, wallets, cards, compliance, and analytics |
| `src/models/`       | SQLAlchemy ORM models for users, accounts, transactions, cards, and ledger entries                         |
| `src/services/`     | Core business logic for payments, cards, wallets, and account management                                   |
| `src/compliance/`   | KYC/AML engines, regulatory frameworks, and compliance workflows                                           |
| `src/security/`     | Authentication, encryption, rate limiting, threat prevention, and password security                        |
| `src/integrations/` | Connectors for external systems including banking (Plaid, FDX), payments (Stripe), and currency exchange   |
| `src/analytics/`    | Dashboard services, reporting engines, real-time analytics, and metrics calculation                        |
| `src/nocode/`       | Rule engine, workflow builder, and configuration engine for dynamic business logic                         |
| `src/gateway/`      | API gateway logic for request routing and external API handling                                            |
| `src/config/`       | Centralized application settings and security policies                                                     |
| `src/database/`     | Database utilities and connection management                                                               |
| `src/utils/`        | Shared utility functions and helpers                                                                       |
| `migrations/`       | Database schema migration files                                                                            |
| `tests/`            | Comprehensive test suite covering unit, integration, functional, API, performance, and security testing    |

### Running the Backend

Development server:

```bash
cd backend
python run_server.py
```

With Docker:

```bash
cd backend
docker-compose up
```

Running tests:

```bash
cd backend
./run_tests.sh
```

For full backend documentation, see [backend/README.md](backend/README.md).

## ML Services

The `ml_services/` directory contains the machine learning stack that powers real-time fraud detection, risk assessment, and intelligent financial insights. Models are built with scikit-learn, XGBoost, and LightGBM, exposed as services that the backend can call during transaction processing.

### Key Components

| Directory                   | Purpose                                                                                              |
| --------------------------- | ---------------------------------------------------------------------------------------------------- |
| `config/`                   | Environment driven settings                                                                          |
| `core/`                     | Enums, exceptions, logging, signed and versioned model registry                                      |
| `data/`, `features/`        | Transaction validation, synthetic data, feature engineering, history stores                          |
| `fraud_detection/`          | Rule engine, anomaly and supervised models, stacked ensemble, detector, explainer, lifecycle service |
| `risk_assessment/`          | Credit, fraud, liquidity, operational and compliance risk scoring                                    |
| `transaction_intelligence/` | Categorization, recurring payment detection, spending analysis, forecasting                          |
| `support_chatbot/`          | Intent routing, retrieval, answers grounded in account data, PII redaction                           |
| `training/`, `evaluation/`  | Training pipeline and CLI, metrics, fairness report, walk-forward validation                         |
| `monitoring/`, `serving/`   | Drift and latency monitoring, Prometheus exporter, service container used by the backend             |
| `tests/`                    | Unit, integration and performance tests                                                              |

### Fraud Detection Ensemble

Scoring uses a stacked ensemble of Isolation Forest, One-Class SVM, an autoencoder, Random Forest, XGBoost, LightGBM and a neural network, combined with a deterministic rule engine. Quality metrics are computed on a holdout set at training time and exposed by `GET /api/v1/fraud/model/status`. Models trained on the built-in synthetic generator are labeled as such and are intended for development; train production models on real labeled data.

### Backend Integration

The backend calls `ml_services` through `backend/src/services/ml_gateway.py`. Payments are screened before funds move, fraud alerts are persisted, analysts resolve alerts and feed labels back to the model, and the `/api/v1/ai/*` endpoints expose risk assessment, categorization, spending analysis and the chatbot. See `ml_services/README.md` for configuration and the full endpoint list.

### Running ML Services

ML services are typically invoked by the backend or run as standalone inference workers. Models are trained with `python -m ml_services.training.cli`. `fraud_detection/service.py` provides the main entry point for real-time scoring requests.

## Technology Stack

| Layer            | Technology                                                                   |
| ---------------- | ---------------------------------------------------------------------------- |
| Backend language | Python 3.11+                                                                 |
| Web framework    | Flask + flask-restx                                                          |
| ORM              | SQLAlchemy                                                                   |
| Databases        | PostgreSQL, Redis                                                            |
| Messaging        | Kafka / RabbitMQ                                                             |
| ML frameworks    | scikit-learn, XGBoost, LightGBM                                              |
| Containerization | Docker                                                                       |
| Testing          | pytest, with unit, integration, functional, performance, and security suites |

## Testing

Both backend and ML services maintain extensive test coverage. The backend test suite is organized by test type under `backend/tests/`, while ML service tests live under `ml_services/tests/`. Tests validate correctness, integration contracts, performance benchmarks, and security controls.

## Related Documentation

- [Backend README](backend/README.md) - Detailed backend architecture, API routes, and configuration
- [Project README](../README.md) - High-level project overview, installation guide, and contribution guidelines
- [docs/](../docs/) - Additional documentation including API reference, architecture specs, and ML performance reports
