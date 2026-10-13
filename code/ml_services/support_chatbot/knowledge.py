from typing import Dict, List

DEFAULT_KNOWLEDGE_BASE: List[Dict[str, str]] = [
    {
        "id": "wallets",
        "title": "Wallets and accounts",
        "content": "Your Flowlet wallet holds balances in one or more currencies. Open the Wallet page to see balances, add funds, and review recent activity. Each wallet has its own transaction history.",
        "keywords": "wallet account balance add funds deposit currency",
    },
    {
        "id": "send_money",
        "title": "Sending money",
        "content": "To send money, open Wallet and choose Send, enter the recipient and amount, and confirm. Transfers between Flowlet wallets are processed immediately when your balance and limits allow it. Review the recipient carefully before confirming because completed transfers can be difficult to reverse.",
        "keywords": "send transfer pay payment recipient p2p move money",
    },
    {
        "id": "receive_money",
        "title": "Receiving money",
        "content": "To receive money, share your wallet details from the Receive page. Incoming transfers appear in your transaction history once processed.",
        "keywords": "receive incoming request payment link",
    },
    {
        "id": "cards",
        "title": "Cards",
        "content": "You can issue a card from the Cards page. A card can be frozen and unfrozen at any time from the same page if you misplace it or want to pause spending. Freezing a card does not cancel it.",
        "keywords": "card freeze unfreeze block issue virtual physical lost stolen pin",
    },
    {
        "id": "lost_card",
        "title": "Lost or stolen card",
        "content": "If a card is lost or stolen, freeze it immediately from the Cards page and review recent transactions for anything you do not recognize. Then contact support so the card can be replaced.",
        "keywords": "lost stolen card missing replace freeze",
    },
    {
        "id": "fraud_alerts",
        "title": "Fraud alerts",
        "content": "Flowlet scores transactions for fraud risk in real time. Suspicious activity may be challenged, held for review, or blocked. You can review alerts on the Alerts page and mark activity you recognize or do not recognize.",
        "keywords": "fraud alert suspicious unauthorized scam hacked blocked declined",
    },
    {
        "id": "security",
        "title": "Account security",
        "content": "Protect your account with a strong unique password and enable multi factor authentication in Security settings. Flowlet will never ask for your password or one time codes by phone or email.",
        "keywords": "security password mfa two factor 2fa authentication protect login",
    },
    {
        "id": "kyc",
        "title": "Identity verification",
        "content": "Identity verification (KYC) is required to unlock higher limits and some features. Complete it from your profile by submitting the requested details and documents. Review times vary.",
        "keywords": "kyc verification identity verify documents passport id compliance",
    },
    {
        "id": "limits_fees",
        "title": "Fees and limits",
        "content": "Transaction fees and limits depend on your account type, currency, and verification level. You can see the fee before you confirm a transfer. Completing identity verification can raise your limits.",
        "keywords": "fee fees limit limits charge cost maximum daily",
    },
    {
        "id": "currencies",
        "title": "Multiple currencies",
        "content": "Flowlet supports several currencies. Currency conversion uses current exchange rates and the rate is shown before you confirm.",
        "keywords": "currency exchange convert foreign fx rate usd eur gbp",
    },
    {
        "id": "statements",
        "title": "Statements and history",
        "content": "Your full transaction history is available on the Transactions page where you can filter by date, type, and status.",
        "keywords": "statement history transactions export download report",
    },
    {
        "id": "budgeting",
        "title": "Budgeting and insights",
        "content": "The Analytics and Budgeting pages categorize your spending automatically and highlight trends, recurring payments, and categories where you spend the most.",
        "keywords": "budget budgeting analytics spending insights categories save savings goal",
    },
    {
        "id": "login_issues",
        "title": "Login problems",
        "content": "If you cannot sign in, use the forgot password option to reset your password. If your account is locked after several attempts, wait a few minutes and try again or contact support.",
        "keywords": "login sign in locked password reset forgot cannot access",
    },
    {
        "id": "disputes",
        "title": "Disputing a transaction",
        "content": "If you see a charge you do not recognize, freeze your card, then report it to support with the transaction details so it can be investigated.",
        "keywords": "dispute chargeback wrong charge unrecognized refund complaint",
    },
    {
        "id": "support",
        "title": "Contacting support",
        "content": "For issues that need a person, contact Flowlet support from the Help section. Include the transaction identifier when you report a problem.",
        "keywords": "support help contact agent human representative",
    },
]

INTENT_PATTERNS: Dict[str, str] = {
    "account_balance": r"\b(balance|how much (money|do i have)|funds available|available funds)\b",
    "transaction_history": r"\b(recent|last|latest|history|statement)\b.*\b(transactions?|payments?|activity|purchases?)\b|\b(my transactions?|explain.*transactions?)\b",
    "spending_analysis": r"\b(spend|spending|spent|expenses?|where.*money go|budget)\b",
    "savings_advice": r"\b(save|saving|savings|goal|reduce.*(expenses?|spending)|cut costs?)\b",
    "card_management": r"\b(card|freeze|unfreeze|pin|virtual card)\b",
    "payments_transfers": r"\b(send|transfer|pay|payment|wire|remit)\b",
    "fraud_security": r"\b(fraud|scam|hacked?|unauthori[sz]ed|stolen|suspicious|phishing|dispute|not me|did not make)\b",
    "kyc_compliance": r"\b(kyc|verify|verification|identity|documents?)\b",
    "fees_limits": r"\b(fees?|limits?|charges?|cost|maximum)\b",
    "technical_support": r"\b(error|bug|crash|not working|cannot|can't|login|log in|sign in|password|locked)\b",
    "greeting": r"^\s*(hi|hello|hey|good (morning|afternoon|evening)|thanks|thank you)\b",
}

ESCALATION_PATTERN = r"\b(unauthori[sz]ed|stolen|hacked?|scam|fraud|dispute|did not make|not me|lawyer|complaint|account locked)\b"
