from flask import Blueprint

from .ai_service import ai_service_bp
from .analytics import analytics_bp
from .api_gateway import api_gateway_bp
from .auth import auth_bp
from .banking_integrations import banking_integrations_bp
from .card import card_bp
from .compliance import compliance_bp
from .fraud_detection import fraud_detection_bp
from .kyc import kyc_bp
from .kyc_aml import kyc_aml_bp
from .ledger import ledger_bp
from .monitoring import monitoring_bp
from .multicurrency import multicurrency_bp
from .payment import payment_bp
from .security import security_bp
from .user import user_bp
from .wallet import wallet_bp
from .wallet_compat import wallet_compat_bp

# The main API blueprint for version 1
api_bp = Blueprint("api", __name__, url_prefix="/api/v1")


# Register all sub-blueprints with the main API blueprint
api_bp.register_blueprint(user_bp)
api_bp.register_blueprint(auth_bp)
api_bp.register_blueprint(wallet_bp)
api_bp.register_blueprint(wallet_compat_bp)
api_bp.register_blueprint(payment_bp)
api_bp.register_blueprint(ledger_bp)
api_bp.register_blueprint(analytics_bp)
api_bp.register_blueprint(compliance_bp)
api_bp.register_blueprint(fraud_detection_bp)
api_bp.register_blueprint(multicurrency_bp)
api_bp.register_blueprint(kyc_aml_bp)
api_bp.register_blueprint(kyc_bp)
api_bp.register_blueprint(card_bp)
api_bp.register_blueprint(monitoring_bp)
api_bp.register_blueprint(security_bp)
api_bp.register_blueprint(ai_service_bp)
api_bp.register_blueprint(banking_integrations_bp)
api_bp.register_blueprint(api_gateway_bp)


# Alias blueprint: /payment/* -> delegates to payment_bp handlers
from flask import Blueprint as _BP

from .payment import send_p2p_payment as _send_p2p

payment_alias_bp = _BP("payment_alias", __name__, url_prefix="/payment")


@payment_alias_bp.route("/<wallet_id>/send", methods=["POST"])
def _payment_alias_send(wallet_id):
    return _send_p2p(wallet_id)


api_bp.register_blueprint(payment_alias_bp)
