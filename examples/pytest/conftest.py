"""Shared fixtures for the P34 API pytest workflow.

Configuration comes from the environment so the same tests run locally and in CI:

    P34_API_URL   base URL (default https://api.hyperc.com/v1)
    P34_API_KEY   your API key; API-hitting tests are SKIPPED when unset
    P34_WAIT_MIN  optional: minutes to wait for the full cluster fit in the
                  end-to-end test (default 0 = don't wait, just assert queued)
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "client"))


@pytest.fixture(scope="session")
def api_url() -> str:
    return os.environ.get("P34_API_URL", "https://api.hyperc.com/v1").rstrip("/")


@pytest.fixture(scope="session")
def api_headers() -> dict:
    key = os.environ.get("P34_API_KEY")
    if not key:
        pytest.skip("P34_API_KEY not set — skipping API tests")
    return {"Authorization": f"Bearer {key}"}


@pytest.fixture()
def tiny_market():
    from example_client import MARKET_TYPE, build_sheets

    # build_sheets defaults are the smallest CLUSTER-viable size: current
    # models need ~100 observed groups per qty option plus declined groups as
    # unlabeled context, so the smoke fit here can also complete end-to-end
    menus, sales = build_sheets(seed=11)
    return menus, sales, MARKET_TYPE
