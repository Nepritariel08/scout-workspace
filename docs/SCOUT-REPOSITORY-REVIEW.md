# Enterprise AI foundation review

Reviewed 2026-11-01. Primary sources below. This is a suitability and source
review, not a penetration test or a general production-reliability ranking.
GitHub stars/test-file counts do not establish security. No new platform,
customer account or public endpoint was deployed during this review.

## Recommendation

Qualify **LibreChat** as Scout's employee/customer conversation foundation.
Retain the existing DSH/Odoo queue and port the useful Open Duet review/recovery
contract; retain native Scout device actions behind their separate authorization
boundary. Use one product and pinned upstream components, with small Scout
adapters rather than maintaining several full chat forks. Existing Open Duet
owner-pilot evidence remains valid for its tested scope.

Source fork [Nepritariel08/scout-platform](https://github.com/Nepritariel08/scout-platform)
now exists with its upstream MIT attribution retained. The selected release pin
is available there; its default branch is not an approved production build.
The existing Scout/Open Duet fork remains the contract/reference pilot during
integration; no second public chat app has been activated.

The initial Open Duet selection addressed a personal workspace/queue pilot.
Employee/customer access materially expands that requirement. Building a full
multi-user/tenant system inside its single-owner server is a larger maintenance
commitment than qualifying a foundation that already contains those controls.

## Compared repositories

| Candidate | Relevant strengths | Material qualification or licensing boundary | Decision |
| --- | --- | --- | --- |
| [LibreChat](https://github.com/LibreChat-AI/LibreChat) | Multi-user authentication, OIDC, resource/feature permissions, MCP, compatible model endpoints, persistent/multi-device conversations. | Application code MIT with notices retained; dependency terms still apply. Current docs are latest/dev. Latest inspected release entries are marked prerelease; source presence is not live isolation proof. Adds MongoDB; native DSH/Scout integration still required. | Leading candidate for employee/customer qualification. |
| [Open WebUI](https://github.com/open-webui/open-webui) | Self-hosted local/API model chat, knowledge, roles/groups/resource permissions. | Current license restricts altering branding beyond50 end users in a rolling30-day window unless an exception/permission/license applies. Its additive UI/resource grants do not replace external record authorization. | Good alternative, less suitable for an independently branded product growing across customers without resolving those terms. |
| [Dify](https://github.com/langgenius/dify) | Workflow/application builder and knowledge integration. | Modified Apache terms require authorization for multi-tenant environments and restrict frontend branding changes. Do not assume a rebranded customer platform is covered. | Reference/optional licensed workflow component; not the default Scout foundation. |
| [Onyx](https://github.com/onyx-dot-app/onyx) | Enterprise search/chat and connector-oriented knowledge retrieval. | MIT portions plus separately licensed `ee` directories; exact required permission-sync/SSO features and operating footprint need edition/source qualification. | Retrieval-focused alternative if its connectors justify it; do not add a second chat portal in the initial stack. |
| [Open Duet](https://github.com/Anil-matcha/open-duet) / current Scout fork | Proven owner pilot with durable task intent, originating-conversation review, explicit acceptance and crash recovery. | Self-hosted authentication explicitly has one owner; paired devices are not separate employee accounts. Current Scout engine has one requester binding. | Preserve tested capabilities; do not expose the current binding to staff/customers. |

License observations describe the retrieved files, not a substitute for a
dependency/edition/branding review before distribution or customer service.

## Exact source evidence

- **LibreChat:** canonical repository moved from `danny-avila/LibreChat` to
  `LibreChat-AI/LibreChat`. Evaluated tag `v0.8.8`, commit
  `e8f3be08623663d4ad7f7241e693c94469b63bb0`. Local read-only sparse checkout:
  `D:\SSC Scout\research\LibreChat-v0.8.8-01a19336`. GitHub release metadata
  marks both `v0.8.8` and newer `v0.8.9-rc1` as prereleases. Do not infer stable
  production qualification from the tag's name. Main observed at
  `f4154b649efa37e1345ccc517a4d8d1ed2178c82`; it was not installed.
- At the pinned LibreChat tag, authenticated middleware chains verified user
  context into tenant handling; file access compares user and file tenants;
  tenant bulk-write helpers strip caller tenant fields and inject scoped values.
  Corresponding source test files were observed. **Tests at v0.8.8 were not run.**
  This checks relevant implementation presence, not every endpoint/background
  job or a complete security audit.
- Ten most-recent retrieved exact-tag workflow entries included successful
  [Windows frontend tests36811699600](https://github.com/LibreChat-AI/LibreChat/actions/runs/36811699600)
  and [tag-image build36807628650](https://github.com/LibreChat-AI/LibreChat/actions/runs/36807628650),
  plus successful/skipped retry workflows. This limited result set does not
  establish a freshly passing full backend/security suite. Requalify a patched,
  digest-pinned release before a deployed pilot.
- Follow-up qualification used **v0.8.9-rc1** at
  `8d3da9bbb220a0a96be9330a2e1cbd385fb786d5`, with a digest-pinned isolated
  runtime. Selected source checks passed187 tests unchanged plus53 with a
  Windows-only test-launch patch;82 real HTTP checks passed after explicit
  tenant-role provisioning and after a synthetic database restore. A new
  tenant's default roles did not automatically inherit YAML platform denies.
  See [exact inputs, findings, limits and harness](SCOUT-LIBRECHAT-QUALIFICATION.md).
  This is progress toward qualification, not deployment or shared-user approval.
- **Open WebUI:** release `v0.12.5`, commit
  `f7ac7ee10962ddec0017f5c29b6740d9b9c5faca`, release metadata not prerelease.
  License/RBAC documentation read; no local runtime/tests.
- **Dify:** release `1.18.0`, commit
  `50abea97062110044f15d0e03ccecadd9ccc87ca`, not prerelease. License/source
  metadata read; no local runtime/tests.
- **Onyx:** release `v5.0.3`, commit
  `e3b96ba7dc55ebd103bdeefa4b5d5961fea388dd`, not prerelease. Repository/license
  split read; no enterprise-edition entitlement or live permission-sync test.
- **Existing Scout/Open Duet:** application code `d7f39e8`, source/acceptance
  documentation `24f5a0e` before this architecture update. Existing exact-head
  CI and owner draft task5/crash task7 evidence remain in Issue #4.

## Supporting components: use only where justified

| Component | Proposed use | Initial operating choice |
| --- | --- | --- |
| [OpenFGA](https://github.com/openfga/openfga) | Resource relationships for documents, projects and devices; Apache-2.0 source. | Qualify with the Scout gateway; intersect with source permissions rather than replacing Odoo record rules. |
| [Keycloak](https://github.com/keycloak/keycloak) | Owned OIDC identity/brokering; Apache-2.0 source. | Reuse the existing approved staff identity provider first; add a broker/customer identity service only if required. |
| [Langfuse](https://github.com/langfuse/langfuse) | Tracing/evaluation integration reference. | Redacted structured audit first; edition, storage and resource qualification before adding another telemetry stack. |
| Existing PostgreSQL / possible pgvector | Work state and a separate retrieval store. | Odoo remains authoritative. A vector extension, new database/account or index is separately qualified; never reuse Odoo superuser credentials. |

The upstream LibreChat Compose example includes MongoDB, a RAG API, pgvector,
Meilisearch and an admin component, and uses moving image tags/default example
settings. Do not run that sample unchanged beside Community. Use a minimal
version-pinned deployment with private ports, explicit secrets, disabled unused
features and capacity tests. One8GB host is not a promise of enterprise scale.

## First qualification slice

1. Pin a supported patched candidate and all required runtime dependencies;
   inspect its authentication/tenant/file/search/background boundaries, relevant
   advisories and exact build/CI. Prefer configuration/extensions over deep forks.
2. Establish two synthetic staff users and two customer tenants in isolation.
   Test denial and revocation across chat, files, retrieval, cached answers,
   MCP and queued work. No real customer documents or business actions.
3. Connect a narrow Scout gateway to the existing queue with verified initiating
   identity, tenant and workflow context. Demonstrate one admission/execution,
   result retrieval/review and duplicate/cancel/restart behavior before rollout.

## Primary references

- [LibreChat access control](https://www.librechat.ai/docs/features/access_control),
  [authentication](https://www.librechat.ai/docs/configuration/authentication),
  [environment/tenant configuration](https://www.librechat.ai/docs/configuration/dotenv),
  [MCP configuration](https://www.librechat.ai/docs/configuration/librechat_yaml/object_structure/mcp_servers).
- [Pinned LibreChat MIT license](https://github.com/LibreChat-AI/LibreChat/blob/e8f3be08623663d4ad7f7241e693c94469b63bb0/LICENSE),
  [release metadata](https://github.com/LibreChat-AI/LibreChat/releases),
  [Compose](https://github.com/LibreChat-AI/LibreChat/blob/e8f3be08623663d4ad7f7241e693c94469b63bb0/docker-compose.yml).
- [Open WebUI license](https://github.com/open-webui/open-webui/blob/f7ac7ee10962ddec0017f5c29b6740d9b9c5faca/LICENSE)
  and [RBAC](https://docs.openwebui.com/features/authentication-access/rbac/).
- [Dify license](https://github.com/langgenius/dify/blob/50abea97062110044f15d0e03ccecadd9ccc87ca/LICENSE).
- [Onyx license split](https://github.com/onyx-dot-app/onyx/blob/e3b96ba7dc55ebd103bdeefa4b5d5961fea388dd/LICENSE).
- [OpenFGA authorization concepts](https://openfga.dev/docs/authorization-concepts),
  [source license](https://github.com/openfga/openfga/blob/main/LICENSE),
  [Keycloak guides](https://www.keycloak.org/guides) and
  [source license](https://github.com/keycloak/keycloak/blob/main/LICENSE.txt).
