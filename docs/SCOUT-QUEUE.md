# Scout queue integration

The `scout_queue` engine submits draft-analysis work through the existing
requester MCP connector. Odoo owns the work item; the separately installed DSH
worker owns execution. The workspace keeps conversation receipts and review
controls. It starts no worker, scheduler, tools or business actions.

## Operator binding

Use the connector contract from [queue PR #88](https://github.com/Nepritariel08/ssc-ai-enablement/pull/88),
reviewed at `dba1dab16dcaa32c03984229c628cd866e02e712`. Install its Python
environment separately. The command is restricted to an absolute Python path
and `-m scout_queue.mcp_server`. Arbitrary command arguments, environment
variables and caller-selected Odoo endpoints are refused.

Copy [the example](../deploy/scout-queue.example.json) **outside the source
tree**. Replace every example binding with verified operator values. Point
`SCOUT_QUEUE_CONFIG_FILE` at that absolute JSON path. Give the service account
exclusive access to the config and requester key files (0600 on Linux;
equivalent Windows ACLs). Only the key-file path belongs in the JSON.

`owner_id` is the authenticated workspace owner, `local-owner` on the
single-owner self-hosted server. It is distinct from the verified Odoo UID.
Another application account cannot borrow this binding. Multi-account
deployment needs separately provisioned bindings; this initial engine does
not provide that provisioning. Give each independent workspace database a
unique, stable `client_id`. Preserve it across restarts; never run independent
copies of the database under the same client ID.

The connector must expose exactly these six tools: `scout_queue_status`,
`scout_list_work`, `scout_get_work`, `scout_submit_work`, `scout_accept_draft`
and `scout_cancel_work`. Every operation verifies database, UID, companies,
requester role, draft task kind and disabled business actions. Changes fail
closed. HTTPS is required except for local loopback development.

## Conversation behavior

1. Choose **Scout · DSH queue** as the conversation's engine and send a task.
   Agent instructions, prior plain-text conversation and the enriched current
   prompt must fit 8,000 characters; oversized context is refused intact.
2. A durable submission intent is saved before the submit RPC. The original
   client/thread/turn request key and exact payload remain the recovery source.
   The task card follows its Odoo ID and revision, then shows the returned draft.
3. **Accept draft** accepts only a nonempty returned draft at the reviewed
   revision. It does not authorize downstream business actions. **Cancel task**
   requests Odoo cancellation at the displayed revision. Conflicts require a
   refresh. Repeating an acknowledged acceptance performs a readback.

After a lost submit response or backend restart, **Recover submission** replays
only the stored payload and original idempotency key. It does not construct a
new task. Recovery is refused while the original turn is running. A changed
binding cannot recover the old request. Queue failures are shown without raw
remote errors, credentials or arbitrary caller-selected work-item IDs.

**Stop** is an explicit cancellation request. Backend shutdown or lease loss
detaches the conversation and leaves remote work alone. A wait timeout also
leaves it running; use **Refresh status** to retrieve the existing receipt.
An uncertain/expired worker lease remains a review matter under the queue
contract; this application never automatically re-executes it.

The action endpoint is `POST /api/v1/threads/{thread_id}/scout/{turn_id}` and
accepts only `action` and optional `revision`. Existing authentication, owner,
local-access and CSRF checks apply. It remains admin-scoped under the default
authentication allowlist.

## Inference qualification

The native **OpenRouter** engine is separate from queued DSH execution. Enter
its key in **Settings → Engines**, in the masked field. The engine configuration
is encrypted at rest; use a persistent protected encryption key, never the
throwaway test key. The local **OpenAI-compatible** engine keeps a separate
endpoint and credential. Neither chat engine advertises tool/computer access.

Both chat routes send `max_tokens` (default 1,024, configurable 1–32,768), also
for background calls. OpenRouter additionally sends a provider price ceiling
for prompt and completion tokens, excludes per-request fees, requires parameter
support and disables provider fallbacks. The price default is **0**, permitting
free providers only. Use a free model such as `openrouter/free` for initial
qualification and 64 output tokens. A paid route needs an explicit nonzero
price ceiling. This is a provider **unit-price** limit, not an account budget;
set an OpenRouter API-key credit limit for a cumulative spending ceiling.

Reported `usage.cost` is retained as `cost_usd` alongside token counts. Missing
cost remains unknown, including when cancellation prevents a final usage
receipt. A locally cancelled stream does not prove provider-side billing ended.
The queue worker's inference configuration is separate and must be qualified
with its owner; workspace chat settings are not copied into it.

Provider references: [routing price filters](https://openrouter.ai/docs/guides/routing/provider-selection#max-price)
and [usage accounting](https://openrouter.ai/docs/cookbook/administration/usage-accounting).

## Acceptance evidence

Fixture tests establish MCP protocol handling, committed conversation receipts,
recovery after constructing a new runtime, identity isolation, revision checks
and cancellation semantics. They do **not** establish live Odoo/DSH execution.
Track live task IDs, deployed source versions, provider/model/usage receipts,
restart and duplicate checks, and actual PC-off completion separately in
[the primary outcome tracker](https://github.com/Nepritariel08/ssc-ai-enablement/issues/4).
Shared-host deployment requires the Community migration owner's verified
release of the server scope.
