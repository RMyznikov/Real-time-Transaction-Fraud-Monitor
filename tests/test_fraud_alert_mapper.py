from datetime import datetime, timezone

from app.mappers import fraud_alert_from_json, fraud_alert_to_json
from app.models.fraud_alert import FraudAlert


def test_fraud_alert_json_round_trip_preserves_domain_types() -> None:
    alert = FraudAlert(
        transaction_id="tx-1001",
        account_id="acc-50",
        rule="HIGH_AMOUNT",
        risk_score=80,
        created_at=datetime(2026, 7, 19, 10, tzinfo=timezone.utc),
    )

    restored = fraud_alert_from_json(fraud_alert_to_json(alert))

    assert restored == alert
