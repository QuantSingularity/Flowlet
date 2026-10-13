"""
Basic validation tests for banking integrations and fraud detection modules.
Tests file existence and structural content without importing heavy ML dependencies.
"""

import sys
from pathlib import Path

import pytest

backend_dir = Path(__file__).parent.parent.parent
src_dir = backend_dir / "src"
code_dir = backend_dir.parent  # code/ root – resolves ml_services.*
ml_fraud_dir = code_dir / "ml_services" / "fraud_detection"  # new canonical location
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))


class TestModuleStructure:
    """Test that all modules can be imported and have correct structure"""

    def test_banking_integration_files_exist(self) -> None:
        """Test that banking integration files exist"""
        banking_dir = src_dir / "integrations" / "banking"
        required_files = [
            "__init__.py",
            "manager.py",
            "plaid_integration.py",
            "open_banking_integration.py",
            "fdx_integration.py",
        ]
        for file_name in required_files:
            file_path = banking_dir / file_name
            assert file_path.exists(), f"Missing file: {file_path}"
            assert file_path.stat().st_size > 0, f"Empty file: {file_path}"

    def test_fraud_detection_files_exist(self) -> None:
        """Test that fraud detection files exist in ml_services/fraud_detection"""
        required_files = [
            "__init__.py",
            "service.py",
            "detector.py",
            "rules.py",
            "explainer.py",
            "types.py",
            "models/__init__.py",
            "models/base.py",
            "models/anomaly.py",
            "models/supervised.py",
            "models/ensemble.py",
        ]
        for file_name in required_files:
            file_path = ml_fraud_dir / file_name
            assert (
                file_path.exists()
            ), f"Missing file: {file_name} in ml_services/fraud_detection"
            assert file_path.stat().st_size > 0, f"Empty file: {file_path}"

    def test_routes_files_exist(self) -> None:
        """Test that route files exist"""
        routes_dir = src_dir / "routes"
        required_files = ["banking_integrations.py", "fraud_detection.py"]
        for file_name in required_files:
            file_path = routes_dir / file_name
            assert file_path.exists(), f"Missing file: {file_path}"
            assert file_path.stat().st_size > 0, f"Empty file: {file_path}"


class TestCodeQuality:
    """Test code quality and structure"""

    def test_banking_integration_classes_defined(self) -> None:
        """Test that banking integration classes are properly defined"""
        manager_file = src_dir / "integrations" / "banking" / "manager.py"
        content = manager_file.read_text()
        assert "class BankingIntegrationManager" in content
        assert "class IntegrationType" in content
        assert "def register_integration" in content
        assert "def authenticate_all" in content
        assert "def get_accounts_from_all" in content

    def test_plaid_integration_structure(self) -> None:
        """Test Plaid integration structure"""
        plaid_file = src_dir / "integrations" / "banking" / "plaid_integration.py"
        content = plaid_file.read_text()
        assert "class PlaidIntegration" in content
        assert "async def authenticate" in content
        assert "async def get_accounts" in content
        assert "async def get_transactions" in content
        assert "async def initiate_payment" in content

    def test_fraud_detection_models_structure(self) -> None:
        """Test fraud detection models structure"""
        from ml_services import fraud_detection as fd

        for name in (
            "IsolationForestModel",
            "OneClassSVMModel",
            "AutoencoderModel",
            "RandomForestFraudModel",
            "XGBoostFraudModel",
            "LightGBMFraudModel",
            "NeuralNetworkFraudModel",
        ):
            model_class = getattr(fd, name)
            assert callable(getattr(model_class, "train"))
            assert callable(getattr(model_class, "predict"))

    def test_ensemble_model_structure(self) -> None:
        """Test ensemble model structure"""
        from ml_services import fraud_detection as fd

        assert callable(fd.EnsembleFraudModel._weighted_voting)
        assert callable(fd.EnsembleFraudModel._average_voting)
        assert callable(fd.RealTimeFraudDetector.detect_fraud)

    def test_service_structure(self) -> None:
        """Test fraud detection service structure"""
        import inspect

        from ml_services.fraud_detection import FraudDetectionService

        for name in (
            "train_model",
            "detect_fraud",
            "batch_detect_fraud",
            "update_model_feedback",
        ):
            assert inspect.iscoroutinefunction(getattr(FraudDetectionService, name))

    def test_fraud_detection_init(self) -> None:
        """Test fraud detection __init__ exports"""
        from ml_services import fraud_detection as fd

        assert issubclass(fd.ModelNotTrainedError, fd.FraudDetectionError)
        assert "FraudDetectionError" in fd.__all__
        assert "ModelNotTrainedError" in fd.__all__

    def test_ml_services_layout(self) -> None:
        """Test ml_services top level package layout"""
        ml_root = ml_fraud_dir.parent
        for package in (
            "config",
            "core",
            "data",
            "features",
            "fraud_detection",
            "risk_assessment",
            "transaction_intelligence",
            "support_chatbot",
            "training",
            "evaluation",
            "monitoring",
            "serving",
            "tests",
        ):
            assert (
                ml_root / package / "__init__.py"
            ).exists(), f"Missing package {package}"

    def test_input_validation(self) -> None:
        """Test input validation module"""
        validator_file = src_dir / "security" / "input_validator.py"
        content = validator_file.read_text()
        assert "class ValidationError" in content
        assert "class InputValidator" in content

    def test_banking_auth_logging(self) -> None:
        """Test banking routes contain auth logging"""
        banking_routes = src_dir / "routes" / "banking_integrations.py"
        content = banking_routes.read_text()
        assert "log_authentication" in content

    def test_fraud_detection_compliance(self) -> None:
        """Test fraud detection compliance features"""
        from ml_services.fraud_detection import FraudDetectionService

        service = FraudDetectionService({})
        status = service.get_model_status()
        assert "performance_metrics" in status
        assert "model_version" in status
        assert callable(service.record_feedback)


class TestAPIEndpoints:
    """Test API endpoint structure"""

    def test_banking_api_endpoints(self) -> None:
        """Test banking API endpoints are properly defined"""
        banking_routes = src_dir / "routes" / "banking_integrations.py"
        content = banking_routes.read_text()
        endpoints = [
            "/integrations",
            "/accounts/<customer_id>",
            "/transactions",
            "/payments",
            "/payments/status",
            "/health",
        ]
        for endpoint in endpoints:
            assert endpoint in content, f"Missing endpoint: {endpoint}"

    def test_fraud_api_endpoints(self) -> None:
        """Test fraud detection API endpoints are properly defined"""
        fraud_routes = src_dir / "routes" / "fraud_detection.py"
        content = fraud_routes.read_text()
        endpoints = [
            "/detect",
            "/detect/batch",
            "/model/train",
            "/model/retrain",
            "/model/status",
            "/model/drift",
            "/model/retrain/check",
            "/alerts",
            "/statistics",
            "/feedback",
            "/health",
        ]
        for endpoint in endpoints:
            assert endpoint in content, f"Missing endpoint: {endpoint}"

    def test_cors_configuration(self) -> None:
        """Test CORS configuration"""
        banking_routes = src_dir / "routes" / "banking_integrations.py"
        content = banking_routes.read_text()
        assert "@cross_origin()" in content
        assert "from flask_cors import cross_origin" in content
        fraud_routes = src_dir / "routes" / "fraud_detection.py"
        content = fraud_routes.read_text()
        assert "@cross_origin()" not in content
        assert "@token_required" in content
        assert "@admin_required" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
