# Scout Workspace: source adoption

Date: 2026-11-01 (Asia/Shanghai)

Engineering tracker: [SSC AI Enablement #4](https://github.com/Nepritariel08/ssc-ai-enablement/issues/4), under [architecture #8](https://github.com/Nepritariel08/ssc-ai-enablement/issues/8).

## Decision and scope

Use Open Duet as the preferred source foundation for an independently maintained Scout workspace. This is a source selection and local fork preparation; the Scout integration has not been implemented or activated.

- Upstream: https://github.com/Anil-matcha/open-duet
- Reviewed revision: `87d71d7055ddd79d5db6f43f4cd56a7c9873c6dd`
- Local branch: `scout/bootstrap-20261101`
- Remote: `upstream`; no SSC publication remote has been configured.
- License: Apache-2.0. Preserve the upstream license, attribution, and applicable notices when adapting or distributing the code.
- Owner: Codex, current OpenDots assessment/adoption session. This checkout is independent of the active DSH/Community queue source lane and the Community migration host owner.

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

## Validation receipt

Upstream exact-main [CI run 41067147210](https://github.com/Anil-matcha/open-duet/actions/runs/41067147210) passed backend tests on PostgreSQL and SQLite, Linux sandbox enforcement, real-process backend smoke, server smoke, and desktop Node tests. Frontend, mobile and isolated Chromium jobs were skipped by that run's path filters; it does not establish fresh coverage for those jobs.

Local baseline: Windows, Node.js `v24.19.0`, unchanged upstream application code.

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

## Next implementation slice

1. Implement the Scout execution adapter against the existing queue contract in coordination with its owner, with task IDs, cancellation, terminal results and receipts; preserve the initial draft-only scope.
2. Qualify the chosen OpenRouter/local route with a bounded model request, then streaming, cancellation, cost reporting and any separately authorized tool/approval flow.
3. Verify service restart, expired claims, uncertain completion without duplicate execution, requester isolation and a task completed while the Windows client is off before replacing an existing workflow.

The existing Community host owner must release the shared deployment target before host work. This source preparation makes no host, connector, access, schedule or business-state change.
