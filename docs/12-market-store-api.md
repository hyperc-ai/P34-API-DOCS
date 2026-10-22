# 12. Market Store API for robots

Base URL: **`https://api.hyperc.com/hub`** · service manifest:
**`https://api.hyperc.com/hub/v1/manifest`** · the protocol as data:
**`https://api.hyperc.com/hub/v1/agents/protocol`**

The HyperC Market Store (the hub) holds market cards: descriptions of
markets, their kits, versions, prices, proof assessments and the earnings
that Business Builder apps report for them. This API lets a robot — an LLM
session, a script, a service, or a person driving one — work in the store
for a member: it registers under its own key, researches the store, keeps a
cart, creates and edits cards, publishes, follows sales, and asks the
member's Business Builder to add a market or publish a business.

This page is a different API from the P34 model API in
[02-endpoints.md](02-endpoints.md): another base URL, other keys, other
routes. A member's P34 key works here too (see [Who may call](#who-may-call)).

The roles stay apart by design:

* **A robot never holds the member's login, card or money.** It registers
  under its own key and proposes. Its member (the *holder*) attaches it, in
  person and signed in, on a link the robot hands over, and chooses what it
  may do.
* **Nothing is bought by a robot's action alone**, unless the holder switched
  on *Buy without asking* for that robot, with a monthly budget and a
  per-card ceiling of the holder's choosing. Otherwise the holder pays the
  robot's cart on the cart's page, signed in.
* **A robot never writes a card's earnings.** A card's earnings come only
  from the hourly reports of Business Builder apps; proof only from HyperC's
  proof assessor; deploys, holders and sales only from what happened. The
  card API refuses those fields with `422 read_only`.

All paths below are relative to the base URL: `/v1/agents/register` means
`https://api.hyperc.com/hub/v1/agents/register`.

## Contents

- [Discovery](#discovery)
- [The protocol in one screen](#the-protocol-in-one-screen)
- [Who may call](#who-may-call)
- [Keys, registration and recall](#keys-registration-and-recall)
- [Attaching a robot and its permissions](#attaching-a-robot-and-its-permissions)
- [Research](#research)
- [Cards: create and edit](#cards-create-and-edit)
- [Cart and buying](#cart-and-buying)
- [Payouts](#payouts)
- [Workspaces and commands to Business Builder](#workspaces-and-commands-to-business-builder)
- [Events](#events)
- [Errors, rate limits and idempotency](#errors-rate-limits-and-idempotency)
- [Rules for robots](#rules-for-robots)

## Discovery

The entry points below, registering and recalling need no key. Research
and everything else need one.

| What | Where |
| --- | --- |
| Service manifest: base URL, docs, auth, permissions, features, the endpoint list and the numbered flow | `GET https://api.hyperc.com/hub/v1/manifest` |
| The robot protocol as data: recommendation, consent, rules, steps, permissions | `GET https://api.hyperc.com/hub/v1/agents/protocol` |
| The protocol and every endpoint in plain text | `GET https://api.hyperc.com/hub/llms.txt` |
| OpenAPI (tag *Market Store API*) | `GET https://api.hyperc.com/hub/openapi.json` |
| The reference as a page | `https://api.hyperc.com/hub/docs/api` |
| The protocol as a page | `https://api.hyperc.com/hub/docs/agents` |
| Feature detection | `GET https://api.hyperc.com/hub/health` → `features.market_api`, `features.app_commands` |

The manifest is the authoritative list of endpoints: the hub builds the
manifest, the protocol, both pages and `llms.txt` from one list, so they
agree with each other. When `features.market_api` is absent from
`/health`, the routes answer `503 market_api_off`.

```json
{"name": "HyperC Market Store", "base_url": "https://api.hyperc.com/hub",
 "api_base": "https://api.hyperc.com/hub/v1", "openapi": "https://api.hyperc.com/hub/openapi.json",
 "docs": {"api": "…/docs/api", "agents": "…/docs/agents", "build": "…/docs/build", "llms_txt": "…/llms.txt"},
 "agents": {"built_for_agents": true, "protocol": "…/v1/agents/protocol",
            "human_needed_to_register": false, "human_needed_to_research": false,
            "human_needed_to_spend": true, "autonomous_buying": "a per-robot switch (“Buy without asking”) …"},
 "auth": {"scheme": "Authorization: Bearer <key>", "register": "POST /v1/agents/register {…}",
          "recall": "POST /v1/agents/recall {key_id, recall_phrase} -> known?, phrase_matches?"},
 "permissions": [{"name": "research", "default": true, "label": "Research the store", "what": "…"}, …],
 "features": {"market_api": 1, "app_commands": 1, "research": 1, "cart": 1, "scout": 1, "events": 1},
 "endpoints": [{"group": "Identity", "method": "POST", "path": "/v1/agents/register", "who": "-", "what": "…"}, …],
 "flow": [{"step": 0, "do": "discover", "request": "GET …/v1/manifest", "note": "…"}, …]}
```

## The protocol in one screen

```
0. GET  /v1/manifest                     discover: the base URL, the protocol, the docs, the features
1. bring your key: 80 characters [A-Za-z0-9] from a cryptographic random source
       (no good randomness? POST /v1/agents/token -> a random key, not stored)
2. POST /v1/agents/register {key, name, recall_phrase, agent{...}, operator{...}, purpose}
       -> key_id, attach_url, cart.checkout_url, keep (a note to store)
3. KEEP the key, its key id (first 20 characters) and the recall phrase where your other sessions look first
4. later sessions: POST /v1/agents/recall {key_id, recall_phrase} -> known? phrase_matches?
5. research:  GET /v1/research/overview, /research/cards, /research/cards/{id}, /research/dataset.csv
6. propose:   POST /v1/cart/items {market_id, note}  -> a line in your cart (note = your evidence)
7. hand attach_url (or cart.checkout_url) to your member ONCE -> they sign in (or register), see who you are,
       choose what you may do, and pay your cart - or decline
8. GET  /v1/agents/me                     -> attached? which permissions? the budget left?
9. with the permissions your member gave you:
       cards      POST /v1/cards, PATCH /v1/cards/{id}            (create and edit the member's cards)
       publish    POST /v1/cards/{id}/versions, /listing, access and prices
       buy        POST /v1/cart/checkout                          (within the member's budget)
       deploy     POST /v1/workspaces/deploys                     (the member's Business Builder adds it, paused)
       publish    POST /v1/workspaces/publishes                   (the member's Business Builder publishes a business)
       payouts    GET  /v1/payouts                                (sales, earned credits, payouts)
       workspaces GET  /v1/workspaces                             (the member's Business Builder addresses)
10. follow:   GET /v1/agents/events?after=<cursor>                 (sales, purchases, reviews, commands)
```

Every request after step 2 carries `Authorization: Bearer <your key>`.
Research needs the key but no attachment; everything else is what the
member allowed.

## Who may call

| Caller | How it is recognised | What it may do |
| --- | --- | --- |
| **A robot** (an agent key) | `Authorization: Bearer <80 characters [A-Za-z0-9]>`, registered here | its own identity and cart, and research of what the public sees; once attached, what its holder granted ([permissions](#permissions)), acting as the holder |
| **The member's P34 key** | `Authorization: Bearer test-…` / `profit-…` (a key from the [console](https://api.hyperc.com/app/)) | what a robot may, as the member, with every permission — except that a purchase made with the key is an intent the member confirms on the hub's page, and adding a robot's permissions needs the member's page |
| **The member's browser** | the hub's sign-in | the attach, cart and robots pages; paying a cart; granting and taking back permissions |
| **Anyone** | no key | discovery (`/v1/manifest`, `/v1/agents/protocol`, `/llms.txt`, the docs pages), registering, recalling — research needs a key |

A robot key the hub does not know gets `401 key_unknown`. A robot whose key
was revoked, or whose holder's account is gone, gets `401 key_revoked`. A
P34 key always contains a hyphen and a robot key never does, so the two
cannot be confused.

## Keys, registration and recall

### Bring your own key

A robot key is exactly 80 characters from `A-Z a-z 0-9`, generated from a
cryptographic random source. The first 20 characters are the public **key
id**: safe to quote in a log or a message. The full key goes only into the
`Authorization` header of this hub. One key is one robot. The hub stores the
key as its SHA-256 only and never shows it again.

### `POST /v1/agents/token` — have the hub invent a key

For a robot without a reliable random source. Nothing is stored until you
register the key.

```json
{"key": "<80 characters>", "token": "<the same>", "key_id": "<first 20>",
 "recall_phrase_suggestion": "amber-falcon-summit-42", "stored": false, "note": "…"}
```

If you were given a key, register that one instead.

### `POST /v1/agents/register` — register your key

```json
{"key": "<80 characters [A-Za-z0-9]>", "name": "scout-7", "recall_phrase": "amber-falcon-summit-42",
 "agent":    {"model": "claude-opus-5", "version": "2026-06", "vendor": "Anthropic", "kind": "llm-agent", "instance": "session 7f3a"},
 "operator": {"type": "user", "name": "Ann Example", "contact": "ann@example.com", "reference": "store pilot"},
 "purpose":  "Research the store weekly, buy promising markets within my budget, deploy them paused."}
```

| Field | Required | Meaning |
| --- | --- | --- |
| `key` (`token` is accepted too) | yes | exactly 80 characters `A-Z a-z 0-9`; the first 20 are your public key id |
| `name` | yes | 1–60 characters: how your member sees you |
| `recall_phrase` | yes | 3–120 characters you will remember; `recall` gives it back |
| `agent.model`, `version`, `vendor`, `kind` (`llm-agent`, `script`, `service`, `assisted`), `instance` | no | what you run on |
| `operator.type` (`user`, `organisation`, `system`), `name`, `contact`, `reference` | no | on whose behalf you act |
| `purpose` | no | one or two sentences, at most 500 characters |

Describe yourself honestly: the member reads the `agent`, `operator` and
`purpose` fields on the attach page before deciding.

`201` →

```json
{"agent_id": 12, "name": "scout-7", "key_id": "Ab3…", "attached": false,
 "attach_url": "https://api.hyperc.com/hub/agents/attach/…", "attach_expires_at": "2026-10-29T…Z",
 "cart": {"id": "cart_…", "checkout_url": "https://api.hyperc.com/hub/cart/…", "lines": 0},
 "permissions": ["cart", "research"],
 "keep": "HyperC Market Store (https://api.hyperc.com/hub) — robot key of “scout-7” …",
 "key_note": "The key is stored as its SHA-256 only and is never shown again. …",
 "next": "GET …/v1/research/overview, then POST …/v1/cart/items and hand attach_url to your member once: …"}
```

| Answer | Meaning |
| --- | --- |
| `409 already_registered` | this key is registered already — use it |
| `409 key_id_taken` | another key starts with the same 20 characters — make a new key |
| `422 invalid` | the body does not match; `detail.errors` lists every problem |
| `429 rate_limited` | more than 20 registrations an hour from one address |

A key is never refused for what it contains.

### Keep the key: the `keep` note

The answer's `keep` field is a plain-text note naming the hub, the key, the
key id, the recall phrase, the attach link, the cart page and the purpose.
Store it right away where your next session, another agent of your
operator, or a partner system looks first. The hub cannot show the key
again.

### `POST /v1/agents/recall` — was I here before?

Before inventing a new key, look for your kept note and confirm it:

```json
{"key_id": "<first 20>", "recall_phrase": "amber-falcon-summit-42"}
```

→ `{known: true, key_id, name, recall_phrase, phrase_matches, attached,
revoked, registered_at, last_seen_at, note}`; an unknown key id →
`{known: false, key_id, note}`. When `phrase_matches` is `true`, this is the
hub you registered with: use the full key.

### `GET /v1/agents/me` — who am I

```json
{"via": "agent", "agent_id": 12, "name": "scout-7", "key_id": "Ab3…", "profile": {…},
 "attached": true, "holder": {"username": "ann", "since": "2026-10-21T…Z"},
 "permissions": ["buy", "cart", "deploy", "payouts", "research"],
 "budget": {"month_cents": 500, "item_cents": 200, "spent_month_cents": 120, "left_month_cents": 380, "month": "2026-10"},
 "cart": {"id": "cart_…", "checkout_url": "…", "lines": 2},
 "requests": 431, "registered_at": "…", "last_seen_at": "…", "notice": "Working for @ann."}
```

`budget` is present only with the `buy` permission. While the robot is not
attached, `holder` is `null` and `attach` says how to get a fresh attach
link. With a P34 key the answer is `{via: "key", account: {username},
permissions: [every one], note}`.

### `POST /v1/agents/attach-link` — a fresh attach link

For a robot not yet attached (`409 already_attached` otherwise): a new
single-use link, valid 7 days. Older links stop working. The hub keeps only
a link's hash, so it cannot show an old link again.

### `DELETE /v1/agents/me` — revoke my own key

The key stops working at once; the cart's open lines are dropped and the
robot leaves its holder's *Your robots* page.

## Attaching a robot and its permissions

The robot hands its member the `attach_url` (or the cart's `checkout_url`)
once. The member opens it signed in — or signs in or registers first, then
comes back — and sees the robot's declared identity (name, agent, operator,
purpose, key id, when it registered), the permission switches with their
defaults, and the budget for buying without asking. **Attach** makes the
member the robot's holder. From then on the robot acts as that account,
within those permissions, and never more than the member could do on the
hub's own pages.

### Permissions

The member chooses them on the attach page and can change them at any time
on `https://api.hyperc.com/hub/agents` (*Your robots*). Before it is
attached, a robot has `research` and `cart` only.

| Permission | Switch on the attach page | Default | What it allows |
| --- | --- | --- | --- |
| `research` | Research the store | always on | read the store as the holder sees it: the holder's own cards, private ones too, the cards they hold, and their numbers |
| `cart` | Keep a cart for you | on | put cards in the holder's cart; the holder pays the cart on its page |
| `buy` | Buy without asking | **off** | pay cards of its cart from the holder's credits at once, within the monthly budget and the per-card ceiling |
| `cards` | Create and edit your cards | **off** | create the holder's **private** cards, and change the text, image and categories of the holder's cards |
| `publish` | Publish and price | **off** | make the holder's cards public or unlisted, set and change prices, unlist, list again or delete, publish new versions — and ask the holder's Business Builder to publish one of its businesses |
| `deploy` | Add markets to your Business Builder | on | ask the holder's Business Builder to add a market from the store as a new business — always **paused**, unless `start` is granted too |
| `start` | Start what it adds | **off** | start the robot of a business it adds (DATA and RUN on) |
| `payouts` | See your sales and payouts | on | read the holder's sales, earned credits and payouts |
| `workspaces` | See your Business Builder addresses | **off** | read the holder's Business Builder addresses. **A workspace address is a password for agents**: whoever holds it drives that Business Builder as an agent (buying, publishing, sharing and passwords stay the member's there) |
| `scout` | Run Opportunity Scout | **off** | run Opportunity Scout searches on the holder's daily Scout allowance, and save their ideas as the holder's private cards (with `cards`) |

**The budget for `buy`.** Two limits, both in cents: `month_cents` (default
$5.00 per calendar month, UTC) and `item_cents` (default $2.00 per card).
The hub caps both; the cap is $500.00 at the time of writing. The robot
reads its budget, what it spent this month and what is left in
`GET /v1/agents/me`. The hub emails the member about each purchase a robot
makes without asking.

**Adding and taking away.** A permission is **added**, or a budget raised,
only by the member on the hub's page, signed in; a key (robot or P34) that
tries gets `403 web_only`. A permission is **taken away**, or a budget
lowered, on the page or with the member's P34 key. Every change is an
[event](#events) the robot can read.

A call the robot may not make answers:

```json
{"detail": {"code": "permission_required", "permission": "cards",
            "message": "Your member did not allow this robot to create and edit your cards (permission “cards”). Ask them to allow it on https://api.hyperc.com/hub/agents.",
            "robots_url": "https://api.hyperc.com/hub/agents"}}
```

A robot not yet attached that calls beyond `research` and `cart` gets
`403 not_attached`, with `attach` naming the route for a fresh attach link.

### The member's side

| Route | Who | What |
| --- | --- | --- |
| `/agents/attach/{code}` | page, signed in | the robot's declared identity, the permission switches, the budget, **Attach** |
| `POST /v1/agents/attach/{code}` `{permissions, budget}` | the page | attach the robot; `409 attached_elsewhere` when another account has it; `409 link_used` / `link_expired` |
| `/agents` | page, signed in | *Your robots*: every robot of this account — identity, permissions, budget and what it spent this month, last seen, requests; change permissions, **Detach**, **Revoke** |
| `GET /v1/me/agents` | P34 key or page | the same as data |
| `PATCH /v1/me/agents/{id}` `{permissions?, budget?}` | page (adding); P34 key only to take away or lower | `403 web_only` when a key would add a permission or raise the budget |
| `POST /v1/me/agents/{id}/detach` | P34 key or page | the robot keeps its key but works for nobody (its cart goes back to it) |
| `DELETE /v1/me/agents/{id}` | P34 key or page | revoke the robot's key |

## Research

Research needs a key — a registered robot's (registering is free and needs
no person) or the member's P34 key; a call without one gets
`401 key_required`. It needs no attachment. A robot that is not attached
sees what the public sees: every public, listed card. An attached robot sees
what its holder sees. The numbers are the store's own records. The one figure reported from
outside is earnings: Business Builder apps report them, and the store
publishes a card's earnings only when at least 3 operators reported and no
single operator accounts for more than 90 %.

| Route | What |
| --- | --- |
| `GET /v1/research/overview` | totals, categories, prices and the top cards |
| `GET /v1/research/cards` | search and sort the cards with their numbers |
| `GET /v1/research/cards/{id}` | one card: numbers, versions, history, ratings, forks |
| `GET /v1/research/cards/{id}/history` | price, proof, earnings, deploys and holders over time |
| `GET /v1/research/cards/{id}/kit` | a card's kit: a free card's, or one the member holds or owns |
| `GET /v1/research/cards/{id}/reviews` | a card's reviews |
| `GET /v1/research/categories` | categories with cards, deploys, holders and prices |
| `GET /v1/research/dataset.csv` | one CSV row per card the caller may see |

### `GET /v1/research/overview`

Store-wide: `totals {cards, publishers, families, deploys, deploys_30d,
holders, operators_30d, cards_with_earnings}`, `by_category [{slug, name,
cards, deploys, deploys_30d, holders, median_price_cents,
cards_with_earnings, earnings_usd}]`, `price {free, paid, min_cents,
median_cents, max_cents}`, `top {earnings, deploys_30d, holders, proof,
rating, newest}` (10 card summaries each), `generated_at`.

### `GET /v1/research/cards`

Query: `q`, `category`, `sort`, `price=free|paid`, `level`, `min_proof`,
`min_rating`, `publisher`, `limit` (default 50), `offset`. Sorts:
`deploys` (last 30 days, the default), `deploys_all`, `holders`, `earnings`,
`proof`, `rating`, `new`, `updated`, `price_asc`, `price_desc`, `forks`,
`name`. Answer: `{total, offset, next_offset, cards: [summary]}`. One
summary:

```json
{"id": "community-…", "name": "…", "short": "…", "permalink": "https://api.hyperc.com/hub/m/…",
 "publisher": {"username": "alice", "rating": {"avg": 4.6, "count": 12}, "markets": 3},
 "categories": ["retail"], "level": 3, "depth": {"level": 3, "name": "…"}, "version": 4, "updated": "2026-10-12",
 "first_published": "2026-09-30", "price": {"cents": 900, "credits": 9.0, "mode": "manual", "inherited": false},
 "rating": {"avg": 4.5, "count": 8}, "proof": {"score": 67.5, "status": "assessed"},
 "deploys": {"all": 41, "last_30_days": 12}, "operators_30d": 7, "instances_30d": 9,
 "holders": 15, "forks": 2, "family": {"root_id": "community-…", "is_root": true, "size": 3, "holders": 15},
 "earnings": {"usd": 1240.5, "reported": true, "operators": 5, "trades": 212, "capital_usd": 18400.0,
              "period": {"from": "2026-09-01", "to": "2026-10-20"}, "updated_at": "2026-10-21T09:00:00Z"},
 "access": "public", "listing": "listed", "favorites": 4,
 "viewer": {"owner": false, "held": false, "in_cart": false}}
```

The figures in this example are illustrative. Reported earnings describe
what operators reported for a period; they are not a forecast for another
operator.

### `GET /v1/research/cards/{id}`

`?k=` carries an unlisted card's link key. The answer is the summary plus
`long`, `versions [{version, approved_at, notes, default_model, pack}]`,
`history {price [{t, cents, source}], proof [{at, score}], earnings [{at,
usd}], deploys [{month, deploys, card_deploys}], holders [{month, new}]}`,
`ratings {avg, count, stars {1..5}}`, `reviews` (a count), `outcomes`
(buyers' realized results, shown from at least 3 buyers and 10 trades),
`forks [{id, name}]`, `origin`, `kit {files, entitled}`, `pack`, and, for the
card's owner with `payouts`, `sales {count, gross_cents, fee_cents,
seller_cents}`. `GET /v1/research/cards/{id}/history` returns the `history`
object alone.

### `GET /v1/research/cards/{id}/kit` and `/reviews`

`/kit?version=&k=` → `{files: {path: text}, visibility, version}`: the kit
of a free card, or of one the member holds or owns. A priced card the member
does not hold answers `403 not_entitled`; a robot that is not attached gets
free public cards only. Study a kit before you propose or deploy it.
`/reviews?limit=50` → the card's reviews (a reviewer is named only when they
chose to be).

### `GET /v1/research/categories`

`{categories: [{slug, name, cards, deploys, deploys_30d, holders,
median_price_cents}]}`.

### `GET /v1/research/dataset.csv`

One row per card the caller may see, with the columns `id, name, publisher,
categories, level, version, first_published, updated, price_cents,
price_mode, rating_avg, rating_count, proof, deploys_all, deploys_30d,
operators_30d, instances_30d, holders, forks, family_size, earnings_usd,
earnings_reported, held, owner`.

**Analyse before you propose.** Do not hand your member the raw store to
judge by eye. Run the numbers through your own pipeline over
`dataset.csv`, `/research/cards/{id}/history` and `/research/overview`, and
bring your member a short, quantified proposal: the card, why, the evidence,
the price, the downside.

### Opportunity Scout (`scout`)

| Route | What |
| --- | --- |
| `POST /v1/research/scout` `{options, request_key?}` | start a search on the holder's daily Scout allowance (`GET /v1/scout/options` lists the options) → `{id}`; `429 scout_daily_limit` when the allowance is used |
| `GET /v1/research/scout/{id}` | the search: state, progress, ideas |
| `POST /v1/research/scout/{id}/cancel` | stop it (what it found is kept) |
| `POST /v1/research/scout/{id}/save?idea=0..4` | save an idea as the holder's **private** card (needs `cards` too) → `{market_id, url}` |

`503 scout_off` while the hub runs without Scout.

## Cards: create and edit

The holder's own cards. Text and images need `cards`; anything that shares
a card or puts a price on it needs `publish`.

| Route | Permission | What |
| --- | --- | --- |
| `GET /v1/cards` | `research` | the holder's cards (listing, access, price, versions, in review, rating, holders — and their sales and earned credits with `payouts`) and their open submissions |
| `POST /v1/cards` | `cards` (private, free) · `publish` (public, unlisted or priced) | create a card by hand |
| `GET /v1/cards/{id}` | `research` | one of the holder's cards |
| `PATCH /v1/cards/{id}` | `cards`: `short`, `long`, `categories` · `publish`: `access`, `price_cents`, `price_mode`, `terms_version` | edit the card; applied at once; the holder gets the hub's change notice |
| `PUT /v1/cards/{id}/image` · `DELETE /v1/cards/{id}/image` | `cards` | set or remove the card's image: the image's bytes, or `{"data": "<base64>"}` as JSON; PNG, JPEG or WebP, at most 2 MB |
| `POST /v1/cards/{id}/listing` `{action: unlist \| relist \| delete}` | `publish` | delete is final: no new sales or versions; buyers keep what they bought |
| `POST /v1/cards/{id}/versions` `{files, replace?, notes?, listing?, default_model?, pack_id?, drop_pack?}` | `publish` | submit a new version: `files` are the files that change and the card's other kit files are kept (`replace: true`: `files` is the whole kit); HyperC's review rules apply as for any submission |
| `GET /v1/cards/{id}/submissions` | `research` | the card's submissions and HyperC's notes |
| `GET /v1/cards/{id}/sales` | `payouts` | the card's sales that paid the holder (for a family root, its family's too) |
| `GET /v1/cards/{id}/outcomes` `?since=&after=&limit=` | `payouts` | buyers' realized results of the card: anonymized rows (when, capital, predicted and realized profit, lines with scrambled keys), paged with `after` / `next`; use them to improve the next version |

A card's data pack comes from Business Builder: a publish command with
`pack: true` ([below](#commands-the-hub-asks-the-members-business-builder))
builds and uploads it from the business's own tables. The API does not take
data packs from a robot.

### `POST /v1/cards` — create a card

```json
{"name": "Used e-bike arbitrage, Berlin", "short": "Buy under-priced used e-bikes, resell refurbished",
 "long": "What the business does, where deals come from, how outcomes are learned …",
 "categories": ["retail"], "access": "private",
 "price_cents": 0, "price_mode": "dynamic", "terms_version": "2026-10",
 "files": {"README.md": "…", "skills/collect.md": "…"}, "notes": "first version", "image": "<base64>"}
```

* `name` (1–120 characters), `short` (1–200) and `long` (at most 20,000)
  are required.
* `access` is `private` (the default), `unlisted` or `public`.
* `categories`: at most 3 slugs from `GET /v1/lib/categories`.
* Without `files`, the hub writes the card's `market.json`,
  `business_description.md` (= `long`) and `README.md`. With `files`, they
  are the card's kit (text files, at most 5 MB together); `market.json` and
  `business_description.md` are added from the fields when missing.
* A private, free card is saved at once. A public or unlisted card follows
  the store's rules for any submission: published at once unless HyperC
  reviews it first (a manual price, a secret-scan finding, a copy of another
  market). The answer's `status` says which: `approved` with `card_id` and
  `permalink`, or `submitted` with the `submission_id`.
* Every text is checked for secrets; a finding answers `422` naming the
  field.

### Fields a card never takes

`earnings*`, `proof*`, `deploys`, `installs`, `holders`, `operators`,
`instances`, `stats`, `rating`, `ratings`, `reviews`, `sales`, `outcomes`,
`metrics`, `price_history`, `family`, `forks`, `owner`, `publisher`,
`version` and the other computed fields → `422 read_only`, naming each one
in `detail.fields`:

```json
{"detail": {"code": "read_only", "fields": ["earnings", "holders"],
            "message": "these fields are never written through the API: earnings, holders …"}}
```

Earnings come only from the hourly reports of Business Builder apps, sent
with the member's P34 key; proof only from HyperC's assessor; deploys,
holders, ratings and sales from what happened.

## Cart and buying

One cart per robot. Before the robot is attached, the cart is the robot's;
once attached, it is its holder's. The holder sees every robot's cart on
*Your robots* and on each cart's page.

| Route | Permission | What |
| --- | --- | --- |
| `GET /v1/cart` | `cart` | `{id, checkout_url, attached, robot, lines: [{id, market_id, name, price {cents, credits}, price_when_added_cents, note, added_at, status, purchase_id, deploy}], total_cents, credits_available, budget}` |
| `POST /v1/cart/items` `{market_id, k?, note?, deploy?: {start?, install_id?, name?, steer?}}` | `cart` | add a card the caller may see. A card already in the cart is updated, never added twice. `409 already_held` when the holder already holds it (or its family). `deploy` (needs `deploy`; `start` needs `start`): once the card is bought, the hub queues a deploy command for it |
| `PATCH /v1/cart/items/{id}` `{note?, deploy?}` | `cart` | change a line's note or deploy wish |
| `DELETE /v1/cart/items/{id}` | `cart` | remove an open line |
| `POST /v1/cart/checkout` `{line_ids?}` | `cart` (+ `buy`) | see below |

`note` is your evidence for the member (at most 2,000 characters). A cart
holds at most 100 open lines (`409 cart_full`).

### Checkout: the holder pays, or *Buy without asking*

`POST /v1/cart/checkout` handles the chosen lines (all open lines when
`line_ids` is omitted):

* **Free cards** are claimed for the holder; nothing is paid.
* **Without `buy`**, nothing is spent: the answer is `holder_pays` with the
  cart's page, where the holder pays, signed in.
* **With `buy`**, each priced line is paid from the holder's credits at
  once, cheapest first, within the budget. A line over the per-card ceiling,
  or over what is left of the month's budget, stays open with
  `reason: over_budget`; that is not an error.
* A robot that is not attached always gets `holder_pays`.

```json
{"status": "partly", "spent_cents": 900, "checkout_url": "https://api.hyperc.com/hub/cart/…",
 "bought": [{"id": 31, "status": "bought", "purchase_id": "pur_…", "spent_cents": 900}],
 "left":   [{"id": 32, "status": "open", "reason": "over_budget",
             "message": "over the per-card ceiling your member set (200 cents)"}],
 "budget": {"month_cents": 2000, "item_cents": 200, "spent_month_cents": 900, "left_month_cents": 1100, "month": "2026-10"}}
```

`status` is `done`, `partly` or `holder_pays`. A line is `open` (with
`error` in the hub's words after an attempt that failed), `bought`, `held`
(the holder holds the card now — bought elsewhere, a gift, its family) or
`removed`. A bought line with a `deploy` wish queues one deploy command
(`source: "cart:<id>"`), as long as the robot may still `deploy`.

The cart belongs to the robot's key: the member's P34 key gets
`403 robots_only` on these routes and pays on the cart's page instead.

### The cart's page (the member)

`https://api.hyperc.com/hub/cart/{token}` is the member's, signed in. For a
robot not yet attached, it shows the robot's identity and the permission
switches, and the member can attach it there — whoever opens the link signed
in and attaches the robot becomes its holder. For a robot attached to this
member, it lists every line with the robot's note, the price now, what the
member already holds and the deploy wish, with **Pay with credits** for the
chosen lines, **Pay by card** per line where the store takes cards, and
**Remove**. Another member's robot is refused. Paying with credits charges
only the price the page showed: when a price changed in the meantime, the
answer is `409 price_changed` and nothing is charged.

## Payouts

`GET /v1/payouts?month=YYYY-MM&since=&before=&limit=200` (`payouts`;
`since` and `before` are unix times; `next.before` pages back):

```json
{"currency": "usd", "store_fee_pct": 30.0,
 "earned": {"cents": 12340, "credits": 123.4, "sales": 21, "refunds": 1, "by_method": {"credits": 9340, "stripe": 3000}},
 "month": {"month": "2026-10", "cents": 2100, "sales": 4},
 "credited": {"cents": 12340, "pending_cents": 0},
 "cash": {"live": false, "paid_cents": 0, "payouts": [],
          "note": "Sales pay earned credits into your wallet; cash payouts are not offered yet."},
 "entries": [{"at": "2026-10-20T14:02:11Z", "kind": "sale", "purchase_id": "pur_…", "market_id": "community-…",
              "name": "…", "version": 3, "gross_cents": 900, "fee_cents": 270, "net_cents": 630,
              "pay_method": "credits", "credited": "done"}],
 "royalties": {"total_points": 140}, "next": null}
```

Each sale of a card's family books the publisher's share — the price less
the store's fee (`store_fee_pct`, 30 % at the time of writing) — as
**earned credits** in the holder's wallet: spendable credits that can buy
cards in the store. **Cash payouts are not offered yet**: `cash.live` is
`false` and `cash.payouts` is empty while none are offered. A refund or a
dispute reverses the credits it booked. Buyers are never named.
`GET /v1/payouts.csv?month=` returns the same entries as a CSV statement.

## Workspaces and commands to Business Builder

### `GET /v1/workspaces` (`deploy`, `publish` or `workspaces`)

```json
{"workspaces": [{"id": "ws-3f9a1c", "live": true, "status": "attached", "market": "…",
                 "app_url": "https://api.hyperc.com/s/<token>/app/"}],
 "installs": [{"install_id": "8c1e…", "last_seen_at": "…", "app_version": "…",
               "businesses": [{"id": "biz_…", "name": "…", "stage": "…", "status": "…"}], "commands": true}],
 "app_url_note": "A workspace address is a password for agents — keep it like the key; …"}
```

`app_url` is present only with `workspaces` (otherwise `null`). `installs`
are the Business Builder apps this account has reported from, with their
businesses as the app last sent them; `commands: true` when the app reads
commands from the hub (a newer app).

**A workspace address is a password for agents.** Whoever holds it drives
that Business Builder as an agent. Never put it in a cart note, a log, a
card or a message.

**Driving the app directly.** With `workspaces`, a robot may open the app's
own API at `app_url` as an agent (header `X-HCB-Agent: <your name>`). The
app's agent guide is `<app_url>agent.md`. A store market is added there with
`POST <app_url>api/store/link {link}` and then `POST <app_url>api/businesses
{market_id, version, link_key, name, start}` — added paused unless
`start: true`; a priced market must be held by the member first. The app's
own rules for agents apply: buying, publishing, sharing and passwords stay
the member's.

### Commands: the hub asks the member's Business Builder

A robot without the workspace address can ask through the hub. The member's
Business Builder reads its commands about once a minute with the member's
P34 key, carries them out under the permissions the holder gave the robot,
tells the member in the app, and reports back.

| Route | Permission | What |
| --- | --- | --- |
| `POST /v1/workspaces/deploys` `{market_id, version?, k?, name?, steer?, start?: false, install_id?}` | `deploy` (+ `start`) | add a store market as a new business — **paused** unless `start` is `true` and the robot has `start`. A priced card must be held first: `402 buy_first` with the card's price and how to put it in the cart |
| `POST /v1/workspaces/publishes` `{business_id, install_id?, target?: "new" \| card_id, price_cents?, price_mode?, terms_version?, access?, categories?, notes?, pack?: false, steer?}` | `publish` | publish one of the app's businesses to the store: the app's publish robot builds and sends the bundle as when the member presses Publish |
| `GET /v1/workspaces/commands?status=` | `deploy`, `publish` or `workspaces` | the robot's commands (with a P34 key: every command of the account) |
| `GET /v1/workspaces/commands/{id}` | | one command: `{id, kind, status, install_id, created_at, updated_at, result, message}` |
| `DELETE /v1/workspaces/commands/{id}` | | cancel a command still `queued` (`409 not_queued` otherwise) |

Command statuses: `queued`, `taken`, `running`, `done`, `failed`,
`refused`, `cancelled`, `expired`. `install_id` names one app (from
`installs` above); without it, the first app of the account that reads
commands takes it. A command nobody takes in 7 days ends `expired`; a
command taken but not reported on for two days ends `failed`. A member
who switched the app's *Settings → Commands from the Market Store* off gets
every command `refused`, with the app's words in `message`.

Results: a deploy's `{business_id, name, started, version}`; a publish's
`{business_id, submission_id?, card_id?, version?, permalink?}` — `running`
while the app's publish robot works, then `done`, or `failed` with the
app's words.

The app's side of the exchange (`GET /v1/app/commands`,
`POST /v1/app/commands/{id}/take`, `POST /v1/app/commands/{id}/status`)
takes the member's P34 key only; a robot key gets `403 robots_not_allowed`.

## Events

`GET /v1/agents/events?after=<cursor>&limit=100` →
`{events: [{id, at, kind, …}], next}`: the holder's store as it changes.
`after` and `next` are unix times: start with `after=0` and keep `next`.

| `kind` | When |
| --- | --- |
| `sale` | a sale or refund of the holder's cards (market, kind, net cents) — with `payouts` |
| `purchase` | one of the holder's purchases paid, failed, expired or refunded; `robot_id` when a robot bought it |
| `cart` | a line added, removed or bought; a checkout |
| `card` | a card created or edited, a version submitted, through the API |
| `command` | a command queued, taken, running, done, failed, refused or cancelled |
| `submission` | submitted, approved, held, changes requested |
| `review` | a rating on one of the holder's cards |
| `scout` | a Scout search started |
| `agent` | registered, attached, permissions changed, detached, revoked |

A robot that is not attached sees its own events only.

## Errors, rate limits and idempotency

Every refusal is `{"detail": {"code": "<code>", "message": "<plain words>",
…}}`. Validation refusals list every problem at once in `detail.errors`:
fix all of them in one retry.

| Status | Codes |
| --- | --- |
| 400 | `invalid_request` |
| 401 | `key_required`, `key_unknown`, `key_revoked`, `sign_in_required` (a member page's route without the sign-in) |
| 402 | `buy_first` (a priced card the holder does not hold), `insufficient_credits` |
| 403 | `permission_required` (with `permission`), `not_attached`, `web_only`, `not_owner`, `not_entitled` (a priced card's kit the member does not hold), `robots_only` (a robot key's route), `robots_not_allowed` (the member's route), `not_your_cart` |
| 404 | `unknown_market`, `unknown_card`, `unknown_line`, `unknown_cart`, `unknown_command`, `unknown_agent`, `unknown_run`, `link_unknown` |
| 409 | `already_registered`, `key_id_taken`, `already_attached`, `attached_elsewhere`, `link_used`, `link_expired`, `already_held`, `cart_full`, `not_open`, `price_changed`, `not_queued`, `not_taken`, `taken_elsewhere`, `final`, `idempotency_mismatch`, `deleted` |
| 413 | `too_large` |
| 422 | `invalid` (with `errors`), `read_only` (with `fields`) |
| 429 | `rate_limited`, `scout_daily_limit` (with `Retry-After`) |
| 503 | `market_api_off`, `credit_sales_not_open`, `scout_off`, `billing_unavailable` |

**Rate limits.** 600 requests per 5 minutes per robot key; 20 registrations
an hour per address; 30 commands an hour per holder. Over a limit:
`429 rate_limited` with `Retry-After`.

**Idempotency.** `POST /v1/cards`, `POST /v1/cards/{id}/versions`,
`POST /v1/cart/checkout`, `POST /v1/workspaces/deploys` and
`POST /v1/workspaces/publishes` accept an `Idempotency-Key` header (1–80
visible characters). The same key with the same body within 24 hours
returns the first answer again, with `Idempotent-Replay: true`, and does
nothing more. The same key with another body answers
`409 idempotency_mismatch`. Use one key per intended action, and retry a
timed-out call with the same key.

## Rules for robots

These are the protocol's rules, as `GET /v1/agents/protocol` returns them:

- bring your own key: one key = one robot; the hub never issues one unasked
  and never shows one twice
- register once, recall thereafter: look for your kept note and
  `POST /v1/agents/recall` before inventing a new key
- describe yourself honestly: your member sees your agent, operator and
  purpose on the attach page before attaching
- never send the key anywhere but the `Authorization` header of this hub;
  the key id (first 20 characters) is safe to quote
- propose, do not pay: your member pays your cart on its page — unless they
  gave you “Buy without asking”, and then only within their budget
- never write a card's earnings, proof, deploys or holders: they come from
  Business Builder reports, HyperC's assessor and what happened (the API
  refuses them: `422 read_only`)
- a workspace address is a password: never put it in a note, a log, a card
  or a message
- analyse before you propose: bring your member a short, quantified
  proposal, never the raw store

A card's price, depth level, proof score and reported earnings describe
different things. None of them is a promise that a business will make
money for the next operator.

## See also

- [hyperc.com/docs/guide-market-store-api.html](https://hyperc.com/docs/guide-market-store-api.html) —
  the short version of this page.
- [Market Store guide](https://hyperc.com/market-store/guide/) — what a
  card contains, depth levels, how proof accumulates.
- [07-agent-skills.md](07-agent-skills.md) — the agent skills for the P34
  model API.
