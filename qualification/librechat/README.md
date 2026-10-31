# LibreChat synthetic qualification

This harness tests a candidate foundation for Scout. It is **not a production
deployment or a complete employee/customer security qualification**. It contains
no Odoo binding, provider key, production identity provider or native-device
integration. See [measured results](../../docs/SCOUT-LIBRECHAT-QUALIFICATION.md).

The application remains the unmodified upstream release image. The test-only
Windows patch applies to a separate source checkout, not the runtime image.

## Exact inputs

- LibreChat `v0.8.9-rc1`, a prerelease, source
  `8d3da9bbb220a0a96be9330a2e1cbd385fb786d5`.
- App image `ghcr.io/librechat-ai/librechat` digest
  `sha256:26e3290c82002fd5e4d5e0fd8f7de4d2f2a430f12049d82190d1e4a80f2a3cb2`.
- Mongo `8.0.20`, digest
  `sha256:098862b1339f031900ca66cf8fef799e616d6324fa41b9a263f2ec899552c1ef`.
- Recorded host: Windows, WSL Ubuntu, Docker29.1.3/Compose2.40.3. Source tests
  used isolated Windows Node24.22.2/npm11.19.1 and MongoMemoryServer11.3.0
  downloading Mongo8.2.6. These source tests and the Mongo8.0.20 HTTP run are
  separate evidence.

## Isolated runtime

Claim a unique local runtime/project in the existing primary work record. Check
for another writer before operating Docker. Do not stop unrelated containers,
prune Docker, reuse real keys or point these scripts at business databases.

On Windows, run `Initialize-Qualification.ps1 -RuntimeDirectory <absolute empty
directory outside this checkout>`. It copies the runtime files and generates
disposable secrets with owner/SYSTEM NTFS access. It refuses to overwrite an
occupied directory and starts no services. Never print or commit `.env.qa`.

Run Compose from that disposable directory with a unique `--project-name`:

```sh
docker compose --project-name scout-qual-UNIQUE up -d
docker compose --project-name scout-qual-UNIQUE exec -T app node /app/scout-qualification-seed.cjs
docker compose --project-name scout-qual-UNIQUE exec -T app node /app/scout-qualification-probe.cjs
```

The internal network has **no published host ports or external connectivity**.
The probe runs inside the app container and sends real HTTP requests to the
running server. The fixtures are two private staff users in `staff` and one
customer user in each of `customer-a` and `customer-b`; customer emails overlap
deliberately. Every account has USER privileges. Test passwords/tokens never
appear in the result report. Registration, social login and unused capabilities
are disabled. The raised `LOGIN_MAX=1000` is for repeated local tests only.

`TRUST_TENANT_HEADER=true` is a **test fixture**: the probe supplies pre-auth
tenant context within the isolated container. A production gateway must strip
client tenant headers and resolve tenant membership from approved identity and
server configuration. This harness does not establish that gateway.

The seed first copies the verified platform deny policy into each synthetic
tenant's USER role. Do not rely on YAML to update tenant roles automatically.
For a previously seeded run with default tenant roles, invoke
`node /app/scout-qualification-policy.cjs` using `compose exec`, then restart the
app to evict cached roles before testing. This helper accepts only the named
synthetic database/tenants; it is not a production role-management API.

The probe requires correct statuses **and expected private content**. In
particular, the upstream file middleware sends an error envelope with HTTP200
for an unrecognized browser User-Agent. A 200 response alone is insufficient.

## Restart and synthetic database restore

Restart only this project's app, then rerun the probe without reseeding. For
the restore drill:

1. Stop this project's app to quiesce synthetic writes. Use `mongodump` on its
   `mongo` service with `--db ScoutQualification --archive=<private path>
   --gzip --quiet`. Preserve the protected disposable app keys and app-data
   fixture manifest. Record the archive hash; do not commit the archive.
2. Start `mongo-restore` using both `-f compose.yaml -f compose.restore.yaml`.
   Restore the archive with `mongorestore --archive=<private path> --gzip
   --nsInclude='ScoutQualification.*' --quiet`. This creates a new database
   volume; never use `--drop` against an existing or business database.
3. Start `app` with the same two Compose files. The override points it to
   `mongo-restore`; existing app keys and manifest remain mounted. Rerun the
   HTTP probe without seeding. Stop all three qualification services afterward
   and verify their states before releasing ownership.

This checks synthetic Mongo recovery with preserved keys. It does not prove
filesystem attachment backup, key loss recovery, encrypted off-host custody,
Odoo recovery, task replay safety or production recovery targets.

WSL services alone did not keep this test distro running reliably. Keep an
owned, bounded WSL shell active during the drill rather than changing global
WSL configuration. End that shell after stopping the qualification services.

## Existing upstream tests

Use a separate checkout at the exact source pin, read its `AGENTS.md`, install
the lockfile with a suitable isolated runtime and build `data-provider`,
`data-schemas` and `api` from the root scripts. Do not mutate global Node.
Run Jest from each owning workspace with `--runInBand --coverage=false
--runTestsByPath` and record JSON results outside source:

- `packages/data-schemas`: `src/models/plugins/tenantIsolation.spec.ts`,
  `src/models/plugins/tenantIsolation.coverage.spec.ts`,
  `src/config/tenantContext.spec.ts`, `src/utils/tenantBulkWrite.spec.ts`.
- `packages/api`: `src/middleware/preAuthTenant.spec.ts`,
  `src/middleware/__tests__/tenant.spec.ts`,
  `src/auth/credentials.eviction.spec.ts`.
- `api`: `server/middleware/__tests__/requireJwtAuth.spec.js`,
  `server/middleware/accessResources/fileAccess.spec.js`,
  `server/routes/__tests__/auth.tenant.spec.js`.

The pinned auth-route suite unconditionally passes `--nounixsocket` to Mongo.
Windows Mongo8.2.6 rejects it with exit2. Preserve the original failed result;
on Windows, apply `auth-route-windows.patch` to the isolated checkout and rerun
that suite. The patch changes only the platform-specific database launch
argument. Report patched results separately from pristine upstream results.
