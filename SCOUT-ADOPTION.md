# Scout Workspace: source adoption

Date: 2026-11-01 (Asia/Shanghai)

Engineering tracker: [SSC AI Enablement #4](https://github.com/Nepritariel08/ssc-ai-enablement/issues/4), under [architecture #8](https://github.com/Nepritariel08/ssc-ai-enablement/issues/8).

Source bootstrap: [Scout Workspace PR #1](https://github.com/Nepritariel08/scout-workspace/pull/1). The fork's existing Actions workflows are enabled; its PR checks provide the current fork-head status separately from the upstream evidence below.

## Decision and scope

Use Open Duet as the source foundation for an independently maintained Scout workspace. The owner authorized the GitHub fork and source bootstrap on 2026-11-01. The source now includes a requester-only Scout execution adapter and conversation review controls. Live queue integration and activation remain unverified.

- Scout fork: https://github.com/Nepritariel08/scout-workspace
- Upstream: https://github.com/Anil-matcha/open-duet
- Initial reviewed and locally tested revision: `87d71d7055ddd79d5db6f43f4cd56a7c9873c6dd`
- Published fork base: `94c48383fce62f02759b4bb52eb5677ddff978d4`. Its seven subsequent commits change only frontend files; the Scout bootstrap branch is rebased onto this current fork main.
- Local branch: `scout/bootstrap-20261101`
- Remotes: `origin` is the Scout fork; `upstream` retains the original source. Upstream pushes are disabled in this checkout.
- License: Apache-2.0. Preserve the upstream license, attribution, and applicable notices when adapting or distributing the code.
- Owner: Codex, chat `01a19336-83fb-7ab0-9829-6fc1c290c93f`. This checkout is independent of the active DSH/Community queue source lane and the Community migration host owner.

## Candidates compared

| Candidate | Source evidence | Fit for Scout |
| --- | --- | --- |
| [Open Duet](https://github.com/Anil-matcha/open-duet/tree/87d71d7055ddd79d5db6f43f4cd56a7c9873c6dd) | Durable conversation events, approvals, encrypted engine configuration, process recovery, SQLite/PostgreSQL, engine adapters, and current passing backend/sandbox/process CI | Preferred workspace foundation. API engines currently provide chat only; a DSH/queue adapter is required for Scout execution. |
| [CopilotKit/OpenDots](https://github.com/CopilotKit/OpenDots/tree/8091324942b86789ed0da7facbee855145d933b0) | Exact-main CI passed; OpenAI-compatible Chat Completions adapter with tools, MCP approvals, pages, and OpenBot computers | Good UI/tool template, but conversations require CopilotKit Intelligence. Supported production self-hosting requires its self-hosted plan; local evaluation is licensed, time limited, and supported on macOS. Replacing that dependency is additional engineering. |
| [Shashankss1205/OpenDots](https://github.com/Shashankss1205/OpenDots/tree/de37e7445418ace9862daf33b7ac7014064790de) | Exact-main CI passed; Linux runtime, persistent goals/events, approval policy, compatible API and Ollama providers | Useful runtime reference, but a smaller prototype and another executor/scheduler alongside the existing DSH pilot. Its compatible API requires the selected model to support the configured structured-output dialect. |

This comparison supports a preferred starting point, not a general claim of production reliability. Test-file counts, stars, and activity alone do not establish correctness.

## Proposed Scout integration

```text
Scout browser / desktop interface
              |
              v
Open Duet workspace and conversation history
              |
       Scout execution adapter
              |
Shared MCP / Odoo Community work queue
              |
      Leased DSH worker ---> local inference / OpenRouter API
              |
              +---> authorized MCP / action adapters (future scope)
```

Open Duet may retain its application conversation database. Odoo remains authoritative for the pilot's work state, execution claims, acceptance and receipts. GitHub remains authoritative for source, skills and architecture. Link records by durable IDs; do not introduce another work queue for the same jobs.

Keep one executor and scheduler for each job. Do not activate Open Duet routines or team dispatch for work already owned by the DSH/Odoo queue. The current DSH pilot is draft-only and has no worker tools; adopting this interface does not expand that scope.

Open Duet's native `openrouter` engine points at `https://openrouter.ai/api/v1`. Its current capability contract exposes no tools, approvals, MCP, images or computers. Direct OpenRouter chat can be used independently, but tool-capable Scout execution needs a separate engine/queue adapter and verified provider configuration. See upstream [engine capabilities](https://github.com/Anil-matcha/open-duet/blob/87d71d7055ddd79d5db6f43f4cd56a7c9873c6dd/docs/ENGINES.md).

Self-hosted state does not make OpenRouter inference local: authorized prompt context sent to that route reaches OpenRouter and its selected provider. Local inference remains a separate route. Existing ChatGPT connector authorizations do not transfer to this application.

## Bootstrap validation receipt

Upstream exact-main [CI run 41067147210](https://github.com/Anil-matcha/open-duet/actions/runs/41067147210) passed backend tests on PostgreSQL and SQLite, Linux sandbox enforcement, real-process backend smoke, server smoke, and desktop Node tests. Frontend, mobile and isolated Chromium jobs were skipped by that run's path filters; it does not establish fresh coverage for those jobs.

The newer fork base `94c48383fce62f02759b4bb52eb5677ddff978d4` passed upstream [CI run 41230380223](https://github.com/Anil-matcha/open-duet/actions/runs/41230380223): frontend lint/build, server smoke and desktop Node tests. Backend, sandbox, mobile and isolated Chromium jobs were skipped by its path filters. These two runs establish different evidence; neither is represented as a full fresh run of every job.

Initial local baseline: Windows, Node.js `v24.19.0`, unchanged upstream application code at the initial reviewed revision. The desktop and build-script files are unchanged by the seven newer frontend commits. These historical results precede the implementation below.

| Check | Result |
| --- | --- |
| `node --test --test-reporter=spec scripts/build-ui.test.js` | PASS: 11 passed, 0 failed, 0 skipped. These are build-script fixtures, not a frontend production build. |
| `cd desktop; node --test --test-reporter=spec 'test/*.test.js'` | FAIL: 125 tests, 117 passed, 4 failed, 4 skipped. |
| Backend tests on this PC | NOT RUN: upstream requires Python 3.14+, while the discovered installed interpreters are 3.11 and 3.12. |
| Live OpenRouter inference, tool use and model quality | NOT RUN. No provider credential was read, configured or used. |
| Scout adapter, queue integration, deployed service and laptop-off acceptance | NOT IMPLEMENTED / NOT RUN. |

Windows failure details:

- `desktop/test/doctor.test.js`: two cross-platform CLI-discovery fixture assertions failed at lines 59 and 96. The fixtures select Darwin behavior while operating on this Windows filesystem; further qualification is required.
- `desktop/test/native-control.test.js:49`: symlink creation failed with `EPERM` on this Windows host.
- `desktop/test/smoke-packaged.test.js:8`: the Darwin executable assertion expects POSIX separators, while the returned path uses Windows separators.

The four failures remain visible. No test was weakened or marked passing. Desktop installation and Windows production use remain unqualified.

## Adapter implementation

The `scout_queue` engine now verifies the fixed requester MCP binding, persists
an exact submission intent before the RPC, and follows the Odoo work-item ID
and revision. A task card in the originating conversation supports refresh,
idempotent submission recovery, explicit draft acceptance and cancellation.
An application owner cannot borrow another owner's Odoo binding. Explicit Stop
requests cancellation; backend detachment preserves remote work for recovery.
No worker or business-action capability was added to this workspace.

Native chat routes now send an output-token cap. OpenRouter also applies an
explicit provider unit-price ceiling (default free-only), excludes per-request
fees, disables provider fallback and retains reported cost with token usage.
These controls also apply to the native background text path. They do not
configure DSH's separate model profile or impose a cumulative account budget.

See [operator setup, recovery and inference qualification](docs/SCOUT-QUEUE.md).
Local qualification uses an isolated Python 3.14.7 environment and an SSD
checkout; the Google Drive checkout remains the bootstrap snapshot. No
production credentials or production database are used in tests.

Local adapter checkpoint (2026-11-01): 91 focused backend tests passed across
the Scout queue, engine registry, compatible chat/OpenRouter engines and
conversation runtime; all 298 frontend tests passed. Frontend production and
static-export builds passed. ESLint had zero errors and four warnings in
unchanged components. Full backend/OS qualification is provided separately by
the fork's exact-head PR checks. No live provider or Odoo/DSH receipt exists at
this source checkpoint.

## Remaining live acceptance

The first useful outcome is one draft task submitted from the Scout workspace, executed once through the Odoo/DSH queue, and returned to the same conversation with its Odoo work-item ID and review state. The requester can then accept the draft. External business actions are outside this first slice.

The queue source contract is in [SSC AI Enablement PR #88](https://github.com/Nepritariel08/ssc-ai-enablement/pull/88), reviewed for planning at `dba1dab16dcaa32c03984229c628cd866e02e712`. Its exact-head connector and clean Community CI passed. It remains a draft source PR; this is not a deployment claim. Reconcile its current reviewed head with its owner before implementing the adapter.

1. Connect the prepared Scout adapter to an approved live requester binding and verify one queue task, its returned draft and explicit acceptance in the same conversation.
2. Qualify the chosen OpenRouter/local route with a bounded model request, then streaming, cancellation, cost reporting and any separately authorized tool/approval flow.
3. Verify service restart, expired claims, uncertain completion without duplicate execution, requester isolation and a task completed while the Windows client is off before replacing an existing workflow.

The existing Community host owner must release the shared deployment target before host work. This source preparation makes no host, connector, access, schedule or business-state change.
