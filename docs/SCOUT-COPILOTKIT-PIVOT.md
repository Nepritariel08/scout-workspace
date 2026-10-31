# CopilotKit OpenDuet: active Scout direction

The owner's 2026-11-01 instruction selects **CopilotKit/OpenDuet** and supersedes
the Anil-matcha interface and LibreChat recommendation. This is integrated into
the existing owned-AI goal and [primary checkpoint](https://github.com/Nepritariel08/ssc-ai-enablement/issues/4#issuecomment-6547459663),
not a new project or a reset of employee/customer security requirements.

## Source and ownership

- Owned fork: [Nepritariel08/scout-copilot](https://github.com/Nepritariel08/scout-copilot).
  Parent verified CopilotKit/OpenDuet; MIT retained; default main.
- Reviewed upstream pin: `f52288fff5ccdbd3de428d573d9f026fce5ff480`.
  Scout branch: `scout/integration-20261101`.
- Source owner: Codex `01a19336-83fb-7ab0-9829-6fc1c290c93f`, confined to this
  fork and the existing Scout PR1 architecture/reference files. The other
  Open Duet Integration Plan chat reported no source/device mutations and
  correctly left integration ownership with this lane.
- This repository/PR1 preserves the old adapter and accepted pilot receipts.
  LibreChat's fork/qualification and unfinished local admission research are
  historical only; no second chat product was deployed.

## What carries over

| Requirement/capability | CopilotKit integration |
| --- | --- |
| One Scout product | Brand through `openbot/examples/scout`, copied from the OpenDuet tenant package. Keep embedded OpenBot platform fixes upstream-compatible. |
| Queue and DSH | Port durable intent/idempotency, task ID/revision, review/acceptance, cancel and recovery to the existing executable queue contract. No second worker/scheduler for its work. |
| Employees/customers | Verified session to active tenant/source permissions and a server-held per-user Odoo requester reference. No shared UID5 binding, model-supplied authority or prompt-only controls. |
| OpenRouter/local models | OpenAI-compatible endpoint plus namespaced tool-capable model. Qualify output caps, all auxiliary calls, data release, budgets, outage and usage receipts; the old pilot's limits are not inherited. |
| MatePad/phone | One web/mobile surface plus the existing narrow native consent/execution adapter. Remote origin receives no trusted JavaScript bridge. Fresh WI182/device ownership and real login/reconnect/receipt evidence before replacement/install. |
| Context, cache and actions | Preserve every layer and negative test in the enterprise architecture; a copied personal package and channel group `all` are not customer isolation. |

## Dependency that must be resolved

The pinned server requires Intelligence API, WebSocket and project key for
durable threads. Local memory-table fallback does not remove this requirement.
An owned MIT interface is therefore not yet a fully local production stack.

Official [local Intelligence evaluation](https://docs.copilotkit.ai/intelligence/self-hosting-local)
is currently for macOS/Docker Desktop, requires at least12 GiB Docker RAM and
uses a renewable evaluation license. It does not fit the existing8GB Linux
Community host. Production self-hosting has separate entitlement; managed
Intelligence would store approved conversation data outside Linode. Resolve
that deployment/data/license choice before business data. A replacement local
thread adapter is separate engineering, not a configuration switch or license
bypass. No account, paid commitment or hosted project has been created here.

OpenDuet's current README has no published OpenDuet-specific deploy image/guide;
plain OpenBot images do not establish equivalence. Pin and build the actual
owned source. Keep same-Linode preference for the measured Scout pilot, separate
PostgreSQL/pgvector database/user and private services; preserve Community and
never give a Bot the shared host shell or Odoo superuser credentials.

## Immediate acceptance sequence

1. Validate the Scout package with upstream loaders and focused model/auth/
   policy checks. Review persistence, identity and dependency footprint.
2. Port the existing queue contract behind verified identity; test denied and
   revoked access, recovery without replay and one reviewed synthetic result.
3. After fresh host/device ownership reconciliation, run a private central
   pilot and mobile login/reconnect/native parity; expand to employees/customers
   only after the access matrix and capacity/restore criteria pass.

Source/fork/configuration is distinct from tested integration, deployment,
live inference, device installation and owner acceptance. PC-off remains
deferred/unarmed; no new timer or duplicate queue monitor is created.

Primary references: [CopilotKit OpenDuet source](https://github.com/CopilotKit/OpenDuet/tree/f52288fff5ccdbd3de428d573d9f026fce5ff480),
[pinned configuration](https://github.com/CopilotKit/OpenDuet/blob/f52288fff5ccdbd3de428d573d9f026fce5ff480/openbot/docs/configuration.md),
[Intelligence production self-hosting](https://docs.copilotkit.ai/intelligence/self-hosting),
and the [owner's CopilotKit video](https://www.youtube.com/watch?v=v8avTs34rDU).
The video page was identified; no complete audio transcript was obtained.
