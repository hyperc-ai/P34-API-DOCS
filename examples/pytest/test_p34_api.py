"""Minimal pytest workflow for a P34 API integration.

Two layers, cheapest first:

1. offline payload checks — always run, no network;
2. live smoke — needs P34_API_KEY: health, capability listing, and ``mock:
   true`` /fit input parsing and validation. Generated rows are never sent as
   an actual fit.

Run:  P34_API_KEY=... pytest -v
"""
from __future__ import annotations

import os
import pytest
import requests

from wire import records

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


def test_fit_input_parsing(api_url, api_headers, tiny_market):
    from example_client import BUSINESS_DESCRIPTION

    menus, sales, market_type = tiny_market
    r = requests.post(
        f"{api_url}/fit",
        json={"menus": records(menus), "sales": records(sales), "market_type": market_type,
              # required context: the business + its unit economics (or save
              # one in the console's Business profile instead)
              "business_description": BUSINESS_DESCRIPTION, "mock": True},
        headers=api_headers, timeout=120,
    )
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["mock"] is True
    assert out["billing"]["tokens_charged"] == 0


def test_client_grounded_publishes_your_labels(api_url, api_headers, client_grounded_market):
    """grounding_mode=client_grounded: P34 derives nothing, it publishes what you sent.

    Runs as an input test: parsing and validation only, with no grounding,
    cluster work, or tokens charged.
    """
    menus, sales, market_type = client_grounded_market
    r = requests.post(
        f"{api_url}/fit",
        json={"menus": records(menus), "sales": records(sales), "market_type": market_type,
              # no business_description: nothing is compiled from one in this mode
              "grounding_mode": "client_grounded", "mock": True},
        headers=api_headers, timeout=120,
    )
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["mock"] is True
    assert out["billing"]["tokens_charged"] == 0


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
