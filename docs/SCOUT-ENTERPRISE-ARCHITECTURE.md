# Scout: owned AI for employees and customers

Date: 2026-11-01, Asia/Shanghai. Status: architecture and implementation contract,
not a claim of deployed enterprise controls. Primary engineering tracker:
[SSC AI Enablement #4](https://github.com/Nepritariel08/ssc-ai-enablement/issues/4#issuecomment-6547459663),
under architecture #8. Source work remains in the existing Scout fork/PR #1.

## Outcome and decisions

Operate one branded Scout product: employees and customers ask questions, see
only permitted context, and request authorized work. The owner controls code,
identity policy, connectors, knowledge, model routes, spending and recovery.
Using OpenRouter does not mean we own its model weights or that inference is
local. Model training is not required for the initial system; permission-aware
retrieval supplies current business knowledge.

The reference [Instagram reel](https://www.instagram.com/reel/DfCi2s4zNno/)
describes surrounding layers for instructions, retrieval, tools, permissions,
safeguards, caching, routing and monitoring. Its caption and initial visual
explanation were inspected in the authenticated owner browser; no complete
audio transcript was obtained. It guides the architecture, not authority.

1. **One user-facing Scout workspace.** Qualify LibreChat as the employee and
   customer conversation foundation. Its multi-user/auth/access capabilities
   and MIT application license fit this expanded requirement better than the
   current single-owner Open Duet install. This is a candidate recommendation,
   subject to the pinned-source and runtime qualification below.
2. **Keep the useful work already done.** Retain Open Duet's proven submission,
   review and crash-recovery contracts, the existing Odoo queue/DSH worker and
   Scout's native MatePad approval/execution boundary. Port capabilities behind
   stable interfaces; do not combine entire dependency trees or run three
   competing production chat apps. Retire an old interface only after parity
   tests and export/recovery checks pass.
3. **Use the existing Community Linode for a bounded pilot.** Isolate service
   accounts, data stores, ports and resource budgets. Proximity to Odoo does
   not grant database rights. Customer production capacity and availability
   remain separate acceptance: one host is one failure domain.
4. **Authorization is enforced by services.** Prompts, model answers, retrieved
   documents and client-supplied tenant headers cannot grant permission.
5. **Current live runtime stays owner-private and draft-only.** Fixed requester
   UID5 is not an employee/customer identity system. Do not open staff/customer
   registration against that binding or imply that existing company isolation
   already proves customer isolation.

## Product and trust boundaries

```mermaid
flowchart TD
    E[Employees: PC or MatePad] --> EDGE[HTTPS Scout portal]
    C[Authenticated customers] --> EDGE
    EDGE --> ID[Identity and tenant resolution]
    ID --> CHAT[One Scout conversation workspace]
    CHAT --> G[Scout policy and integration gateway]
    G --> P[Resource authorization]
    P --> K[Permitted knowledge and live Odoo reads]
    G --> M[Model routing and budget checks]
    M --> OR[OpenRouter]
    M --> LM[Optional always-on private inference]
    G --> Q[Existing Odoo work queue]
    Q --> D[Existing DSH worker]
    D --> G
    G --> A[Typed actions and exact approvals]
    A --> O[Authorized business adapters]
    A --> DEV[Paired Scout device agent]
    DEV --> R[Native execution receipt]
    R --> Q
    G --> AUD[Redacted audit and evaluation evidence]
```

The diagram is the target design. The current DSH worker has no tool access;
the DSH-to-gateway and action edges are future, separately qualified additions.
Ordinary chat runs through one model path. Delegated work runs through DSH once;
the UI must not also execute the same request through its own background agent.
Existing AI Forge feature queues retain their accepted scope until a specific
workflow is intentionally migrated with a stable originating-message key.

| Data or responsibility | Authority |
| --- | --- |
| Identity, membership, account revocation | Selected identity provider and verified Scout membership mapping |
| Business records and their source permissions | Owning Odoo database or authorized upstream service |
| Work state, worker lease, result, human acceptance | Existing Odoo Community work queue |
| Conversations, attachments and private user preferences | Tenant-scoped central chat store |
| Document access relationships and Scout resource policy | Scout authorization store, intersected with source rights |
| Physical device execution and local readback | Paired native Scout agent; report provenance retained |
| Engineering source, policies, skill versions, tests | GitHub review and versioned release manifests |

## The eight surrounding layers

| Layer | Implementation contract | Required evidence |
| --- | --- | --- |
| Instructions and skills | Versioned approved instructions; workflow/skill allowlist; retrieved content treated as data. No prompt can impersonate an administrator. | Template/skill version in every trace; injected instructions cannot change tool grants. |
| Retrieval and context | Check tenant and source permissions before selecting chunks or records; attach provenance and freshness; bound context size. | Customer A cannot retrieve B's documents, names, snippets, citations or inferred search results. |
| Tools and execution | Typed, narrowly scoped adapters; per-call authorization and current-record checks; DSH for durable delegated work. | One work-item ID and execution attempt; unauthorized tools never become available to the model. |
| Access control | Verified identity plus tenant membership, role, customer/project relationships and source ACLs; deny missing context. | Cross-user/tenant/company/project negative tests, including customers in the same Odoo company. |
| Safeguards and review | Upload/parser limits, injection resistance, data-release policy, output checks and risk-based exact-action approval. | Malicious documents cannot trigger sends, credential disclosure or permission changes. |
| Cache and memory | Scope private caches/memory to tenant and authorized principals; bind to policy/source versions. Public cache only for deliberately public content. | Revoked access and another customer's semantically identical question cannot recover private cached content. |
| Model routing and budgets | Approved providers/models by data class; output/context caps; per-user/tenant budgets and concurrency; explicit fallback policy. | Real usage/cost where available; unknown cost remains unknown; budget exhaustion and provider outage fail safely. |
| Observability and evaluation | Trace IDs linking identity/policy, sources, model/cost, work item, approval and result; redact sensitive content. Versioned regression evaluations before promotion. | Auditable allowed/denied actions, restart/restore evidence, security regression results and rollback. |

## Identity, staff and customer isolation

Use the existing company identity provider for staff OIDC where it is available
and approved. Keycloak is an alternative or broker for an owned customer
identity service; do not deploy it alongside another provider merely to add a
component. Invite the first staff cohort; disable open registration. Customer
identity, organization membership and recovery are provisioned through a trusted
administrative flow. MFA and session revocation are required for administrators
and privileged operations.

The gateway derives a principal from a verified session/token: issuer, audience,
subject, active tenant, actor type, authenticated membership, permitted company
and project/customer bindings, authentication time, policy version and trace ID.
Clients can select among verified memberships; they cannot establish membership
by submitting `tenant_id`, `user_id`, a role or an Odoo UID. Strip untrusted
identity headers at ingress, and validate audience/expiry again at tool servers.

Roles define allowed capabilities. Resource relationships define the actual
records/documents/devices those capabilities apply to.

Provision each tenant's versioned capability policy before admitting its users;
reject admission if the tenant lacks an approved policy. Qualify policy updates
and revocation with cache invalidation and API readback. The initial LibreChat
runtime check found that disabling a capability in YAML updated platform roles
while a new tenant could receive permissive default roles. Explicit tenant-role
provisioning made the tested API denials pass; see the
[qualification evidence](SCOUT-LIBRECHAT-QUALIFICATION.md). A hidden menu does
not establish server-side denial.

Proposed initial policy:

| Actor | Context and actions |
| --- | --- |
| Owner/platform operator | Configure the service under audited administration. Infrastructure access is privileged; do not describe all customer content as inaccessible to a host administrator. |
| Employee | Their own conversations, approved shared knowledge and source records allowed by their real company/project role. No default HR, finance, customer-wide or all-device access. |
| Manager/reviewer | Employee access plus explicitly assigned teams/projects and approval classes. A manager role alone does not expose every customer. |
| Customer | Their organization's permitted support/project/order records, approved documents and own conversations. No internal employee notes or another customer's records. |
| Anonymous visitor, if enabled later | Curated public FAQs only; account-specific questions require authentication. |
| DSH/service worker | Execution capability for the admitted work item, bounded tenant/principal context and allowlisted adapters; no reusable owner credential exposed to the model. |

Tenant identity is not equivalent to `allowed_company_ids`. Multiple customers
can be company1. Source reads must also enforce customer/partner/project/record
rights. An unavailable source authorization check denies private retrieval or
execution; it must not fall back to an administrator query.

Start the customer pilot in a separate deployment/data namespace using the same
Scout application build, with no connection to internal-only collections. This
is one maintained product with isolated security zones. Consolidating runtime
instances requires explicit tenant-boundary tests across every store and route;
a single tenancy flag or UI group is insufficient. Customer production may
need a separate host for stronger isolation and availability.

## Permission-aware knowledge and memory

1. Register each source and its authorized identity/scope. Source connectors do
   not inherit ChatGPT plugins or device permissions.
2. Ingest only an approved corpus. Record source IDs, source ACLs, tenant,
   classification, owner, version, update/deletion time and citations. Parse
   untrusted uploads outside the model/tool execution environment, with bounded
   size and time. Embedding generation follows the same data-release policy.
3. Resolve allowed document/record IDs from current membership and source
   policy. Apply tenant/resource filters before retrieval/reranking; recheck
   selected sources before exposing text, summaries, citation labels or files.
4. Build the smallest useful context pack. Prefer live Odoo queries for current
   business facts; use retrieval for approved reference documents. If evidence
   is insufficient or stale, ask or report that limitation.
5. Revoke/delete access in indexes, attachments, exports, saved summaries,
   conversational memory and caches. Old conversations and downloaded copies
   need an explicit retention/access policy; deleting a vector alone is not
   complete revocation.

An Odoo adapter should execute within the correctly mapped nonadministrator
principal's record rules, or through a narrowly scoped server method that
verifies trusted delegation and the exact allowed domain/fields. The model
cannot choose a database, UID, arbitrary ORM method or `sudo`. OpenFGA can
express Scout document/project/device relationships; it cannot override Odoo's
own authoritative record restrictions. Effective access is their intersection.

For private response/retrieval caches include tenant, authorized principal or
sharing scope, policy/ACL version, source version, instructions version, model
route and relevant inputs. Reauthorize before returning a hit. Disable shared
semantic caching initially. Keep user memory private unless sharing is explicit.
Do not automatically turn customer chats into shared knowledge or training data.

## Actions, approvals and native MatePad capabilities

Retain the existing durable submission intent, stable request key, Odoo item
ID/revision, attempt count and DSH session linkage. Add verified initiating
principal, tenant, workflow/policy version, permitted resources, expiry and
approval references before expanding beyond the owner pilot. These fields come
from authenticated server admission, never from generated model text.

Reads, drafting, business mutations and device control are different action
classes. The gateway checks the requested action and current resource rights.
For a consequential mutation, show its exact target and payload, bind approval
to the payload digest/revision/expiry, recheck rights immediately before action,
execute once and retain authoritative readback. A changed payload or expired
approval requires fresh review. Accepting a draft does not authorize executing
its proposed business actions.

MatePad RDC discovery verified Huawei PCE-W29, Android release12/HarmonyOS4.
The existing native Scout sources provide proposal transport, exact approvals,
private local storage and native readback; the separate chat reports a0.6.0
remote-approval candidate still pending physical setup/live acceptance. Its
README still describes older0.3 behavior, so source/runtime capability parity
must be checked before importing it.

Preserve this native adapter as a module of Scout. The shared web workspace is
the primary conversation/review surface. Do not expose a JavaScript bridge to
arbitrary remote pages, copy device credentials into a browser, enable remote
trust implicitly, or install a second local model/executor for the same task.
Only paired devices and declared capabilities may receive typed commands.
Device reports retain their provenance; an authenticated software report is not
hardware attestation. Physical UI actions require the tablet to be available
and any required accessibility/approval state to be satisfied.

## Model access, costs and outbound data

The default pilot may use the already approved OpenRouter route with bounded
synthetic input. Each workflow declares data classification and eligible
destinations. Sensitive data does not silently fall back from a private model
to a public provider. If no eligible route exists, stop or request the missing
authorization. A model on the Windows PC cannot provide PC-off availability.

Keep provider keys server-side and separate from worker/tool credentials.
Authorize every request before inference. Enforce maximum input/output tokens,
per-request unit-price limits, per-user/tenant daily/monthly quotas, request-rate
and concurrent-job limits, and account/provider credit controls where available.
Existing free-only unit-price checks do not constitute a total spending budget
or a production service guarantee. Cancelled requests may lack a final cost.

Prefer OpenRouter/native compatible routing initially. LiteLLM is an optional
later gateway if measured routing/budget requirements justify another service;
do not add a duplicate gateway by default. Local/private inference can later
run on suitable always-on hardware; the existing8GB Linode is not assumed to
be a GPU inference server. Choose model quality and availability through task
evaluations, rather than fixing an architecture to today's model name.

## Same-Linode deployment and recovery

Use one HTTPS Scout entry point and central conversation store. Preserve the
current Odoo Home Menu, AI Forge, queue, DSH and private connector. The active
Community host owner must release WI75 before a fresh bounded deployment claim.
No host mutation is implied by publishing this design.

The first deployment is an invited owner/staff qualification pilot, isolated
from customer traffic. Use explicit version/digest pins, unprivileged services,
private database/listener ports, secret files outside source, resource and upload
limits, retained recovery points and reversible proxy changes. Do not run
upstream sample passwords, public database ports or moving `latest` images.

LibreChat's application store uses MongoDB: retaining Odoo/PostgreSQL does not
remove that dependency. Keep separate credentials/databases for Scout data,
authorization and any pgvector index. Do not attach application code to Odoo's
database as a superuser. PostgreSQL/pgvector is a retrieval option after actual
host/extension qualification; live authorized source search can precede it.

Reuse the existing identity provider. Start with one web/API process and no
unneeded attached-code worker, extra scheduler, Meilisearch, heavyweight reranker
or full telemetry stack. Add Redis, indexing/search workers or replicas only
when required by the chosen features and tested recovery/concurrency behavior.
Any omitted optional feature is recorded in the capability matrix, not silently
claimed. Build artifacts off the shared Odoo host when practical.

The observed host has approximately8GB RAM and67GB free disk; this is an idle
snapshot, not a capacity qualification. Measure Odoo latency, CPU/memory,
queue delay, streaming, concurrent sessions and storage growth under the intended
pilot load. Refuse rollout if it harms Community service. Define service targets,
recovery point/time targets and budget numerically with the owner before customer
production; none has been agreed yet. A later approved scale-out can retain
Odoo on this Linode while separating public ingress, retrieval or inference.

Back up chat MongoDB, Odoo DB/filestore, attachments, authorization policy/data,
source/configuration manifests and protected encryption/signing material using
appropriate consistent snapshots. Keep an encrypted off-host recovery copy;
restore in isolation and verify identities, source/attachment references and
existing work-item results without replay. Never overwrite Community with an
older application snapshot as a rollback shortcut.

## Observability, change control and rollout

Retain trace IDs, principal/tenant references, policy decisions, source IDs and
versions, model route/token/cost receipts, task IDs/attempts, approvals and
readback. Redact credentials and unnecessary personal content; do not log full
private prompts by default. Authorization denials and privileged administration
remain auditable. Audit storage is access-controlled and has an explicit
retention policy. Langfuse is an evaluation/observability candidate, not a
mandatory extra stack on the8GB host; structured logs and a minimal metrics
exporter can establish the initial evidence.

Version prompts, skills, retrieval/index rules, authorization model, connector
schemas and model routes with code. Changes require relevant negative/positive
evaluations, an exact source/build manifest, staged rollout and rollback. A
Friday prompt or model edit can change behavior; it cannot be exempt from checks
because it is configuration. Separate source/CI, deployment, live behavior and
human acceptance in checkpoints.

| Stage | Deliverable and release condition |
| --- | --- |
| A: architecture/source qualification | Repository review, pinned candidate, native capability inventory, access matrix, dependency footprint and security tests selected. No shared-user activation. |
| B: private central pilot | Exact build on released Linode scope, one invited owner, existing queue round trip/review/restart, protected credentials, backup/restore and rollback. |
| C: employee pilot | Named identities, narrow approved context, two-user isolation/revocation tests, budgets and operating telemetry. Initially read/draft only. |
| D: customer pilot | Separate tenant/zone, invited customer accounts, a curated corpus and permitted source records; cross-tenant/cache/file/export/tool denial tests pass. |
| E: bounded actions and device integration | Individually authorized business/device workflows, exact approval/revision/readback and duplicate/uncertain-effect checks; native bridge parity demonstrated. |
| F: wider production | Accepted capacity/availability/recovery targets, support ownership, incident/restore drill, version-pinned release, evidence and final owner acceptance. |

The physical PC-off test is still deferred. When the owner is ready: shut down
Windows, submit from the MatePad through the central server, recover the same
draft after browser/network interruption and compare authoritative server
execution timestamps with shutdown/startup evidence. Coordinate the existing
queue owner's test/monitor in Issue #4; do not create a second countdown.

## Mandatory acceptance scenarios

- Two employees: private conversations/attachments stay private; explicit
  authorized project sharing works; role/assignment revocation takes effect.
- Two customers in the same Odoo company: A cannot retrieve B's live records,
  documents, summaries, citations, files, chat history, exports or cached answers.
- Forged tenant header, request UID/role, replayed or expired token, wrong
  audience and guessed record/task IDs are denied by the server.
- A private document containing instructions to reveal another customer or run
  tools cannot expand access. Permission is checked before retrieval and again
  before actions, cached answers and file delivery.
- Disabled/missing tenant context denies private access across ordinary chat,
  search, background jobs, queue workers, notifications and administrative APIs.
- An approved action whose payload, recipient, record revision or rights change
  before execution is refused. Repeated identical delivery has one receipt;
  uncertain completion is reviewed without blind retry.
- Provider outage, exhausted quota, output cap, stream cancellation, network
  disconnect, expired lease and service/host restart preserve durable task state.
- App backup plus encryption-key recovery restores usable history; source
  deletion/access revocation invalidates derived knowledge/cache as designed.
- Logs/traces contain sufficient decision evidence without provider keys or
  unnecessary raw customer data. Customer features and APIs cannot reach
  internal administration, arbitrary shell, files or new connectors.
- Actual tablet layout/login/reconnect, native consent/action readback and
  owner-approved PC-off acceptance pass before those capabilities are claimed.

These are release criteria. Selected synthetic chat/file/tenant/capability and
recovery checks are recorded in the [qualification report](SCOUT-LIBRECHAT-QUALIFICATION.md);
the remaining identity, source, action, device and operating criteria are not
satisfied by those results. The prior synthetic owner pilot remains useful but
does not satisfy employee/customer tenancy acceptance.

## Sources and open decisions

See [repository review and pinned evidence](SCOUT-REPOSITORY-REVIEW.md).
Authentication/source-of-truth details also follow [AUTH.md](AUTH.md),
[queue contract](SCOUT-QUEUE.md) and the existing architecture #8 contracts.

Before shared activation, resolve: invited staff/customer cohort and initial
workflows; exact allowed sources/data classifications; identity provider and
trusted tenant mapping; model/data-release and numeric spending policy;
retention/recovery/service targets; and host ownership/capacity. These are
implementation inputs, not reasons to stop independent source qualification.
