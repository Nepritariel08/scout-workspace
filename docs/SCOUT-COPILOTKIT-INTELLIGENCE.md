# Scout CopilotKit/OpenDuet pivot and owned Intelligence

Status: design and migration contract; not deployed or accepted in production.

Upstream source pin: [CopilotKit/OpenDuet](https://github.com/CopilotKit/OpenDuet/tree/f52288fff5ccdbd3de428d573d9f026fce5ff480), MIT.
Primary tracker: [SSC AI Enablement #4](https://github.com/Nepritariel08/ssc-ai-enablement/issues/4#issuecomment-6547459663).

## Decision

Use CopilotKit/OpenDuet as the mobile-first product foundation. This supersedes
the earlier Anil-matcha/open-duet and LibreChat foundation choices. Preserve the
existing Scout queue adapter, task cards, OpenRouter limits, DSH/Odoo receipts,
and MatePad approval boundary as migration donors. Retire an old interface only
after equivalent behavior and recovery are demonstrated.

For Scout-owned Intelligence, do not emulate an undocumented CopilotKit API.
Use CopilotKit's open AG-UI protocol and Runtime where useful, while owning the
conversation store, authorization, memory policy, and thread UI in Scout.
OpenDuet's current Rich Threads path depends on CopilotKit Intelligence; a
third-party thread store is not a drop-in backend for that feature.

## Service boundaries

| Responsibility | System of record / owner |
| --- | --- |
| Verified identity, tenant membership, role, revocation | SSC identity provider and Scout policy service |
| Conversation threads, message events, replay cursor, user memory | Scout Intelligence PostgreSQL service |
| Active streaming and notifications | Redis/pub-sub; never the durable record |
| Attachments | Encrypted object storage with tenant-scoped authorization |
| Work item, lease, attempt, result and human acceptance | Existing Odoo Community queue |
| Draft/analysis execution | Existing DSH worker through that queue |
| Model inference | Server-side model router; OpenRouter only for approved data classes |
| Device action and local execution receipt | Paired Scout device controller and existing approval boundary |

## What Scout Intelligence must provide

- Authenticated APIs to create, list, rename, archive, delete and resume a user's
  permitted threads. Derive tenant and principal from verified server identity.
- Append-only, tenant-scoped AG-UI event history for messages, state, tool
  cards, approvals and final receipts. Support replay after refresh and a lost
  phone connection. Do not persist model chain-of-thought.
- User-controlled memory records with owner, tenant, provenance, consent,
  source version, retention and delete/export behavior. Do not turn chat text
  into global memory automatically.
- Permission-filtered retrieval before prompt construction, with source IDs and
  freshness available for citations. Re-check authorization at action time.
- Per-tenant model allowlists, context/output budgets, concurrency caps and
  fail-closed provider routing. Never send restricted context through an
  unapproved OpenRouter route or fallback.
- Redacted audit events that link principal, policy version, thread, source
  references, model route, work-item ID, approval and receipt.

PostgreSQL is the durable conversation and memory store; Odoo remains the
durable work queue. Redis is only a delivery/cache aid. Store conversation rows
with tenant/principal keys and enforce authorization in the API and database.
A client-provided tenant, role, company or Odoo user ID never establishes access.

## DSH and OpenRouter

DSH remains the queue worker for durable, asynchronous draft/analysis jobs. It
does not replace thread storage, user identity, cross-device replay or memory.
A delegated Scout turn creates one Odoo work item with a stable request key,
thread/turn reference, narrow context grant and a bounded task kind. DSH runs
once under its worker binding and returns a draft. Scout shows the draft and
queue receipt for human review. Business actions remain disabled unless a later
separately authorized adapter and exact approval are added.

Interactive chat and delegated work must not execute the same request twice.
Do not add an OpenDuet routine or second scheduler over jobs already owned by
Odoo/DSH. Keep OpenRouter credentials server-side, apply the current price and
output limits, and record provider-reported cost when available.


## Verified OpenDuet source seams

- The server configuration currently declares only an Intelligence runtime mode and requires its API URL, WebSocket URL and project key at boot.
- The Copilot runtime assembly says there is no SSE-only branch and wraps built-in agents in Intelligence-aware thread handling.
- The authenticated thread-status route asks CopilotKit whether a remembered thread exists; the local app database does not currently replace that history/replay contract.
- User memory already has a local-store fallback when Intelligence is unavailable. Reuse its owner scoping and graceful failure pattern, but do not mistake it for durable thread/event storage.
- The first owned-service change should replace the boot capability model and thread APIs/UI with a tested Scout event store. Do not impersonate the private CopilotKit client or point it at an undocumented endpoint.

