# 7. Agent skills and per-runtime notes

## The four API skills

[`skills/`](../skills/) holds four skills for any agent that calls this API,
listed in the order a request passes through them. They carry the judgement
this documentation cannot state as a field rule, and they link back here for
every table rather than copying one.

1. [p34-prepare-inputs](../skills/p34-prepare-inputs/SKILL.md) — map the
   caller's recorded history and current option schedule into the Menus and
   Sales tables with the record intact, and enumerate every executable T=0
   quantity. Long form:
   [references/history-contract.md](../skills/p34-prepare-inputs/references/history-contract.md).
2. [p34-business-economics](../skills/p34-business-economics/SKILL.md) —
   collect the caller's actual fees, costs, lead times and horizons, compute
   the values their records support, and write the `business_description`
   around them.
3. [p34-submit-and-monitor](../skills/p34-submit-and-monitor/SKILL.md) — run
   the client-side checks, test inputs, submit a separate actual fit, and follow the `session_id`
   through the documented statuses.
4. [p34-interpret-results](../skills/p34-interpret-results/SKILL.md) — turn a
   `done` result into executable orders and refusals, and state how far the
   predicted profit can be trusted.

### Grounding choice for agents

Use the default `business_led` mode. Do not recommend, implement or submit
client-side grounding before consultation with HyperC and agreement on an
enterprise integration. Correct grounding requires vast compute resources;
this mode is reserved for preserving enterprise private knowledge and know-how.
Having profit labels or encountering a grounding failure is not a reason to
switch modes. See the
[enterprise reference](02-endpoints.md#bringing-your-own-labels-client_grounded).

### Installing them

The repository is laid out as a portable
[Agent Plugins](https://agent-plugins.org/) package: a `plugin.json` at the
root and one `skills/<skill-name>/SKILL.md` per skill, with a skill's own
files beside it. A client that reads that layout can load the four straight
from a checkout.

- **Pin a commit.** The skills and the documentation anchors they link to move
  together; skills from one revision against docs from another will link into
  headings that have moved.
- **Native discovery differs per agent, and is not verified here.** Search
  paths, manifests and install commands belong to each client. What is tested
  is the content of the skills, by injecting them into an agent's context —
  which says nothing about whether a given product auto-discovers them. If
  yours has no plugin mechanism, point it at the four `SKILL.md` paths or copy
  `skills/` where it already looks.
- **Nothing else is required.** No workspace VM, no membership and no bundle:
  the four skills work from this repository and the caller's own records and
  API key. The runtime notes below are about narrow *channels*, not about
  these skills — a shell-less agent still uses the same four.

---

## Notes for specific agent runtimes

P34 is driven by agents, and agents differ in what they can *do* rather than in
what they understand. A coding agent with a shell, a hosted assistant with only
a web-fetch tool, and a workflow engine that can POST all reach the same API and
the same [membership workspace](../README.md#access--membership) — but the
narrow ones meet limits that have nothing to do with P34 and are easy to
misread as an outage.

The rest of this page collects those runtime-specific notes. Everything below
is about the **channel**: the API contract itself is in
[docs/02-endpoints.md](02-endpoints.md), and the data rules in
[docs/03-data-format.md](03-data-format.md).

> Members' workspace VMs ship this same guidance on the machine, at
> `/workspace/URL_ONLY_AGENTS.md`, and the workspace's own `/agents` page
> carries the wider fetch-only manual — response caching, writing files through
> a GET, and chunked transfers.

---

## ChatGPT and other hosted agents: driving the workspace from a URL bar

**Applies to:** any agent whose only tool is a web fetch or a browser — a
ChatGPT agent, a hosted assistant inside a corporate sandbox, any environment
where the workspace is reachable as a URL and there is no terminal.

One rule carries most of the value:

> **Keep every `/run/` URL under 4,000 characters, total.** Put the long thing
> in a file, then run the file with a short command.

### HyperC HTTP shell: 502 errors from long `/run/` URLs

Date tested: **2026-09-04 UTC**

#### Summary

The HyperC workspace can be healthy while a long URL-encoded shell command
returns `502 Bad Gateway`. In the tested workspace route, the failure depended
on the total browser-visible URL length:

- **4,711 characters:** succeeded (`Command exit 0`)
- **4,712 characters:** failed (`502 Bad Gateway`)
- Longer probes at 4,800, 5,000, 6,000, 7,000, 8,000, and 12,000 characters
  also failed.

Treat **4,711 as an observed boundary, not a guaranteed platform contract**.
Proxy configuration, encoding, HTTP version, routing, or future backend changes
may alter it. Use a conservative operational ceiling of **4,000 total URL
characters**.

#### Test method

The test used harmless commands of the form:

```text
<workspace-access-url>/run/true%20%23AAAA...
```

The `#` was percent-encoded, so the appended characters became a shell comment.
This varied the request-URL length without performing work or producing
meaningful output. The measurement was the final URL length reported by the
browser after navigation.

Observed results:

| Total URL length | Result |
| --- | --- |
| 1,000 | Success |
| 2,000 | Success |
| 4,000 | Success |
| 4,700 | Success |
| 4,710 | Success |
| 4,711 | Success |
| 4,712 | 502 |
| 4,800+ | 502 |

#### Diagnosis procedure

When a `/run/<encoded-command>` request returns 502:

1. Open the workspace base URL. If it loads, the workspace gateway is
   reachable.
2. Run the short health check `<workspace-access-url>/run/pwd`.
3. If `pwd` succeeds but the original command returns 502, measure the **fully
   encoded, complete URL**, including scheme, hostname, access path, `/run/`,
   and encoded command.
4. If it approaches 4,000 characters, treat URL length as the likely cause.
5. If even the base URL or `/run/pwd` fails, investigate workspace/origin
   availability instead; that is a different failure mode.

#### Required workaround

Do not place long shell programs, embedded Python, heredocs, JSON, or large
argument lists directly in `/run/<encoded-command>`.

Instead:

1. Keep each `/run/` command short — preferably below 4,000 total URL
   characters.
2. Put complex logic in a script inside the workspace.
3. Invoke it with a short command such as:

```text
cd /workspace/project && python3 status_check.py
```

4. For long-running jobs, launch the existing script with `nohup`, redirect
   output to a log, and use a separate short `tail` command for status.
5. Split setup, launch, and inspection into multiple short requests rather than
   one large compound request.

#### Security note

The workspace access URL and P34 API key are secrets. Never include either in
logs, memos, user-facing reports, or copied diagnostics. Use placeholders such
as `<workspace-access-url>` and read the API key from the configured
environment or secret file.

#### Reproduction-run context

This issue was found while checking a P34 `rc012` reproduction. A 500-character
launch URL and a 402-character polling-launch URL both succeeded. The fresh
calculation was accepted with HTTP 200 and entered `business_led` grounding
through `claude_code_live`. The URL-length 502 was therefore independent of P34
model execution.

### Where the ceiling actually lives

A `502 Bad Gateway` is written by a **proxy**, not by the shell: on a 502 the
workspace never saw the request at all. The gateway on the VM accepts a request
line up to 64 KB, and a 3,000-character command has been recorded arriving
intact. So the boundary measured above belongs to something in front of the
workspace — or to the agent's own fetch layer, which is usually the tighter of
the two.

Two consequences:

- **The number is per route, and per harness.** A ceiling measured through one
  access URL, from one agent environment, does not transfer. Measure yours once
  at the start rather than designing around a number somebody else observed.
- **Getting a shorter URL through proves nothing about the long one.** Cached
  fetches make this worse: vary an `&n=<anything>` parameter on every check so
  the fetch layer cannot replay an earlier answer.

If there is any way out of the URL channel — a code-execution tool, an MCP
server, a browser that can POST, or an SSH key the member authorises for the
workspace account — take it. Every limit on this page disappears at once, and
none of them is a boundary anyone intended.
