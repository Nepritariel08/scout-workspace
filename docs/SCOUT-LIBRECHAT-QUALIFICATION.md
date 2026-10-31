# LibreChat candidate qualification

Historical candidate: the owner's later CopilotKit/OpenDuet pivot supersedes
this foundation and its implementation lane. Preserve these measured receipts
as research; they do not qualify CopilotKit. See the
[active integration contract](SCOUT-COPILOTKIT-PIVOT.md). No LibreChat runtime was
deployed or opened to employees/customers.

Recorded 2026-11-01. This is a bounded synthetic qualification for the
[enterprise architecture](SCOUT-ENTERPRISE-ARCHITECTURE.md), not a production
release, penetration test or approval to admit employees/customers.

The owner source fork is now [Nepritariel08/scout-platform](https://github.com/Nepritariel08/scout-platform),
verified as a public fork of LibreChat-AI/LibreChat with its MIT license retained.
The qualified commit exists in that fork. Its moving default branch is not the
qualified release pin. No future LibreChat pilot is selected by this record.

## Candidate and reproducibility

| Input | Observed value |
| --- | --- |
| Application source | LibreChat-AI/LibreChat `v0.8.9-rc1`, explicitly prerelease; `8d3da9bbb220a0a96be9330a2e1cbd385fb786d5` |
| Runtime image | `ghcr.io/librechat-ai/librechat@sha256:26e3290c82002fd5e4d5e0fd8f7de4d2f2a430f12049d82190d1e4a80f2a3cb2` |
| Runtime Node | 24.22.1, read from the running image |
| Runtime Mongo | 8.0.20; `sha256:098862b1339f031900ca66cf8fef799e616d6324fa41b9a263f2ec899552c1ef` |
| Local source-test runtime | Isolated Windows Node24.22.2/npm11.19.1; MongoMemoryServer11.3.0/Mongo8.2.6 |
| Container environment | WSL Ubuntu, Docker29.1.3, Compose2.40.3; isolated internal network; no effective published host port |

The vendor Windows Node archive matched the retrieved official SHA256 manifest
(`ca1bff5d8ead13c9f2ea404a176db46bd430704d5b5113734049fa365e7799e2`).
Global Node was not changed. The lockfile installed successfully and the three
backend package builds (`data-provider`, `data-schemas`, `api`) passed.

The runtime image has no OCI source-revision label. Seven inspected files match
the source pin after normalizing Windows checkout line endings: root package and
lockfile, JWT strategy, auth/conversation/message routes and file-access
middleware. This is a limited source correspondence check, **not** full build
provenance or a reproducible-build attestation.

## Measured results

| Check | Result and limit |
| --- | --- |
| Four data-schema suites | 88 passed, including real Mongo tenant queries, bulk writes and context/cache-key isolation |
| Three API-package suites | 44 passed: pre-auth tenant trust, authenticated tenant context and credential retirement with failing auth cache |
| Backend JWT/file middleware | 55 passed in two suites |
| Backend auth-route suite, pristine pin on Windows | 53 failed during Mongo startup; Windows Mongo rejects the unconditional `--nounixsocket` option with exit2; reproduced directly |
| Same auth-route suite with test-only platform patch | 53 passed; the patch omits only that unsupported option on Windows and preserves the original assertion bodies |
| Real running release HTTP, initial scope | 70 passed; four USER accounts in three tenants, private conversations/messages/text files, bad-token/retirement/tenant-spoof negatives |
| Explicit tenant deny-policy provisioning | 82 passed, including MCP list/tools/create rejection for every synthetic account |
| Fresh bootstrap with policy before first login | 82 passed in a new project/database created by the checked initializer and seed |
| App restart, no reseed | Initial 70 checks repeated successfully against persistent state |
| Fresh Mongo volume restored from synthetic archive | 82 passed without reseeding; repeated after removing the ineffective host port declaration |

Selected final source results total **240 passing tests across 10 suites**:
187 passed on pristine source and 53 used the test-only Windows portability
patch. These are selected suites, not the complete upstream test suite. The
runtime image was not patched.

The HTTP checks include two staff users in the same tenant and customer A/B
with the same email in different tenants. Each user can read only their seeded
private content. Guessed conversation/message/file IDs and forged tenant headers
cannot expose another account's content. Login without tenant context, malformed
and system tenant values, registration, anonymous access, tampered bearer and a
bearer retired by a credential barrier are rejected. The test supplies tenant
context inside the isolated environment; it does not test a production identity
provider or trusted gateway.

No real customer documents, Odoo credentials, OpenRouter keys or paid inference
were used. The harness makes no model requests; the internal Docker network
blocks external connectivity. The reported zero provider calls describes this
test scope, not a production billing monitor.

## Configuration findings and required controls

1. **Provision tenant roles before admitting users.** The YAML updated platform
   USER permissions, but `getRoleByName` created a missing tenant USER role from
   defaults. A tenant MCP list request returned200/empty object despite the
   platform `mcpServers.use=false` setting. This did not expose a configured
   secret, but it disproved the assumed capability denial. The synthetic
   provisioner copied the verified deny policy into each tenant role; after
   cache eviction/restart, MCP list/tools/create returned403. A production
   provisioner must enforce a policy version before user admission and handle
   policy updates/revocation with cache invalidation and API readback. The
   fixture helper is not that production provisioner.
2. **Tenant headers are trusted only behind a verified gateway.** Strict mode
   plus `TRUST_TENANT_HEADER=true` requires a private backend and a gateway that
   strips client headers and resolves permitted tenant membership. The probe's
   synthetic tenant choice must not become the public admission mechanism.
3. **Check response content and protocol.** File routes rejected the default
   Node User-Agent using an error event inside HTTP200. The fixture now uses
   the expected browser request shape and asserts the private marker as well
   as status; the original response was not counted as a successful download.
4. **Separate platform and environment failures.** WSL shut down the local
   containers gracefully; no app OOM was observed. A bounded owned WSL shell
   kept the distro active for the remaining checks. No global WSL setting or
   unrelated container was deliberately changed. This is not Linode service
   lifecycle acceptance.

## Recovery and operating evidence

The app was stopped before dumping the synthetic `ScoutQualification` database.
The 14874-byte gzip archive was restored into a newly created Mongo container
and volume. SHA256:
`a113b280c58b9929fd6f8cab55e05967dbea582f1f61c6d1d4e6d546424329fe`.
The same protected disposable app keys and fixture manifest were retained;
accounts, private records and tenant deny policies remained usable. The 82 HTTP
checks passed against the restored store without seeding.

This proves a synthetic database restore with preserved keys. It does not prove
binary attachment recovery, loss of app keys, off-host encrypted custody, source
ACL revocation, Odoo/queue recovery or numeric production recovery targets.

One idle sample was approximately386.5MiB for the app and220.8MiB for Mongo
under1.5GiB/768MiB caps. It is not a concurrent-session, retrieval or inference
load test and does not establish safe capacity beside Community Odoo.

## Advisory spot check

The following published vendor advisories list fixes before the candidate tag:
[custom-endpoint SSRF](https://github.com/LibreChat-AI/LibreChat/security/advisories/GHSA-gc9r-88c3-7qhq)
and [MCP URL environment-secret expansion](https://github.com/LibreChat-AI/LibreChat/security/advisories/GHSA-4pcc-j6m6-wcwx)
list v0.8.4-rc1; [MCP viewer secret exposure](https://github.com/LibreChat-AI/LibreChat/security/advisories/GHSA-6vqg-rgpm-qvf9)
lists v0.8.4; [MCP OAuth resource validation](https://github.com/LibreChat-AI/LibreChat/security/advisories/GHSA-gvpj-vm2f-2m23)
lists v0.8.5. This is a source/advisory spot check, not proof that every current
advisory or dependency is resolved. No live exploit test or full dependency
audit was performed.

## Release state and next slice

The [reproducible harness](../qualification/librechat/README.md), Windows test
patch and [sanitized receipt](../qualification/librechat/receipt.json) accompany
this record. Raw logs/reports and the protected synthetic archive stay outside
tracked source. All five disposable containers were read back stopped with
exit0/OOM=false, and the bounded WSL helper ended. Runtime ownership is released
after this evidence is checkpointed in the primary work record. Volumes and the
protected archive are retained for review; no unrelated containers were stopped.

No Linode application, public sign-in, shared staff/customer access, real source
retrieval, tool authority or native-device feature was activated. Next: trusted
identity/tenant admission and production role provisioning, per-user Odoo/queue
mapping, then a minimal private Linode pilot with fresh host ownership. Follow
the remaining employee/customer/device/action acceptance in the architecture;
the physical PC-off test stays deferred.
