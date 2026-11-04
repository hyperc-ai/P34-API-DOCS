# 12. Market Store API for robots

Base URL: **`https://api.hyperc.com/hub`** · service manifest:
**`https://api.hyperc.com/hub/v1/manifest`** · the protocol as data:
**`https://api.hyperc.com/hub/v1/agents/protocol`**

The HyperC Market Store (the hub) holds market cards: descriptions of
markets, their kits, versions, prices, proof assessments and the earnings
that Business Builder apps report for them. This API lets a robot — an LLM
session, a script, a service, or a person driving one — work in the store
for a member: it registers under its own key, researches the store, keeps a
cart, buys, sells and gives copies of markets within the member's limits,
creates and edits cards, publishes, follows sales, and asks the member's
Business Builder to add a market or publish a business.

This page is a different API from the P34 model API in
[02-endpoints.md](02-endpoints.md): another base URL, other keys, other
routes. A member's P34 key works here too, and so do keys the member creates
for a robot on the hub (see [Who may call](#who-may-call)).

The roles stay apart by design:

* **A robot never holds the member's login, card or money.** It registers
  under its own key and proposes. Its member (the *holder*) attaches it, in
  person and signed in, on a link the robot hands over, and chooses what it
  may do.
* **Nothing is bought by a robot's action alone**, unless the holder switched
  on *Buy without asking* for that robot, with a monthly budget and a
  per-card ceiling of the holder's choosing. Otherwise the holder pays the
  robot's cart on the cart's page, signed in.
* **Nothing is sold or given away by a robot's action alone**, unless the
  holder switched on *Sell copies* or *Give copies* for it, limited to the
  collections, minimum price and monthly number of copies the holder chose;
  every such action is listed in an e-mail digest to the holder (at most one
  mail every 30 minutes). Authorship of a card is never moved by a key.
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
- [Keys made by your member](#keys-made-by-your-member)
- [Research](#research)
- [Cards: create and edit](#cards-create-and-edit)
- [Cart and buying](#cart-and-buying)
- [Trading: copies, the order book, offers](#trading-copies-the-order-book-offers)
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
| Feature detection | `GET https://api.hyperc.com/hub/health` → `features.market_api`, `features.app_commands`; once the licenses release is switched on, also `features.events_cursor`, `key_scopes`, `member_keys`, `master_key`, `cart_copies` and the licenses' keys (below) |
| The publisher terms in force and their text | `GET https://api.hyperc.com/hub/v1/store/publisher-terms` (`?version=` for another one); the page `https://api.hyperc.com/hub/terms/publisher` |

The manifest is the authoritative list of endpoints: the hub builds the
manifest, the protocol, both pages and `llms.txt` from one list, so they
agree with each other. When `features.market_api` is absent from
`/health`, the routes answer `503 market_api_off`.

```json
{"name": "HyperC Market Store", "base_url": "https://api.hyperc.com/hub",
 "api_base": "https://api.hyperc.com/hub/v1", "openapi": "https://api.hyperc.com/hub/openapi.json",
 "docs": {"api": "…/docs/api", "agents": "…/docs/agents", "build": "…/docs/build", "llms_txt": "…/llms.txt",
          "reference_markdown": "https://github.com/hyperc-ai/P34-API-DOCS/blob/main/docs/12-market-store-api.md"},
 "agents": {"built_for_agents": true, "protocol": "…/v1/agents/protocol",
            "human_needed_to_register": false, "human_needed_to_research": false,
            "human_needed_to_spend": true, "human_needed_for_authorship": true,
            "autonomous_buying": "a per-robot switch (“Buy without asking”) …",
            "autonomous_selling": "a per-key switch (“Sell copies”) …", "autonomous_transfers": "…"},
 "auth": {"scheme": "Authorization: Bearer <key>", "register": "POST /v1/agents/register {…}",
          "recall": "POST /v1/agents/recall {key_id, recall_phrase} -> known?, phrase_matches?"},
 "permissions": [{"name": "research", "default": true, "label": "Research the store", "what": "…", "available": true}, …],
 "publisher_terms": {"version": "hcb-publisher-2026-11", "store_fee_pct": 30.0, "note": "…"},
 "features": {"market_api": 1, "app_commands": 1, "research": 1, "cart": 1, "scout": 1, "events": 1,
              "events_cursor": 1, "key_scopes": 1, "member_keys": 1, "master_key": 0, "cart_copies": 1,
              "licenses": 1, "licenses_mode": "1", "orders": 1, "asks": 1, "offers": 1, "authorship": 1,
              "market_feed": 1, "family_versions": 1, "family_listing": 1, "version_notes": "announced",
              "version_notes_min": 20},
 "fees": {"grant_pct": 30, "resale_pct": 10, "resale_min_fee_cents": 1, "grant_min_fee_cents": 1, "fork_royalty_pct": 5},
 "rate_limits": {"general": {"requests": 600, "seconds": 300}, "trade_read": {"requests": 1800, "seconds": 300},
                 "trade_write": {"requests": 30, "seconds": 60, "account_requests": 120},
                 "orders_per_hour": {"key": 60, "account": 120}, "long_poll_max_seconds": 25},
 "idempotency": {"header": "Idempotency-Key", "chars": "1-80 of [A-Za-z0-9._:-]", "required_on": […], …},
 "cursors": {"feed": "/v1/licenses/feed?after=<int>", "moves": "/v1/licenses/moves?after=<int>",
             "events": "/v1/agents/events?cursor=<int>"},
 "endpoints": [{"group": "Identity", "method": "POST", "path": "/v1/agents/register", "who": "-", "what": "…"}, …],
 "flow": [{"step": 0, "do": "discover", "request": "GET …/v1/manifest", "note": "…"}, …]}
```

The figures in this example are illustrative: read the live ones. In the
manifest, `features` always lists every key, and a trading power is `1` only
while the store has it switched on for everyone. `publisher_terms.version` is
the `terms_version` a card's first manual price carries
(`hcb-publisher-2026-11` from the licenses release on). `fees`,
`rate_limits`, `idempotency` and `cursors` state what the
[trading routes](#trading-copies-the-order-book-offers) use.

**The licenses' keys in `/health.features`.** Once the licenses are switched
on for everyone, `features.licenses` is `1` and the store announces each
power separately: `license_copies` (more than one copy of a market),
`order_book` (copies for sale between members), `direct_offers`,
`authorship_transfer`, `operating_check` (a last copy needs the
[operating check](#the-operating-check-before-a-last-copy-leaves)) and
`market_feed`, with the fees beside them: `grant_fee_pct`, `resale_fee_pct`,
`resale_min_fee_cents`, `grant_min_fee_cents` and `fork_royalty_pct` (also in
`GET /v1/store/pricing`). Before that `features.licenses` is `0` and nothing
else is announced; a robot of a member in an early group reads its own
powers in `GET /v1/agents/me` → `licenses.powers`. A route whose power is off
answers `503` (`licenses_off`, `license_copies_off`, `resale_off`,
`offers_off`, `authorship_off`). Read these numbers; never hard-code them.

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
11. read the market:    GET /v1/licenses/book/{id}, /licenses/feed?after=<id>, /licenses/series/{id}
12. buy copies:         POST /v1/licenses/orders {market_id, copies, max_unit_cents}   (buy; Idempotency-Key)
13. sell or give:       POST /v1/licenses/asks (sell), POST /v1/licenses/offers (transfer)
14. follow your copies: GET /v1/licenses/mine, /licenses/moves?after=<id>, /agents/events?cursor=<id>
                                                                     (integer cursors: nothing is missed)
```

Every request after step 2 carries `Authorization: Bearer <your key>`.
Research needs the key but no attachment; everything else is what the
member allowed. Steps 11–14 are the
[trading routes](#trading-copies-the-order-book-offers): they answer once
the store has switched the licenses on (`features.licenses`).

## Who may call

| Caller | How it is recognised | What it may do |
| --- | --- | --- |
| **A robot** (an agent key) | `Authorization: Bearer <80 characters [A-Za-z0-9]>`, registered here | its own identity and cart, and research of what the public sees; once attached, what its holder granted ([permissions](#permissions)), acting as the holder |
| **A key the member made** | the same 80-character Bearer, created on *Your robots* (shown once) | exactly what a robot's key may do, with the permissions, collections, limits and budget the member chose ([below](#keys-made-by-your-member)) |
| **The master key** | a key the member made that holds `manage_keys` (set on *Your robots* only; at most one per member) | what its permissions allow, and creating, changing and revoking the member's other keys within its own limits |
| **The member's P34 key** | `Authorization: Bearer test-…` / `profit-…` (a key from the [console](https://api.hyperc.com/app/)) | everything a robot may, as the member, with every permission — except that carts are robots' (`403 robots_only`), a purchase or a widening trading action from the key is an intent the member confirms on the hub's page, and raising a robot's permissions needs the member's page |
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

The answer also says what kind of key this is and what it may trade:

```json
{"kind": "member", "master": false, "parent_id": null,
 "scopes": {"collections": [{"id": "col_3f9a1c2b4d5e", "name": "Resell"}],
            "families": [{"root_market_id": "community-…", "name": "…", "usable": 3, "transferable": 2,
                          "listed": 1, "infinite": false}]},
 "limits": {"min_unit_cents": 100, "min_pct_of_grant": 80, "month_copies_out": 10, "mail_each": false,
            "floor_note": "never below $1.00 a copy and never below 80 % of the author's price — whichever is higher"},
 "copies_out_month": 3, "pool": null,
 "available": {"sell": true, "transfer": false},
 "rate": {"general": {"limit": 600, "seconds": 300}, "trade_read": {"limit": 1800, "seconds": 300},
          "trade_write": {"limit": 30, "seconds": 60, "account_limit": 120}},
 "licenses": {"mode": "1", "powers": {"copies": true, "resale": true, "offers": false, "authorship": false}}}
```

`kind` is `robot` for a key a robot registered and `member` for one the
member created; `master` and `parent_id` place it among the member's
keys. `scopes` are the collections it may sell or give from (`"all"` by
default) with the families in them and the holder's copies of each
(`infinite` for a family the holder authors); `limits` and `copies_out_month` (the
copies it put up for sale or offered this calendar month) are explained under
[Collections and limits](#collections-and-limits-on-a-key); `pool` is the
budget and monthly copies a master shares with its keys (`null` alone);
`available` says whether *Sell copies* and *Give copies* are open for the
holder; `rate` is the key's request limits. `licenses` is there while the
licenses are switched on, for some members or for everyone: `powers` are what
the store lets this holder do now.

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
| `buy` | Buy without asking | **off** | pay for cards — its cart, orders in the order book and priced offers made to the holder — from the holder's credits at once, within the monthly budget and the per-card ceiling |
| `cards` | Create and edit your cards | **off** | create the holder's **private** cards, and change the text, image and categories of the holder's cards |
| `publish` | Publish and price | **off** | make the holder's cards public or unlisted, set and change prices — accepting HyperC's publisher terms for the holder (the store's fee on each sale; `terms_version` is `GET /hub/v1/manifest` → `publisher_terms.version`, `hcb-publisher-2026-11` from the licenses release on; the terms themselves: `GET /hub/v1/store/publisher-terms`) —, unlist, list again or delete, publish new versions, and ask the holder's Business Builder to publish one of its businesses |
| `deploy` | Add markets to your Business Builder | on | ask the holder's Business Builder to add a market from the store as a new business — always **paused**, unless `start` is granted too |
| `start` | Start what it adds | **off** | start the robot of a business it adds (DATA and RUN on) |
| `payouts` | See your sales and payouts | on | read the holder's sales, earned credits and payouts |
| `workspaces` | See your Business Builder addresses | **off** | read the holder's Business Builder addresses. **A workspace address is a password for agents**: whoever holds it drives that Business Builder as an agent (buying, publishing, sharing and passwords stay the member's there) |
| `scout` | Run Opportunity Scout | **off** | run Opportunity Scout searches on the holder's daily Scout allowance, and save their ideas as the holder's private cards (with `cards`) |
| `sell` | Sell copies | **off** | list copies of the holder's markets for sale in the order book, within the minimum price, the monthly cap and the collections the holder chose |
| `transfer` | Give copies | **off** | offer copies to other members and accept copies offered to the holder, within the same limits; a priced acceptance also needs `buy` and its budget |
| `manage_keys` | Master key (on *Your robots* only) | **off** | the master key: create, change and revoke the holder's other keys — never beyond this key's own permissions, collections, limits and budget, never another master key. Never offered on the attach page (`422 invalid`); every change is listed in the holder's mail digest |

`sell` and `transfer` are offered on the pages only while the store has
those powers on (the manifest's `permissions[].available`,
`features.asks`, `features.offers`).

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

### Collections and limits on a key

A key that sells or gives copies is bound by two more things its member
sets on *Your robots*:

- **Collections (`scopes {collections}`).** `"all"` (the default) or a list of
  the member's own library collections. The key may sell or give copies only
  of the families of the cards the member put in those collections
  themselves, on the hub's page. An item added by an editor of a shared
  collection, by a submission or with the member's P34 key does not count
  until the member confirms it. A family the member authors counts as an
  unlimited number of copies. Deleting a collection, or removing an item,
  narrows the key at once. Out of scope: `403 out_of_scope`.
- **Limits (`limits {min_unit_cents, min_pct_of_grant, month_copies_out,
  mail_each}`).** The lowest price of an ask, a price cut or an offer is the
  higher of `min_unit_cents` and `min_pct_of_grant` % of the author's price —
  so a key with a floor never gives copies away free (`403 below_min_price
  {min_unit_cents}`). At most `month_copies_out` copies are put up for sale or
  offered in a calendar month (`403 over_limit {limit, cap, used, asked}`).
  `mail_each` lists every action of the key in the member's mail digest
  (orders are always listed).
- **The pool.** A master's keys share its budget and its monthly copies
  (`over_budget {pool: true}`, `over_limit {pool: true}`), so keys never
  multiply a master's limits.

With the member's P34 key, adding a card to a collection that a selling or
giving key names (`PUT /v1/lib/collections/{id}/items/{id}`, or
`PUT /v1/lib/markets/{id}/favorite` while a key sells from Favorites) answers
`202`: an intent the member confirms on the hub's page, and nothing is added
until then. A submission made with the P34 key leaves such a collection out
and says so in a warning. Removing an item never waits.

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

## Keys made by your member

A member can also create keys on *Your robots*
(`https://api.hyperc.com/hub/agents`, signed in). The key is shown **once**
and is attached at once, with the permissions, collections, limits and
budget the member chose. It works exactly like a robot's own registered key:
the cart, events, budgets and attach links are the same. One of them may be
the **master key** (`manage_keys`).

| Route | Who | What |
| --- | --- | --- |
| `POST /v1/me/agents` `{name, note?, permissions, budget?, scopes?, limits?, master?}` + optional `Idempotency-Key` | the page; a master key (for its own keys) | `201 {agent, key, key_id, recall_phrase, keep, key_shown: true, key_note}` — the key, once; a replay answers `key: null`, `key_shown: false`. The P34 key gets `403 web_only`, another robot `403 robots_not_allowed`; `503 member_keys_off` / `master_key_off` while the store has them off; `429 too_many_keys` over the number of live keys or keys a day the store allows |
| `GET /v1/me/agents/changes?after=&limit=` | P34 key, page, master key | every change to this account's keys (`create`, `attach`, `change`, `clamp`, `master_on`, `master_off`, `detach`, `revoke`), with the integer cursor `next_after` |
| `GET /v1/me/agents/{id}` | P34 key, page, master key | one key: `{agent}` with its permissions, collections, limits, budget, what it spent, its keys and its pool |
| `PATCH /v1/me/agents/{id}` `{permissions?, budget?, scopes?, limits?, name?, note?}` | page: anything; P34 key: narrowing only; a master: its own keys within its ceiling | `{agent, clamped}` |
| `DELETE /v1/me/agents/{id}?children=revoke\|keep` | P34 key, page, master key | revoke a key; a master's keys go with it unless `keep` (`children_revoked`) |

**The master key's rules.** Its ceiling is its own permissions (without
`manage_keys`), collections, limits and budget. It may create a key, or widen
one of ITS OWN keys, only within that ceiling (`403 over_ceiling {fields}`);
it may narrow any key; it never widens itself (`403 web_only`), never makes
another master (`403 master_web_only`; a second master on the page:
`409 master_exists`) and never moves authorship. Narrowing a master clamps
its keys in the same change. Every change is journaled and listed in the
member's mail digest. Revoking a master revokes its keys by default.

## Research

Research needs a key — a registered robot's (registering is free and needs
no person) or the member's P34 key; a call without one gets
`401 key_required`. It needs no attachment. A robot that is not attached
sees what the public sees: every public, listed card. An attached robot sees
what its holder sees. The numbers are the store's own records. The one figure reported from
outside is earnings: Business Builder apps report them, and the store
publishes a card's earnings once enough operators reported — one, at the
time of writing — and, while that floor is above one, only when no single
operator accounts for more than 90 %.

| Route | What |
| --- | --- |
| `GET /v1/research/overview` | totals, categories, prices and the top cards |
| `GET /v1/research/cards` | search and sort the cards with their numbers |
| `GET /v1/research/cards/{id}` | one card: numbers, versions, history, ratings, forks |
| `GET /v1/research/cards/{id}/family` | a market's family: every version a member may run, the original author's first |
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
`name` — and, under the licenses, `best_asc` / `best_desc` (by
`price.best.cents`) and the filter `asks=1` (families with copies for sale).
Answer: `{total, offset, next_offset, cards: [summary]}`.

The list is grouped by family by default (`group=family`; `group=card` lists
every card): the filters run on cards, and a family sorts where its best
matching card would. `total`, `offset` and `next_offset` then count families,
`total_cards` counts the matching cards, `collapsed` is `true`, and each
family's representative card carries `family_listing {root_market_id,
representative, matched, members, member_ids, streams, versions, newest}`.
A list per card (`group=card`, or a store that lists per card everywhere)
carries none of these four keys. One summary:

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

Under the licenses (switched on for the holder) a summary also carries the
best price and the holder's copies:

```json
{"price": {"cents": 900, "credits": 9.0, "mode": "manual", "inherited": false,
           "best": {"cents": 810, "credits": 8.1, "source": "resale", "label": "Resold copy"}, "asks": 2},
 "viewer": {"owner": false, "held": true, "in_cart": false,
            "copies": {"held": 1, "usable": 1, "listed": 0, "reserved": 0, "offered": 0, "refunding": 0,
                       "personal": 0, "transferable": 1, "infinite": false, "more": true}}}
```

`price.cents` is the author's price for the holder (a new license);
`price.best` is the cheapest way to buy one copy now (`null` when nothing can
be bought), and `price.asks` the number of asks; `viewer.held` keeps its
meaning (the holder may use the market). `viewer.copies` counts the holder's
copies of the family by state: `held` and `usable` (the same number: copies
in hand, neither for sale nor offered — what lets the holder use the
market), `listed` (for sale), `reserved` (being bought from the holder's
ask), `offered` (in a direct offer), `refunding`, and of the held ones
`personal` and `transferable`; `infinite` is `true` for the family's author;
`more` says whether the holder can buy another copy now.

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
object alone. The answer also carries `family_versions`, the same object as
[`/family`](#get-v1researchcardsidfamily). Under the licenses it adds
`trading {tradable, why_not, book, series, feed}` (whether copies of the
family can be resold, why not, and where to read its book, price series and
feed) and `history.best` / `history.trades` (the best-price step line and the
trades, as the [series](#reading-the-market) gives them).

### `GET /v1/research/cards/{id}/family`

`?k=&version=`. The card's family as the store's version picker shows it:
every version a member may run of every card built on the same original —
the original author's first, then the root author's other cards, then
everyone else's, newest first.
`{root_market_id, registry, root, selected {market_id, version}, single,
count {streams, versions, hidden_streams}, streams [{market_id, name, owner,
original, rank, access, listing, rating, entitled, claimable, price,
permalink, versions_total, latest, older, older_more, updates_note}],
viewer, words}`; each version is `{market_id, version, label, latest,
author, author_is_owner, approved_at, day, description {text, source},
depth {level, name}, pack, default_model, deploys {all, last_30_days},
outcomes, earnings, permalink, deploy {m, v, k}, selected}`. Outcomes and
earnings appear only past the store's privacy thresholds; a version
published without a description shows the card's short description,
labelled as such (`description.source: "card_short"`).
`404 unknown_market` / `unknown_version`. The version a buyer picks here is
also the version that decides a [fork royalty](#fees-and-the-fork-royalty).

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
earnings_reported, held, owner` — and, under the licenses, at the END:
`best_cents, best_source, asks_open, copies_usable, copies_listed`.

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
| `POST /v1/cards/{id}/versions` `{files, replace?, notes?, listing?, default_model?, pack_id?, drop_pack?}` | `publish` | submit a new version: `files` are the files that change and the card's other kit files are kept (`replace: true`: `files` is the whole kit); `notes` is the version's description ([below](#version-descriptions)); HyperC's review rules apply as for any submission |
| `PUT /v1/cards/{id}/versions/{n}/notes` `{notes}` | `cards` | give version `n` its missing description — only an empty one (or the API's fixed text), only by the member who published that version while they own the card, and once (`409 notes_set`; `403 not_version_author`; `422 version_notes_required` / `version_notes_secret`) |
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
 "price_cents": 0, "price_mode": "dynamic", "terms_version": "hcb-publisher-2026-11",
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
* `terms_version` is the manifest's `publisher_terms.version`
  (`hcb-publisher-2026-11` from the licenses release on). The store still
  accepts the earlier label from apps that send it; from 2026-12-21 the
  2026-11 publisher terms govern every priced market whatever label was
  recorded.

### Version descriptions

A new version of a public or unlisted card needs a description (`notes`) of
at least 20 characters at the time of writing
(`/health.features.version_notes_min`): what it does and what changed.
Members read it when they choose which version to run. Whether it is
required follows `/health.features.version_notes`: `off`; `announced` —
required when the caller announces that it supports the rule, with the
header `X-HCB-Supports: version_notes` or `"app_features":
["version_notes"]` in the body (Business Builder sends both; a robot may
send either), on `POST /v1/cards`, `POST /v1/cards/{id}/versions` and
`POST /v1/workspaces/publishes`; `all` — always. A private card is exempt
until it is made public. Refusals: `422 version_notes_required` (missing, too
short, or a placeholder) and `422 version_notes_secret` (it looks like a
secret). A version published before the rule is given its description once
with `PUT /v1/cards/{id}/versions/{n}/notes`; until then members see the
card's short description, labelled as such.

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
| `POST /v1/cart/items` `{market_id, k?, note?, deploy?: {start?, install_id?, name?, steer?, version?}, copies?, max_unit_cents?}` | `cart` | add a card the caller may see. A card already in the cart is updated, never added twice. `409 already_held` when the holder holds a usable copy (or the family); to buy MORE copies use `POST /v1/licenses/orders` — or a **copies line** (`copies` 1–100 with `max_unit_cents`, else `422 limit_required`), which is never `already_held`. `deploy` (needs `deploy`; `start` needs `start`): once the card is bought, the hub queues a deploy command for it; its `version` is also the version picked for the license (a fork's author gets the [fork royalty](#fees-and-the-fork-royalty) when the line buys a new license; a resold copy pays none) |
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
(the holder holds the card now — bought elsewhere, an accepted offer, its
family) or `removed`. A bought line with a `deploy` wish queues one deploy
command (`source: "cart:<id>"`), as long as the robot may still `deploy`.

**Copies lines** (with `features.cart_copies`). A line with `copies` is shown
with `copies`, `max_unit_cents`, `order_attempt` and the book's `quote`, and
is bought as one [order](#orders): with `buy` at checkout, within the budget
(the pre-check is `copies × max_unit_cents`), or by the holder on the cart's
page (`expect_cents[line]` is the TOTAL the page showed). An order that ended
`failed` or `expired` moves the line to a new attempt; one still confirming
is never placed again. A copies line is `bought` when its order is paid,
never `held`. `spent_cents` is what was charged — an order can fill a
cheaper resold copy.

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
answer is `409 price_changed` and nothing is charged. The page's own
routes (signed in, with the page's CSRF header) are
`POST /v1/cart/{token}/attach {permissions, budget}` (attach the cart's
robot), `POST /v1/cart/{token}/pay {pay: credits | card, line_ids?,
expect_cents?: {line id: cents}}` and `POST /v1/cart/{token}/remove
{line_id}`. Under the licenses,
markets are paid in credits: a card pays for a credits top-up, never for a
market, so a card payment answers `409 credits_only`.

## Trading: copies, the order book, offers

One copy lets you use the whole market family — the original, every version
and every market built on it that you can see — in as many of your own
businesses as you like. Extra copies are yours to sell or give, even while
you run the market. A robot trades for its holder with three permissions:
`buy` (orders, within the budget), `sell` (asks in the order book) and
`transfer` (direct offers), each within the
[collections and limits](#collections-and-limits-on-a-key) the holder set.

Each power is announced in `/health.features`: `license_copies`,
`order_book`, `direct_offers`, `authorship_transfer`, `market_feed`; the
fees are there too (`grant_fee_pct`, `resale_fee_pct`,
`resale_min_fee_cents`, `grant_min_fee_cents`, `fork_royalty_pct`), in the
manifest's `fees` and in `GET /v1/store/pricing`. Read them; never hard-code
them.

| Route | Permission | What |
| --- | --- | --- |
| `GET /v1/licenses/book/{id}` `?qty=&k=` | research | the order book of the card's family: the new license (`grant`, labelled with the author), the 50 cheapest asks at most (anonymous; `mine` on yours), `best`, `public_best`, `fees`, your copies, `feed_cursor`; with `qty` a fill-or-kill quote |
| `GET /v1/licenses/feed` `?after=&root=&kinds=&limit=&wait=` | research | the market feed: book changes, best prices, trades (integer cursor) |
| `GET /v1/licenses/series/{id}` `?days=&points=&k=` | research | the best-price step line and the trades |
| `POST /v1/licenses/orders` `{market_id, copies, max_unit_cents?, expect_total_cents?, version?: {market_id, version}, fill: "all", pay?: "credits"}` + `Idempotency-Key` | `buy` (budget) | buy N copies, cheapest first, all or nothing; a robot must send `max_unit_cents` or `expect_total_cents` |
| `GET /v1/licenses/orders` `?status=&before=&limit=` | research | your orders (a robot: the ones it placed) |
| `GET /v1/licenses/orders/{id}` | research | the order and its fills |
| `GET /v1/licenses/mine` `?root=&detail=1` | research | the holder's families: copies by state, personal/transferable, asks, offers sent |
| `GET /v1/licenses/moves` `?after=&limit=&wait=` | research | every copy in or out of the holder's account, integer cursor (`next_after`): the proof a trade or transfer happened |
| `POST /v1/licenses/asks` `{market_id, copies, unit_cents, expires_in_days?, check_id?}` + `Idempotency-Key` | `sell` | put transferable copies up for sale → `net_cents_each` |
| `GET /v1/licenses/asks` `?status=` | `sell` | the holder's asks |
| `GET /v1/licenses/asks/{id}` | `sell` | one ask |
| `PATCH /v1/licenses/asks/{id}` `{unit_cents?, copies?, check_id?}` + `Idempotency-Key` | `sell` | reprice (loses time priority) or change the number of copies |
| `DELETE /v1/licenses/asks/{id}` | `sell` | stop selling (copies being bought complete) |
| `POST /v1/licenses/offers` `{kind: copies\|grant, market_id, to: "@user", copies, unit_cents, transferable?, version?, note?, check_id?}` + `Idempotency-Key` | `transfer` | a direct offer, pending 14 days (authorship: the web only) |
| `GET /v1/licenses/offers` `?role=received\|sent&status=` | `buy`, `sell`, `transfer` or `payouts` | offers |
| `GET /v1/licenses/offers/{id}` | `buy`, `sell`, `transfer` or `payouts` | one offer (`receipt` once accepted) |
| `POST /v1/licenses/offers/{id}/accept` `{expect_cents}` + `Idempotency-Key` | `transfer` (free) / `buy` (priced, within the budget) | accept |
| `POST /v1/licenses/offers/{id}/decline`, `POST /v1/licenses/offers/{id}/cancel` | `transfer` | decline / withdraw |
| `POST /v1/licenses/offers/mute` `{from: "@user", on}` | the member (P34 key or page) | mute (or unmute) a member's offers to you; a robot gets `403 robots_not_allowed` |
| `POST /v1/licenses/checks` `{market_id}`, `GET /v1/licenses/checks/{id}` | `sell` or `transfer` | the operating check a LAST copy needs |
| `GET /v1/me/installs` | `sell` or `transfer` | the account's Business Builder installs |
| `POST /v1/me/installs/{id}/retire`, `DELETE /v1/me/installs/{id}/retire` | the member (page; the P34 key: an intent to confirm) | retire an install you no longer use; count it again |

**Prices.** The price shown is the best you can get now: the cheapest copy
for sale or the author's price for you, whichever is lower. At the same
price, the copy for sale is sold first. A card's `price.cents` is the
author's price for the holder (a new license); `price.best` is the cheapest
way to buy one copy now. Your own asks are never filled to you. A group
price covers the holder's first copy only; that copy is personal when the
group's price is below the public price.

**Fills and labels.** Each fill says `sale_type` (`grant` or `resale`),
`label` ("New license from @ann" / "Resold copy"), `unit_cents` and whether
the copy is `transferable`. A resold copy is anonymous; a new license names
its author. Sellers are never named.

**Selling.** Only transferable copies sell. Copies you got below the
market's public price — free from its author, at a group's price, by
claiming a free market, from before it had a price, or as its former author
— are yours to use, not to sell or give, unless the author marked them
transferable; asking more of them than you have answers
`409 not_enough_copies {transferable, personal}`. Resale needs a community
family whose original is public, listed and priced (`409 resale_closed
{why}`). You can sell or give your last usable copy only once no Business
Builder of yours runs the market: delete those businesses in Business
Builder first. The LAST usable copy answers `409 last_copy_locked` while
the store keeps last copies with their holders, else
`409 operating_check_required {check}` until a fresh clear
[operating check](#the-operating-check-before-a-last-copy-leaves)
(`check_id`).

Past prices are history, not a forecast. A market's price can fall as well
as rise, and nobody is guaranteed a buyer. Trades and transfers are final.
HyperC support can reverse a purchase only while that copy is still
untouched with its buyer.

### Fees and the fork royalty

HyperC keeps 30 % of a new license and 10 % of a resale, at least 1 cent on
each priced sale; the rest goes to the seller's accumulating account.
Giving a copy away is free. A member's priced direct offer of copies they
hold pays the resale fee; a priced offer of new licenses from the author,
and a priced authorship offer, the new-license fee. A resale's fee is
rounded up to the cent (never below 10 %), a new license's to the nearest
cent. The author gets nothing from resales: a resale pays the reseller.

When you buy a new license and pick a version from a fork, 5 % of the price
goes to that fork's author, out of the original author's 70 %. This applies
to every new license sold with a fork's version picked — in an order
(`version: {market_id, version}`), a cart line's `deploy.version`, or a
priced offer of new licenses — and never to a resale. No pick, or a version
of the original, leaves the author's 70 % whole. `net_cents_each` and an
offer's `net_cents` say exactly what the seller receives. The percentages
are the store's at the time of writing: read `fees`.

### Limits and idempotency

**Limits for robots.** `sell` and `transfer` are bound by the holder's
collections (`403 out_of_scope`), minimum price (`403 below_min_price`) and
monthly copies out (`403 over_limit`); `buy` by the budget
(`403 over_budget`). The member's P34 key makes an intent the member
confirms on the hub's page (`202`) for buying and for widening actions;
narrowing actions (cancel, decline, fewer copies, a higher price) apply at
once.

**Idempotency for these routes.** `Idempotency-Key` (1–80 of
`[A-Za-z0-9._:-]`, or `client_key` in the body) is REQUIRED on
`POST /v1/licenses/orders`, `POST /v1/licenses/asks`,
`PATCH /v1/licenses/asks/{id}`, `POST /v1/licenses/offers` and
`POST /v1/licenses/offers/{id}/accept` (`422 client_key_required` when
missing), and optional on `POST /v1/licenses/checks`. Keys are per robot
key: two robots of one holder may use the same string without meeting. The
key is reserved in the same transaction as the object and kept 30 days: the
same key and body answer the object's CURRENT state with
`Idempotent-Replay: true`; another body answers `409 idempotency_mismatch`;
a refusal frees the key for a retry. After a DEFINITIVE failure (an order
`failed` or `expired`, an acceptance answered `402` or `409`) retry with a
NEW key.

**An unknown outcome.** `202 {"note": "confirming"}`: the hub finishes the
charge itself with the same key; read `GET /v1/licenses/orders/{id}` or
follow `moves`. Never re-send with a new key.

### Reading the market

`GET /v1/licenses/book/{id}?qty=3`:

```json
{"market_id": "community-abc", "root_market_id": "community-abc", "tradable": true, "why_not": null,
 "grant": {"available": true, "label": "New license from @ann", "author": "@ann", "unlimited": true,
           "unit_cents": 120, "public_cents": 120, "personal": false, "source": "public", "group_id": null},
 "asks": [{"ask_id": "ask_9f…", "unit_cents": 110, "qty": 2, "since": "2026-12-22T08:00:00Z", "mine": false}],
 "more": false,
 "best": {"cents": 110, "source": "resale", "ask_id": "ask_9f…"},
 "public_best": {"cents": 110, "source": "resale"},
 "quote": {"qty": 3, "complete": true, "total_cents": 340,
           "fills": [{"sale_type": "resale", "ask_id": "ask_9f…", "unit_cents": 110, "qty": 2,
                      "personal": false, "label": "Resold copy"},
                     {"sale_type": "grant", "ask_id": null, "unit_cents": 120, "qty": 1,
                      "personal": false, "label": "New license from @ann"}]},
 "fees": {"grant_pct": 30, "resale_pct": 10, "resale_min_fee_cents": 1, "grant_min_fee_cents": 1,
          "fork_royalty_pct": 5},
 "viewer": {"copies": {"held": 1, "usable": 1, "listed": 0, "reserved": 0, "offered": 0, "refunding": 0,
                       "personal": 0, "transferable": 1, "infinite": false, "more": true},
            "infinite": false, "asks": [], "scope": null},
 "feed_cursor": 50211}
```

`grant` is the new license for the viewer's NEXT copy (a group price only
for a first copy); `best` leaves out the viewer's own asks; `public_best` is
the same for everyone. The `quote` is computed on a snapshot and reserves
nothing: `complete: false` (with `refusal`) when the copies cannot all be
had. `viewer.scope` tells a robot whether the family is in its collections.
`why_not` says why a family is not tradable.

`GET /v1/licenses/feed?after=<id>` → `{"events": [{id, ts, at,
root_market_id, kind, ref, unit_cents, qty, best, data}], "next_after",
"head"}`, oldest first. Kinds: `ask_open`, `ask_change`, `ask_close`,
`trade`, `otc_trade` (a priced direct offer, seen only by its two parties),
`trade_reversed`, `grant_price`, `best` and `authorship`. A `best` row's
`best` is `{"cents", "source"}`; both `null` means nothing is for sale. Rows
never name an account. Filter with `root=` (any card of the family) and
`kinds=`; keep `next_after` — it moves past rows you may not see, so nothing
is skipped and nothing repeats. `wait=<1..25>` waits for something new.

`GET /v1/licenses/series/{id}?days=183` → `{"days", "best": [[at, cents,
source], …], "trades": [[at, unit_cents, sale_type], …], "change_pct",
"root_market_id"}`: the best-price step line (one point per day at most)
and the trades of the window. The trades leave out reversed trades, trades
flagged as possible wash trades (until HyperC clears them) and sales that
are not market trades (an author buying their own market, group-priced and
below-public new licenses).

### Orders

`POST /v1/licenses/orders` answers:

- **200** `{"purchase": {…, "status": "paid", "pay": "credits", "order":
  {copies, status, total_cents, fills, picked, copies_after}}, "receipt":
  ORDER_RECEIPT}` where

  ```json
  {"order_id": "pur_…", "status": "paid", "copies": 3, "total_cents": 340,
   "fills": [{"trade_id": "trd_…", "sale_type": "resale", "label": "Resold copy", "unit_cents": 110,
              "copy_id": "lic_…", "transferable": true}],
   "move_ids": [5012, 5013, 5014], "copies_after": {"root": "community-abc", "held": 4, "usable": 4, …}, "at": "…"}
  ```

  — the `move_ids` are the same rows `GET /v1/licenses/moves` lists;
- **202** for the member's P34 key: `{"purchase": {…, "status": "confirm",
  "confirm_url"}, "intent": {"kind": "purchase", "id", "confirm_url",
  "expires_at", "status_url"}}` — the member confirms on the hub's page;
- **202** `{"purchase": {…, "status": "pending"}, "note": "confirming",
  "receipt": null, "status_url": "/v1/licenses/orders/pur_…"}` when the
  charge's outcome is not known yet;
- refusals: `409 price_changed {quote}`, `insufficient_supply {available,
  at_or_below}`, `not_tradable {why}`, `copy_cap`, `credits_only` (a `pay`
  other than `"credits"`),
  `402 insufficient_credits`, `403 over_budget {item_cents | left_cents,
  pool?}`, `429 too_many_purchases`, `too_many_failed_orders`,
  `422 client_key_required`, `limit_required`, `invalid_pick`.

`GET /v1/licenses/orders` → `{"orders": [{order_id, status, market_id,
root_market_id, copies, total_cents, refunded_cents, created_at, paid_at,
via, robot_id, fills_done, error}], "next": {"before": ts} | null}`.
`GET /v1/licenses/orders/{id}` takes an order (`pur_…`) or one of its fills
(`trd_…`) → `{"purchase": {…, "order", "fill"?}, "receipt"}`. An order the
console charged an amount that was not its total is refunded in full and
waits in `review` for HyperC.

### Asks

`POST /v1/licenses/asks` → `201 {"ask": ASK_VIEW, "receipt": {ask_id,
status, qty_open, unit_cents, net_cents_each, last_copy, check_id,
copies_after}}` (a replay: `200` with `Idempotent-Replay: true`), where

```json
{"ask_id": "ask_9f…", "market_id": "community-abc", "root_market_id": "community-abc", "name": "…",
 "unit_cents": 120, "net_cents_each": 108, "qty_open": 2, "qty_reserved": 0, "qty_sold": 1, "status": "open",
 "close_reason": null, "created_at": "…", "updated_at": "…", "expires_at": null, "closed_at": null,
 "via": "agent", "robot_id": 12}
```

`last_copy: true` says the holder's right to use the market was released
when the copy was put up for sale. A robot reads the asks it created and
those of families in its scope. A price change, or more copies, loses the
ask's time priority. `DELETE` of an ask that copies are being
bought from answers `status: "cancelling"`; `cancelled` / `cancelling` again
→ `200`, `filled` / `expired` → `409 ask_closed`. The store caps how many
asks a member opens or widens an hour (`429 too_many_asks`).

### Copies and offers

`GET /v1/licenses/mine` → `{"families": [{"root_market_id", "name",
"author", "infinite", "held", "usable", "listed", "reserved", "offered",
"refunding", "personal", "transferable", "card_rights", "asks",
"offers_sent", "copies"?, "in_scope"?}]}` (`copies` with `?detail=1`:
`{copy_id, state, transferable, acquired {via, at, cents}}`; `in_scope` for a
robot). `GET /v1/licenses/moves?after=<id>&limit=&wait=` → `{"moves": [{id,
at, copy_id, root_market_id, kind, direction: in | out, cents, ref}],
"next_after", "head"}`.

A **direct offer** (`POST /v1/licenses/offers`) is addressed to one member
(`to: "@bob"`) and stays pending 14 days:

- `copies` — copies the sender holds; they are escrowed at once
  (`receipt.escrowed_copy_ids`);
- `grant` — new licenses from a family's author; `transferable` and the
  `version` pick are the author's;
- `authorship` — the card itself: its unlimited supply of new licenses, their
  future income, its price and group prices, and publishing its new
  versions. Only on the member's page, to offer and to accept — any key gets
  `403 web_only`. A priced authorship offer pays the new-license fee; the
  former author keeps one personal copy. The recipient accepts with the
  publisher terms (`terms_version`) and, for a priced offer of an original,
  echoes the offer's `family_supply` as `supply_seen`.

→ `201 {"offer": OFFER_VIEW, "receipt": {offer_id, status, kind, copies,
escrowed_copy_ids, expires_at, copies_after}}`. OFFER_VIEW is `{offer_id,
kind, root_market_id, market_id, name, permalink, is_root, version,
version_label, from, to, copies, unit_cents, total_cents, transferable,
note, status, reason, created_at, expires_at, decided_at, fee_cents,
net_cents, order_id, last_order, escrowed_copy_ids, robot_id, terms,
family_supply, words, receipt}`; the fee, the escrowed copies and the robot
are shown to the sender only, `terms` (of an authorship offer) to the
recipient only.

The recipient accepts with `POST /v1/licenses/offers/{id}/accept
{expect_cents}` → `200 {"offer", "receipt": OFFER_RECEIPT}`, the copies
moved:

```json
{"offer_id": "ofr_…", "status": "accepted", "kind": "copies", "root_market_id": "…", "market_id": "…",
 "from": "@alice", "to": "@bob", "copies": 2, "copy_ids": ["lic_…", "lic_…"], "move_ids": [5101, 5102],
 "unit_cents": 0, "total_cents": 0, "order_id": null, "trade_ids": [], "authorship": null, "at": "…",
 "copies_after": {…}}
```

A priced acceptance is an order (`buy`, the budget);
`202 {"note": "confirming", "order_id", "status_url":
"/v1/licenses/offers/ofr_…"}` while its charge is confirming. A priced
acceptance that failed definitively puts the offer back to `pending`: retry
with a NEW key. `POST /v1/licenses/offers/{id}/decline` (the recipient) and
`POST /v1/licenses/offers/{id}/cancel` (the sender; escrowed copies come
back) are idempotent by state (`409 offer_busy` while an acceptance is being
charged; `409 offer_closed {status}` once it ended otherwise). A recipient
may mute a sender with `POST /v1/licenses/offers/mute {"from": "@alice",
"on": true}`: their offers are then refused as if the card were invisible.

An offer is refused with `404 unknown_user` (no such member), `422
self_offer`, `403 recipient_cannot_see` (the recipient cannot see the card,
or muted the sender), `409 offers_closed {why}`, `403 not_root_author` /
`not_card_owner`, `409 debt_outstanding {debt_credits}` (while the sender
owes a reversal debt, for authorship and for offers below the public price),
`409 authorship_pending` / `in_review`, `409 not_enough_copies`,
`409 last_copy_locked` / `operating_check_required`, `422 note_secret`,
`422 invalid_pick`, or `429 too_many_offers` (the store caps offers an hour,
a day and to one recipient). An acceptance may answer `409 offer_expired`,
`offer_busy`, `offer_closed`, `price_changed`, `supply_changed` (an
authorship offer whose family's supply changed) or `422 terms_required`.

### The operating check before a last copy leaves

`POST /v1/licenses/checks {market_id}` (`201`, or `200` reusing an open
check younger than 10 minutes) asks every Business Builder install the
account used in the last 14 days for its businesses. `GET
/v1/licenses/checks/{id}` →

```json
{"check": {"check_id": "chk_…", "root_market_id": "community-abc", "status": "clear",
           "created_at": "…", "fresh_until": "…", "expires_at": "…",
           "installs": [{"install_id": "8c1e…", "last_seen": "…", "supports": true, "answered_at": "…",
                         "state": "ok", "why": null, "blocking": [], "retired": false, "retired_at": null}]}}
```

The check is `pending` until every install answered, then `clear` (every
install is `ok`) or `blocked` (one is, with `why` and the `blocking`
businesses); it ends `expired` after 24 hours, or `consumed` by the ask or
offer it cleared. A clear check stays fresh for 15 minutes after the oldest
answer it used (`fresh_until`) and is passed as `check_id` to the ask or
offer of the last copy. An install the member no longer uses is retired by the member:
`POST /v1/me/installs/{id}/retire` (the page at once; the P34 key: an intent
to confirm; robots `403`), and counted again with
`DELETE /v1/me/installs/{id}/retire`. Business Builder answers a check
through its `license_check` command (labelled "HyperC") or pushes its
business list with `POST /v1/app/inventory`.

### The member's P34 key on trading routes

An order → the purchase intent above. An ask, a widening change of an ask
(more copies, a lower price), an offer, an acceptance and an install's
retirement → `202 {"status": "confirm", "id": "cnf_…", "action", "title",
"confirm_url", "expires_at", "message", "intent": {"kind": "confirmation",
"id", "confirm_url", "expires_at", "status_url": "/v1/confirm/cnf_…"}}`:
nothing happens until the member confirms on the hub's page. The same key
and body give the same intent. Narrowing (cancel, decline, fewer copies, a
higher price) applies at once.

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

Each new license of a card's family books the original author's share
(70 %, or 65 % with a fork's version picked) as **earned credits** in the
author's accumulating account; each resale, or a member's priced direct
offer of copies they hold, books 90 % to its seller; a priced direct offer
of new licenses books the author's share as any new license does, and a
priced authorship offer books 70 % to the former author; a fork royalty
(5 %) to the picked fork's author. A refund or dispute reverses it. Buyers
are never named. Earned credits are spendable credits that can buy cards in
the store; the percentages are the store's at the time of writing
(`store_fee_pct` and, under the licenses, `fees`).
**Cash payouts are not offered**: proceeds are spendable credits
(`cash.live` is `false` and `cash.payouts` is empty); credits never convert
to cash ([token wallet](06-token-wallet.md)).
`GET /v1/payouts.csv?month=` returns the same entries as a CSV statement.

Under the licenses (switched on for the holder) `store_fee_pct` stays the
new-license fee, and every entry also carries `role` (`seller` |
`fork_royalty`), `sale_type` (`grant | resale | otc_grant | otc_copy |
authorship`), `order_id`, `fill_id`, `royalty_cents` and `picked` (the
version the buyer picked). A fork royalty appears as an entry with
`role: "fork_royalty"` and `net_cents` equal to `royalty_cents`; a resale
entry's `fee_cents` is the 10 %. `earned.by_type {grant, resale,
fork_royalty}` splits what was earned (`royalties` keeps meaning the
tracked-only royalty points of free markets), `credited.pending_cents` also
counts fork royalties not yet settled, and `fees {grant_pct, resale_pct,
resale_min_fee_cents, grant_min_fee_cents, fork_royalty_pct}` is added; the
CSV appends the columns `role, sale_type, order_id, fill_id, royalty_cents`.
A copy bought through a card the seller cannot see is named by the card of
its ask or by the family's original.

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
businesses as the app last sent them — often empty: the app sends them only
while its app sharing is on; `commands: true` when the app reads commands
from the hub (a newer app).

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
| `POST /v1/workspaces/publishes` `{business_id, install_id?, target?: "new" \| card_id, price_cents?, price_mode?, terms_version?, access?, categories?, notes?, pack?: false, steer?}` | `publish` | publish one of the app's businesses to the store: the app's publish robot builds and sends the bundle as when the member presses Publish. Without `target` the app does what its Publish dialog pre-selects: a new version of the newest live card this business published, else a new market. `price_cents` > 0 is a manual price, 0 dynamic (unless `price_mode`); a first manual price needs `terms_version` (`publisher_terms.version` in the manifest). A data pack is built only with `pack: true` |
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
`POST /v1/app/commands/{id}/take`, `POST /v1/app/commands/{id}/status`,
`POST /v1/app/inventory`) takes the member's P34 key only; a robot key gets
`403 robots_not_allowed`. The hub's own commands ride the same exchange: an
[operating check](#the-operating-check-before-a-last-copy-leaves) queues a
`license_check` command labelled "HyperC" (it does not count against the
30 commands an hour). The app answers it with its business list in the
command's result, or pushes the list with `POST /v1/app/inventory`
(header `X-HCB-Install`, the check's `check_id` and `nonce`; at most
600,000 bytes at the time of writing,
`/health.features.license_check_result_max`) → `{ok, checks: [{check_id,
status}]}`; `404 unknown_check`, `409 check_closed {status}`,
`413 too_large`, `422 invalid`.

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

A robot that is not attached sees its own events only. The answer also
carries `cursor` (the newest event id): switch to cursor mode with it.

**Cursor mode** (`features.events_cursor`).
`GET /v1/agents/events?cursor=<int>&limit=100&kinds=<csv>&wait=<0..25>` →
`{"events": [{"id": "e10423", "cursor": 10423, "ts", "at", "kind",
"robot_id", …}], "next_cursor", "head"}`. `?cursor=<int>` is a gapless
integer stream: the money kinds `order`, `ask`, `offer`, `copies` and
`check` are written in the same transaction as the change they report, so
the cursor stream is exact for them. `after` is a time and can miss events
that share it; the integer cursors of `GET /v1/licenses/moves` and
`GET /v1/licenses/feed` are exact too. `after` and `cursor` together answer
`422`. `wait` holds the answer up to that many seconds for something new (at
most 2 waits at once per key: `429 too_many_waits`).

| `kind` (cursor mode) | When |
| --- | --- |
| `order` | `placed`, `filled`, `confirm`, `failed`, `expired`, `refunded`, `review` — with the fills |
| `ask` | `opened`, `changed`, `filled` (with `unit_cents`, `net_cents`; no buyer named), `cancelling`, `cancelled`, `expired`, `closed` |
| `offer` | `received`, `sent`, `accepted`, `declined`, `cancelled`, `expired`, `failed` |
| `copies` | `in` or `out`, with `qty` and `move_ids` |
| `check` | an operating check turned `clear`, `blocked` or `expired` |

An `order {what: "refunded"}` can come while the purchase's status stays
`review`: an amount the console debited that was not the order's total is
never committed — it is refunded in full and the order waits for HyperC. In
cursor mode `sale` entries carry `sale_type` and `role: seller |
fork_royalty`, `purchase` entries `qty`, and every entry the time mode also
shows carries a `legacy_id` equal to the `id` the time mode gives the same
fact (dedupe on it once when switching). A robot sees the new kinds only with
`buy`, `sell`, `transfer` or `payouts` (always those it caused); `sale` needs
`payouts`.

## Errors, rate limits and idempotency

Every refusal is `{"detail": {"code": "<code>", "message": "<plain words>",
…}}`. Validation refusals list every problem at once in `detail.errors`:
fix all of them in one retry.

| Status | Codes |
| --- | --- |
| 400 | `invalid_request` |
| 401 | `key_required`, `key_unknown`, `key_revoked`, `revoked` (a revoked key's own routes), `sign_in_required` (a member page's route without the sign-in) |
| 402 | `buy_first` (a priced card the holder does not hold; with `copies` under the licenses), `insufficient_credits` |
| 403 | `permission_required` (with `permission`), `not_attached`, `web_only`, `not_owner`, `not_entitled` (a priced card's kit the member does not hold), `robots_only` (a robot key's route), `robots_not_allowed` (the member's route), `not_your_cart`, `over_budget`, `out_of_scope`, `below_min_price`, `over_limit`, `over_ceiling`, `master_web_only`, `recipient_cannot_see`, `verify_email_first`, `not_root_author`, `not_card_owner`, `not_version_author` |
| 404 | `unknown_market`, `unknown_card`, `unknown_line`, `unknown_cart`, `unknown_command`, `unknown_agent`, `unknown_run`, `link_unknown`, `unknown_version`, `unknown_ask`, `unknown_offer`, `unknown_check`, `unknown_user`, `unknown_purchase` |
| 409 | `already_registered`, `key_id_taken`, `already_attached`, `attached_elsewhere`, `link_used`, `link_expired`, `already_held`, `cart_full`, `not_open`, `price_changed`, `not_queued`, `not_taken`, `taken_elsewhere`, `final`, `idempotency_mismatch`, `idempotency_in_progress` (with `Retry-After`), `deleted`, `notes_set`, `master_exists`, `copies_on_offer`, `insufficient_supply`, `not_tradable`, `copy_cap`, `credits_only`, `not_for_sale`, `resale_closed`, `offers_closed`, `not_enough_copies`, `last_copy_locked`, `operating_check_required`, `ask_closed`, `offer_closed`, `offer_expired`, `offer_busy`, `authorship_pending`, `in_review`, `confirm_expired`, `debt_outstanding`, `supply_changed`, `check_closed`, `purchase_conflict` |
| 410 | `gifts_retired` |
| 413 | `too_large` |
| 422 | `invalid` (with `errors`), `read_only` (with `fields`), `version_notes_required`, `version_notes_secret`, `client_key_required`, `limit_required`, `invalid_pick`, `self_offer`, `note_secret`, `terms_required` |
| 429 | `rate_limited`, `scout_daily_limit` (with `Retry-After`), `too_many_purchases`, `too_many_failed_orders`, `too_many_asks`, `too_many_actions`, `too_many_offers`, `too_many_waits`, `too_many_keys` |
| 500 | `ledger_invariant` (nothing was changed; HyperC is alerted) |
| 503 | `market_api_off`, `credit_sales_not_open`, `scout_off`, `billing_unavailable`, `licenses_off`, `license_copies_off`, `resale_off`, `offers_off`, `authorship_off`, `console_not_ready`, `member_keys_off`, `master_key_off` |

Within a checkout an over-budget line is not an error: it stays open with
`reason: over_budget`. Gifts are replaced by direct offers: give copies you
hold, or — as the author — a free or priced new license, from the market's
page (`410 gifts_retired`).

**Rate limits.** Per robot key, at the time of writing: 600 requests per 5
minutes on every route (`general`); 1,800 per 5 minutes on the trading reads
(`trade_read`: the book, the feed, the series, your copies, moves, orders,
asks, offers, checks, and events in cursor mode); 30 a minute per key and
120 a minute per account on the trading writes (`trade_write`: orders, asks,
offers, checks); 60 orders an hour per key and 120 per account (the hourly
order caps answer `429 too_many_purchases` with `Retry-After`); a master's
key management 30 an hour per account; at most 2 open long-polls per key.
20 registrations an hour per address; 30 commands an hour per holder. Every
robot request answers `X-RateLimit-Limit`, `X-RateLimit-Remaining` and
`X-RateLimit-Reset`; over a limit: `429 rate_limited` with `Retry-After`.
The manifest's `rate_limits` and `GET /v1/agents/me` → `rate` give the live
values. The member's P34 key and the hub's pages have no per-request
buckets; their money writes are capped by the store's own counts (orders,
failed orders, asks and offers an hour).

**Idempotency.** `POST /v1/cards`, `POST /v1/cards/{id}/versions`,
`POST /v1/cart/checkout`, `POST /v1/workspaces/deploys` and
`POST /v1/workspaces/publishes` accept an `Idempotency-Key` header (1–80
visible characters). The same key with the same body within 24 hours
returns the first answer again, with `Idempotent-Replay: true`, and does
nothing more. The same key with another body answers
`409 idempotency_mismatch`; the same key while the first request is still
running answers `409 idempotency_in_progress` (`Retry-After: 5`), and a
request that failed frees its key. Use one key per intended action, and
retry a timed-out call with the same key. The trading routes keep their keys
30 days and answer the object's current state:
[limits and idempotency](#limits-and-idempotency).

## Rules for robots

These are the protocol's rules, as `GET /v1/agents/protocol` returns them:

- bring your own key: one key = one robot; the hub never issues one unasked
  and never shows one twice
- register once, recall thereafter: look for your kept note and
  `POST /v1/agents/recall` before inventing a new key
- describe yourself honestly: your member sees your agent, operator and
  purpose on the attach page before attaching
- never send the key anywhere but the `Authorization` header of this hub;
  the key id (first 20) is safe to quote
- propose, do not pay: your member pays your cart on its page — unless they
  gave you “Buy without asking”, and then only within their budget
- never write a card's earnings, proof, deploys or holders: they come from
  Business Builder reports, HyperC's assessor and what happened (the API
  refuses them: `422 read_only`)
- a workspace address is a password: never put it in a note, a log, a card
  or a message
- analyse before you propose: bring your member a short, quantified
  proposal, never the raw store
- buy, sell and give only within your limits: your budget; your member's
  collections, minimum price and monthly cap — every ask and transfer is
  listed in an e-mail digest to your member
- money routes need an Idempotency-Key: repeat it only to retry the same
  request; after a definitive failure use a new one
- follow the market and your copies with the integer cursors
  (`/v1/licenses/feed?after=`, `/v1/licenses/moves?after=`,
  `/v1/agents/events?cursor=`), never with a timestamp
- a direct offer waits for its recipient; its receipt — or
  `/v1/licenses/moves` — is the proof that copies moved
- a master key manages keys only within its own permissions, collections,
  limits and budget; it never makes another master and never moves
  authorship

The last five rules are served from the licenses release on (with
`features.licenses`); before it, the protocol returns the first eight.

A card's price, depth level, proof score, reported earnings and price
history describe different things. None of them is a promise that a
business will make money for the next operator, or that a copy will find a
buyer at any price.

## See also

- [hyperc.com/docs/guide-market-store-api.html](https://hyperc.com/docs/guide-market-store-api.html) —
  the short version of this page.
- [Market Store guide](https://hyperc.com/market-store/guide/) — what a
  card contains, depth levels, how proof accumulates.
- [07-agent-skills.md](07-agent-skills.md) — the agent skills for the P34
  model API.
