BASE_FEATURE_COLUMNS = [
    "amount",
    "hour_of_day",
    "day_of_week",
    "is_weekend",
    "amount_zscore",
    "velocity_1h",
    "velocity_24h",
    "velocity_7d",
    "user_age_days",
    "avg_transaction_amount",
    "transaction_count_30d",
    "unique_merchants_30d",
    "new_device",
    "new_location",
    "unusual_time",
    "high_risk_merchant",
]

EXTENDED_FEATURE_COLUMNS = [
    "amount_log",
    "amount_to_avg_ratio",
    "is_round_amount",
    "minutes_since_last_tx",
    "amount_24h_total",
    "distinct_devices_7d",
    "high_risk_country",
    "cross_border",
    "is_new_user",
]

FEATURE_COLUMNS = BASE_FEATURE_COLUMNS + EXTENDED_FEATURE_COLUMNS

HIGH_RISK_CATEGORIES = frozenset(
    {
        "gambling",
        "adult",
        "adult_entertainment",
        "cryptocurrency",
        "crypto",
        "cash_advance",
        "money_transfer",
        "wire_transfer",
        "prepaid_cards",
        "quasi_cash",
    }
)

FEATURE_DESCRIPTIONS = {
    "amount": "Transaction amount of {value:.2f}",
    "amount_log": "Transaction amount is unusually large for typical spending",
    "amount_zscore": "Transaction amount is {abs_value:.1f} standard deviations from the user's normal",
    "amount_to_avg_ratio": "Transaction amount is {value:.1f} times the user's 30 day average",
    "velocity_1h": "User has made {value:.0f} transactions in the past hour",
    "velocity_24h": "User has made {value:.0f} transactions in the past 24 hours",
    "velocity_7d": "User has made {value:.0f} transactions in the past 7 days",
    "amount_24h_total": "Total value of the last 24 hours reaches {value:.2f}",
    "new_device": "Transaction originates from a device not seen before",
    "new_location": "Transaction originates from a country not seen before",
    "unusual_time": "Transaction occurs at an unusual time for this user",
    "high_risk_merchant": "Merchant category carries elevated fraud risk",
    "high_risk_country": "Transaction involves a high risk jurisdiction",
    "cross_border": "Transaction is cross border relative to the user's usual country",
    "is_round_amount": "Transaction amount is a round figure",
    "minutes_since_last_tx": "Only {value:.0f} minutes since the previous transaction",
    "distinct_devices_7d": "{value:.0f} distinct devices used in the past 7 days",
    "is_new_user": "User has no prior transaction history",
    "user_age_days": "Account activity history spans {value:.0f} days",
    "avg_transaction_amount": "User's 30 day average amount is {value:.2f}",
    "transaction_count_30d": "User made {value:.0f} transactions in the past 30 days",
    "unique_merchants_30d": "User transacted with {value:.0f} merchant categories in 30 days",
    "hour_of_day": "Transaction hour is {value:.0f}",
    "day_of_week": "Transaction day of week is {value:.0f}",
    "is_weekend": "Transaction occurs on a weekend",
}
