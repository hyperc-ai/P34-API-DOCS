# P34 API — User Documentation

Complete user-facing documentation for HyperC's **P34** profit-prediction
service: how the API works, how to prepare your data, runnable examples, a
pytest-based integration workflow, and a demo comparing P34 against an
industry-standard boosting regressor baseline.

## Addresses

| Service | URL | What it is |
| --- | --- | --- |
| **API** | `https://api.hyperc.com/v1/` | The P34 model API (`POST /fit`, `GET /result/...`) |
| **Management console** | `https://api.hyperc.com/app/` | Account, API keys, plans/billing, session status & cancel |
| **Market simulator** | `https://api.hyperc.com/sim/` | Interactive browser simulator — play a synthetic market with P34 predictions |

`GET https://api.hyperc.com/v1/` is open (liveness + capability listing); all
other API calls require an API key from the management console, sent as
`Authorization: Bearer <key>`, on an account with an **active subscription**
(subscribe on the console's plans page — there is no free usage tier).

## Where to start

1. [docs/01-overview.md](docs/01-overview.md) — what P34 does and the mental
   model behind the API (menus, sales, the T=0 task).
2. [docs/02-endpoints.md](docs/02-endpoints.md) — endpoint reference, auth,
   result statuses, model versions.
3. [docs/03-data-format.md](docs/03-data-format.md) — the Menus / Sales /
   market_type input format, rule by rule.
4. [docs/04-errors-and-checks.md](docs/04-errors-and-checks.md) — common
   validation errors and quick self-checks.
5. [examples/](examples/) — runnable code:
   - [examples/client/](examples/client/) — a complete sample client
     (fit → poll → portfolio).
   - [examples/data/](examples/data/) — sample input as Excel, CSV, and JSON.
   - [examples/pytest/](examples/pytest/) — a minimal pytest workflow you can
     drop into CI to validate your integration.
   - [examples/baseline_comparison/](examples/baseline_comparison/) — a demo
     that pits P34 against a gradient-boosting profit regressor on a synthetic
     market with known ground truth.

## Quick taste

```bash
pip install pandas requests pyarrow
python examples/client/example_client.py --url https://api.hyperc.com/v1 --key $P34_API_KEY
```

```python
import requests
r = requests.post("https://api.hyperc.com/v1/fit",
                  headers={"Authorization": "Bearer <key>"},
                  json={"menus": [...], "sales": [...], "market_type": {...}})
session = r.json()["session_id"]
# poll until done:
requests.get(f"https://api.hyperc.com/v1/result/{session}",
             headers={"Authorization": "Bearer <key>"}).json()
```

The response fills in your T=0 menu: per key, the selected quantity
(`qty = 0` = do not trade) and the predicted profit.

---

© HyperC. This repository contains user-facing documentation and examples
only; sample data is synthetic.
