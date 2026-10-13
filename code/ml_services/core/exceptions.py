class MLServiceError(Exception):
    pass


class ConfigurationError(MLServiceError):
    pass


class DependencyUnavailableError(MLServiceError):
    pass


class ServiceUnavailableError(MLServiceError):
    pass


class ModelNotFoundError(MLServiceError):
    pass


class ModelIntegrityError(MLServiceError):
    pass


class FraudDetectionError(MLServiceError):
    pass


class InvalidTransactionError(FraudDetectionError):
    pass


class ModelNotTrainedError(FraudDetectionError):
    pass


class FeatureExtractionError(FraudDetectionError):
    pass
