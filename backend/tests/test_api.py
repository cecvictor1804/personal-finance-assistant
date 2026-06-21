import base64
import json

from app.adapters.fake_provider import plaid_txn
from app.ports.bank_provider import ProviderSyncResult


def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_create_and_list_manual_transaction(client):
    resp = client.post(
        "/transactions",
        json={
            "account_id": "cash",
            "amount_cents": -1599,
            "date": "2026-03-01",
            "merchant": "Shell",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["source"] == "manual"
    assert body["amount_cents"] == -1599
    assert body["id"].startswith("manual_")

    listed = client.get("/transactions").json()
    assert len(listed) == 1
    assert listed[0]["merchant"] == "Shell"


def test_manual_transaction_autocategorizes_from_rules(client):
    client.post("/rules", json={
        "match_type": "contains", "pattern": "shell", "category": "TRANSPORT", "priority": 50,
    })
    resp = client.post("/transactions", json={
        "account_id": "cash", "amount_cents": -1000, "date": "2026-03-02", "merchant": "Shell #5",
    })
    assert resp.json()["category"] == "TRANSPORT"
    assert resp.json()["category_source"] == "rule"


def test_recategorize_creates_remembered_rule(client):
    created = client.post("/transactions", json={
        "account_id": "cash", "amount_cents": -2000, "date": "2026-03-03", "merchant": "Trader Joes",
    }).json()
    txn_id = created["id"]

    resp = client.post(
        f"/transactions/{txn_id}/recategorize",
        json={"category": "GROCERIES", "remember": True},
    )
    assert resp.status_code == 200
    assert resp.json()["category"] == "GROCERIES"
    assert resp.json()["category_source"] == "manual"

    rules = client.get("/rules").json()
    assert any(r["pattern"] == "Trader Joes" and r["category"] == "GROCERIES" for r in rules)


def test_rules_crud(client):
    created = client.post("/rules", json={
        "match_type": "equals", "pattern": "Netflix", "category": "ENTERTAINMENT", "priority": 20,
    }).json()
    assert created["id"].startswith("rule_")

    assert len(client.get("/rules").json()) == 1

    assert client.delete(f"/rules/{created['id']}").status_code == 200
    assert client.get("/rules").json() == []


def test_sync_endpoint_runs_provider(client, provider, seeded_item):
    provider.add_page(ProviderSyncResult(
        added=[plaid_txn(transaction_id="t1", amount=9.99, merchant_name="Cafe",
                         pfc_primary="FOOD_AND_DRINK")],
        next_cursor="c1",
    ))
    resp = client.post("/items/sync")
    assert resp.status_code == 200
    assert resp.json()["added"] == 1

    listed = client.get("/transactions").json()
    assert listed[0]["amount_cents"] == -999


def test_internal_sync_requires_secret(client, seeded_item):
    # No header -> 403
    assert client.post("/internal/sync", json={"uid": "u1", "item_id": "item_1"}).status_code == 403
    # Correct header -> 200
    ok = client.post(
        "/internal/sync",
        json={"uid": "u1", "item_id": "item_1"},
        headers={"X-Internal-Secret": "s3cr3t"},
    )
    assert ok.status_code == 200


def test_pubsub_sync_decodes_envelope(client, provider, seeded_item):
    provider.add_page(ProviderSyncResult(
        added=[plaid_txn(transaction_id="t9", amount=5.0, merchant_name="Bus")],
        next_cursor="c1",
    ))
    data = base64.b64encode(json.dumps({"uid": "u1", "item_id": "item_1"}).encode()).decode()
    resp = client.post(
        "/internal/pubsub/sync?token=s3cr3t",
        json={"message": {"data": data}},
    )
    assert resp.status_code == 204
    assert client.get("/transactions").json()[0]["plaid_txn_id"] == "t9"


def test_pubsub_sync_rejects_bad_token(client, seeded_item):
    resp = client.post("/internal/pubsub/sync?token=wrong", json={"message": {"data": ""}})
    assert resp.status_code == 403


def test_list_accounts(client, repo):
    from app.domain.models import Account

    repo.upsert_account("u1", Account(id="a1", name="Checking", type="depository",
                                      balance_cents=120000))
    repo.upsert_account("u1", Account(id="a2", name="Visa", type="credit",
                                      balance_cents=45000, is_asset=False, is_liability=True))
    accounts = client.get("/accounts").json()
    assert {a["id"] for a in accounts} == {"a1", "a2"}
    visa = next(a for a in accounts if a["id"] == "a2")
    assert visa["is_liability"] is True


def test_budget_get_and_set_caps(client, repo):
    from datetime import date

    from app.domain.categories import Category
    from app.domain.models import Transaction

    repo.upsert_transaction(
        "u1",
        Transaction(id="t1", account_id="a1", amount_cents=-2500, date=date(2026, 6, 10),
                    merchant="Trader Joes", category=Category.GROCERIES),
    )
    got = client.get("/budgets/2026-06").json()
    assert got["spent_cents"]["GROCERIES"] == 2500

    put = client.put("/budgets/2026-06", json={"caps_cents": {"GROCERIES": 40000}}).json()
    assert put["caps_cents"]["GROCERIES"] == 40000
    assert put["spent_cents"]["GROCERIES"] == 2500


def test_budget_rejects_bad_month(client):
    assert client.get("/budgets/2026-6").status_code == 422


def test_alerts_via_sync_then_list_and_read(client, repo, provider):
    from app.domain.models import PlaidItem
    from app.ports.repository import ItemSecret

    # Non-initial item (has a cursor) so alerts are not suppressed.
    repo.save_item_secret(ItemSecret(item_id="item_1", uid="u1", access_token="x", cursor="prev"))
    repo.upsert_item("u1", PlaidItem(id="item_1"))
    provider.add_page(
        ProviderSyncResult(
            added=[plaid_txn(transaction_id="t1", amount=600.0, merchant_name="Big Store",
                             pfc_primary="GENERAL_MERCHANDISE", date="2026-06-10")],
            next_cursor="c2",
        )
    )
    assert client.post("/items/sync").json()["added"] == 1

    alerts = client.get("/alerts").json()
    assert len(alerts) >= 1
    aid = alerts[0]["id"]
    assert client.post(f"/alerts/{aid}/read").status_code == 200

    unread = client.get("/alerts?unread_only=true").json()
    assert all(not a["read"] for a in unread)


def test_recurring_and_forecast_endpoints(client, repo):
    from datetime import date

    from app.domain.models import Account, Flow, RecurringStream

    repo.upsert_account("u1", Account(id="a1", name="Checking", type="depository",
                                      balance_cents=100000))
    repo.upsert_recurring(
        "u1",
        RecurringStream(id="rent", merchant="Landlord", flow=Flow.OUTFLOW,
                        average_amount_cents=-150000, frequency="MONTHLY", last_date=date(2026, 5, 1)),
    )

    rec = client.get("/recurring").json()
    assert any(r["id"] == "rent" and r["flow"] == "outflow" for r in rec)

    fc = client.get("/forecast?horizon_days=60").json()
    assert fc["horizon_days"] == 60
    assert fc["current_balance_cents"] == 100000
    assert "upcoming" in fc


def test_settings_get_put_and_fcm_token(client):
    s = client.get("/settings").json()
    assert s["large_txn_threshold_cents"] == 50000

    updated = client.put(
        "/settings", json={**s, "large_txn_threshold_cents": 10000}
    ).json()
    assert updated["large_txn_threshold_cents"] == 10000

    tok = client.post("/settings/fcm-token", json={"token": "device-abc"}).json()
    assert "device-abc" in tok["fcm_tokens"]
