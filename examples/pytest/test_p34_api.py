"""Minimal pytest workflow for a P34 API integration.

Three layers, cheapest first:

1. offline payload checks — always run, no network;
2. live smoke — needs P34_API_KEY: health, capability listing, /fit intake
   validation (including the no-ground-truth rule), the client_grounded
   bring-your-own-labels path in free mock mode, and the instant /predict
   sanity check;
3. optional end-to-end — set P34_WAIT_MIN>0 to also wait for the real cluster
   fit and assert the returned portfolio's shape.

Run:  P34_API_KEY=... pytest -v
"""
from __future__ import annotations

import os
import time

import pandas as pd
import pytest
import requests

from wire import b64_to_df, records

# session id handed from the smoke fit to the optional end-to-end test
_FIT_SESSION: dict = {}

# --------------------------------------------------------------------------
# 1. offline — payload construction obeys the documented rules
# --------------------------------------------------------------------------

def test_payload_rules_offline(tiny_market):
    menus, sales, market_type = tiny_market

    task = menus[menus["T"] == 0]
    hist = menus[menus["T"] < 0]
    assert len(task) > 0, "a fit request must contain T=0 task rows"
    assert (task["menu"] == 0).all(), "task rows must use the reserved menu id 0"
    assert (hist["menu"] != 0).all(), "history must stay off menu 0"
    assert task["profit"].isna().all(), "task rows must not carry outcomes"
    flags = hist.groupby(["menu", "key"])["historically_chosen"].sum()
    assert flags.le(1).all(), "at most one chosen row per (menu, key)"
    assert flags.gt(0).any(), "a present column must flag something, else it reads as absent"
    assert (sales["T"] <= 0).all(), "sales must be historical"
    assert menus.groupby("key")["T"].apply(lambda t: t[t < 0].nunique() <= 1).all(), \
        "each historical key appears at one T"

    body = {"menus": records(menus), "sales": records(sales), "market_type": market_type}
    assert isinstance(body["menus"][0]["key"], str)


# --------------------------------------------------------------------------
# 2. live smoke — service is up and validates like the docs say
# --------------------------------------------------------------------------

def test_health(api_url, api_headers):
    r = requests.get(f"{api_url}/health", headers=api_headers, timeout=10)
    assert r.status_code == 200


def test_capabilities(api_url, api_headers):
    info = requests.get(f"{api_url}/", headers=api_headers, timeout=10).json()
    assert "default" in info["models"]
    assert any(e.startswith("POST /fit") for e in info["endpoints"])


def test_fit_rejects_task_ground_truth(api_url, api_headers, tiny_market):
    menus, sales, market_type = tiny_market
    poisoned = menus.copy()
    poisoned.loc[poisoned["T"] == 0, "profit"] = 1.0   # forbidden: outcomes on the task
    r = requests.post(
        f"{api_url}/fit",
        json={"menus": records(poisoned), "sales": records(sales), "market_type": market_type},
        headers=api_headers, timeout=120,
    )
    assert r.status_code == 422


def test_fit_and_instant_predict(api_url, api_headers, tiny_market):
    from example_client import BUSINESS_DESCRIPTION

    menus, sales, market_type = tiny_market
    r = requests.post(
        f"{api_url}/fit",
        json={"menus": records(menus), "sales": records(sales), "market_type": market_type,
              # required context: the business + its unit economics (or save
              # one in the console's Business profile instead)
              "business_description": BUSINESS_DESCRIPTION},
        headers=api_headers, timeout=120,
    )
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["status"] == "queued"
    assert out["labeled_rows"] > 0
    _FIT_SESSION["id"] = out["session_id"]              # reused by the e2e test

    now_menu = menus[menus["T"] == 0]
    r = requests.post(
        f"{api_url}/predict",
        json={"session_id": out["session_id"], "menus": records(now_menu),
              "market_type": market_type},
        headers=api_headers, timeout=120,
    )
    assert r.status_code == 200
    selection = b64_to_df(r.json()["selection"])
    assert set(selection.columns) >= {"key", "qty", "profit"}


def test_client_grounded_publishes_your_labels(api_url, api_headers, client_grounded_market):
    """grounding_mode=client_grounded: P34 derives nothing, it publishes what you sent.

    Runs in mock mode — the full intake and grounding path, no cluster work and
    no tokens charged — so this is safe to keep in CI on every commit.
    """
    menus, sales, market_type = client_grounded_market
    labeled_sent = int(menus[menus["T"] < 0]["profit"].notna().sum())

    r = requests.post(
        f"{api_url}/fit",
        json={"menus": records(menus), "sales": records(sales), "market_type": market_type,
              # no business_description: nothing is compiled from one in this mode
              "grounding_mode": "client_grounded", "mock": True},
        headers=api_headers, timeout=120,
    )
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["grounding_mode"] == "client_grounded"
    assert out["status"] == "queued", "client_grounded is synchronous — no grounding phase"
    # every label you sent survives to the published task, and none is invented
    assert out["parse_report"]["client_labeled_rows"] == labeled_sent
    assert out["parse_report"]["profit_values_ignored_on_non_chosen"] == 0
    # the split the model needs is YOURS to preserve in this mode
    assert out["unlabeled_rows"] > 0, "label every row and the cluster fit will refuse it"


def test_checks_off_never_relaxes_a_safety_refusal(api_url, api_headers, client_grounded_market):
    """checks=off skips PLAUSIBILITY checks only — never a structural or safety one."""
    menus, sales, market_type = client_grounded_market
    poisoned = menus.copy()
    poisoned.loc[poisoned["T"] == 0, "profit"] = 1.0   # outcomes on the prediction target

    r = requests.post(
        f"{api_url}/fit",
        json={"menus": records(poisoned), "sales": records(sales), "market_type": market_type,
              "grounding_mode": "client_grounded", "checks": "off", "mock": True},
        headers=api_headers, timeout=120,
    )
    assert r.status_code == 422, "checks=off must not lift the no-ground-truth rule"


# --------------------------------------------------------------------------
# 3. optional end-to-end — wait for the real cluster calculation
# --------------------------------------------------------------------------

def test_end_to_end_portfolio(api_url, api_headers):
    wait_min = float(os.environ.get("P34_WAIT_MIN", "0"))
    if wait_min <= 0:
        pytest.skip("set P34_WAIT_MIN (minutes) to wait for the cluster fit")
    session_id = _FIT_SESSION.get("id")
    # fall back: submit our own fit if the smoke test didn't run first
    if session_id is None:
        from example_client import BUSINESS_DESCRIPTION, MARKET_TYPE, build_sheets
        menus, sales = build_sheets(seed=11)  # defaults are cluster-viable
        out = requests.post(
            f"{api_url}/fit",
            json={"menus": records(menus), "sales": records(sales), "market_type": MARKET_TYPE,
                  "business_description": BUSINESS_DESCRIPTION},
            headers=api_headers, timeout=120,
        ).json()
        session_id = out["session_id"]

    deadline = time.time() + wait_min * 60
    while time.time() < deadline:
        res = requests.get(f"{api_url}/result/{session_id}", headers=api_headers, timeout=30).json()
        if res["status"] in ("done", "failed"):
            break
        time.sleep(20)
    assert res["status"] == "done", f"status={res['status']} error={res.get('error')}"

    portfolio = pd.DataFrame(res["menu"])
    if len(portfolio):
        assert set(portfolio.columns) >= {"key", "menu", "T", "qty", "profit"}
        assert (portfolio["menu"] == 0).all() and (portfolio["T"] == 0).all()
        assert res["n_selected"] == int((portfolio["qty"] > 0).sum())
    else:
        # an empty menu is a valid answer: the model takes no trades
        assert res["n_selected"] == 0
