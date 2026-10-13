# Flowlet ML Services

Machine learning services used by the Flowlet backend: real-time fraud detection, user risk assessment, transaction categorization and spending intelligence, and a support chatbot. The package is framework independent. The Flask backend consumes it through `backend/src/services/ml_gateway.py`.

## Package layout

```
ml_services/
  config/                  environment driven settings (MLSettings)
  core/                    enums, exceptions, logging, signed model registry
  data/                    transaction validation, synthetic data generators
  features/                feature schema, FeatureEngineer, history stores (memory, Redis)
  fraud_detection/
    models/                base, anomaly, supervised, stacked ensemble
    rules.py               deterministic rule engine
    detector.py            real-time detector (model plus rules)
    explainer.py           per-prediction explanations
    service.py             lifecycle: training, feedback, drift, retraining
  risk_assessment/         multi-category user risk scoring
  transaction_intelligence/ categorizer, recurring detection, spending analysis, forecast
  support_chatbot/         intent routing, retrieval, grounded answers, PII redaction
  training/                training pipeline and CLI
  evaluation/              metrics, fairness report, walk-forward validation
  monitoring/              drift (PSI, KS), latency tracking, Prometheus exporter
  serving/                 MLServiceContainer used by the backend
  tests/                   unit, integration, performance
```

## Fraud detection design

Scoring combines a model score and a rule score: `risk = max(model, rules)`. Without a trained model the service runs in `rules_only` mode and reports it in every response and in `/health`.

- Members: Isolation Forest, One-Class SVM, autoencoder (MLP reconstruction error), Random Forest, XGBoost, LightGBM, neural network. XGBoost and LightGBM are optional and skipped with a recorded reason when unavailable.
- Anomaly scores are calibrated with a training-time empirical CDF, so a single transaction scores the same as it would inside a batch.
- Class imbalance is handled per model (class weights, `scale_pos_weight`, minority oversampling).
- Ensemble strategies: `stacking` (default, logistic regression meta-learner on out-of-fold scores), `weighted`, `average`.
- Explanations use native tree contributions (XGBoost, LightGBM) with a standardized-deviation fallback, plus the rules that fired.
- Actions: `allow`, `monitor`, `challenge`, `block` derived from risk thresholds (0.3, 0.6, 0.8 by default).

### Model lifecycle

- `ModelRegistry` stores versioned artifacts with a SHA-256 checksum and an HMAC signature. Loading verifies both, which prevents loading tampered pickles. Set `ML_ARTIFACT_SIGNING_KEY` (falls back to `SECRET_KEY`; required in production).
- Training from labeled features, from a labeled transaction stream (`build_training_frame` reconstructs point-in-time history), or from synthetic data.
- Automatic retraining is champion/challenger: a challenger replaces the incumbent only if its holdout average precision is not worse than the incumbent's by more than `ML_MIN_PROMOTION_GAIN`.
- Retraining triggers: no model, model age, feedback volume, feature drift (PSI).
- Multiple server workers pick up a newly promoted model from the registry within 30 seconds.

### Synthetic bootstrap

`ML_BOOTSTRAP_ON_START` trains on synthetic data when no stored model exists. It defaults to on in development and off in production. Synthetic models are labeled `training_source: synthetic` in the status output. Train production models on real labeled data.

## Configuration

| Variable                                                            | Default                | Purpose                                           |
| ------------------------------------------------------------------- | ---------------------- | ------------------------------------------------- |
| `ML_ENABLED`                                                        | true                   | master switch                                     |
| `ML_MODEL_DIR`                                                      | system temp dir        | model registry location (use a persistent volume) |
| `ML_ARTIFACT_SIGNING_KEY`                                           | `SECRET_KEY`           | artifact HMAC key                                 |
| `ML_BOOTSTRAP_ON_START`                                             | true except production | train synthetic model when none stored            |
| `ML_BOOTSTRAP_SAMPLES`                                              | 6000                   | synthetic sample count                            |
| `ML_MEDIUM_THRESHOLD`, `ML_HIGH_THRESHOLD`, `ML_CRITICAL_THRESHOLD` | 0.3, 0.6, 0.8          | risk level cut-offs                               |
| `ML_AUTO_RETRAIN`                                                   | true                   | allow `maybe_auto_retrain`                        |
| `ML_RETRAIN_INTERVAL_DAYS`                                          | 30                     | model age trigger                                 |
| `ML_MIN_FEEDBACK_SAMPLES`                                           | 200                    | feedback trigger                                  |
| `ML_DRIFT_PSI_THRESHOLD`                                            | 0.25                   | drift trigger                                     |
| `ML_FAIL_OPEN`                                                      | true                   | allow payments when scoring errors                |
| `ML_ENFORCE_IN_PAYMENTS`                                            | true                   | screen payments in the backend                    |
| `ML_BLOCK_IN_PAYMENTS`                                              | true                   | reject payments scored critical                   |
| `ML_REDIS_URL`                                                      | unset                  | shared history store, falls back to memory        |
| `ML_HIGH_RISK_COUNTRIES`                                            | KP,IR,MM,SY,CU         | ISO codes treated as high risk                    |
| `ML_PERSIST_MODELS`                                                 | true                   | write models to the registry                      |

## Backend integration

Payments: `process_internal_transfer` and `process_external_payment` call `screen_payment` before moving funds. A `block` decision raises `FraudBlocked` (HTTP 403, code `FRAUD_BLOCKED`) and persists a `FraudAlert`. A `challenge` decision lets the payment proceed and persists an alert for review.

HTTP endpoints (all under `/api/v1`):

| Endpoint                                                                                                            | Access                       | Purpose                                         |
| ------------------------------------------------------------------------------------------------------------------- | ---------------------------- | ----------------------------------------------- |
| `POST /ai/fraud-detection/analyze`                                                                                  | user (admin for other users) | score a transaction with database history       |
| `GET /ai/fraud-detection/alerts`                                                                                    | user sees own, admin all     | paginated alerts                                |
| `POST /ai/fraud-detection/alerts/<id>/respond`                                                                      | alert owner                  | `recognized` or `not_me`                        |
| `POST /ai/fraud-detection/alerts/<id>/resolve`                                                                      | admin                        | resolve and feed the model                      |
| `POST /ai/risk/assess`, `GET /ai/risk/report`                                                                       | user                         | risk assessment and trend                       |
| `POST /ai/transactions/categorize`                                                                                  | user                         | categorize up to 500 transactions               |
| `POST /ai/transactions/categorize/correction`                                                                       | user                         | learn a user correction                         |
| `GET /ai/spending/analysis`                                                                                         | user                         | spending patterns, recurring payments, forecast |
| `POST /ai/chatbot/query`                                                                                            | user                         | chatbot grounded in account data                |
| `GET /ai/health`                                                                                                    | user                         | ML component health                             |
| `POST /fraud/detect`, `/fraud/analyze`, `/fraud/anomalies`, `/fraud/velocity`                                       | user                         | direct scoring helpers                          |
| `POST /fraud/detect/batch`, `/fraud/feedback`, `/fraud/model/train`, `/fraud/model/retrain`                         | admin                        | operations                                      |
| `GET /fraud/model/status`, `/fraud/model/drift`, `/fraud/model/retrain/check`, `/fraud/alerts`, `/fraud/statistics` | admin                        | monitoring                                      |

## Training CLI

```
python -m ml_services.training.cli train-synthetic --samples 8000
python -m ml_services.training.cli train-transactions transactions.json --label-key is_fraud
python -m ml_services.training.cli train-features features.csv --label-column is_fraud
python -m ml_services.training.cli list
python -m ml_services.training.cli promote <version>
```

## Python usage

```python
from ml_services.fraud_detection import FraudDetectionService

service = FraudDetectionService()
service.warm_up(block=True)
alert = service.detect({"user_id": "u1", "amount": 250.0, "currency": "USD", "merchant_category": "retail"})
print(alert.risk_level, alert.action, alert.explanation["summary"])
```

## Testing

```
pip install -r requirements-dev.txt
python -m pytest tests
```

## Known limitations

- Alerts, feedback and the feature cache are held in process memory. With several server workers, feedback applies only when the worker that scored the transaction receives it. Database alerts are authoritative.
- Chatbot answers come from a curated knowledge base and the user's own account data. An optional LLM fallback in the backend handles low confidence questions when `OPENAI_API_KEY` is set.
- The legacy `ai_models` package was replaced by the packages above.
