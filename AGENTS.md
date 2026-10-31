# Repository Agent Instructions

## Test workflow

- For a narrow change, run the smallest tests that cover the changed behavior first. Find test commands in the relevant package and CI workflow; avoid running the entire backend suite as the default local check.
- Run independent backend and frontend checks in parallel when they cover the same change. For a failure, rerun the specific failing test after fixing it.
- The full backend suite includes process, socket, and end-to-end tests and takes several minutes. Run it for broad backend changes, when requested, or as part of CI/release verification. Do not weaken or remove CI coverage to make local iteration faster.
- Use the backend SQLite and throwaway `TOKEN_ENCRYPTION_KEYS` values from `.github/workflows/ci.yml`; never use production credentials in tests.
- Some integration tests need process or localhost socket permissions that a restricted environment may deny. Treat those as environment failures, not product failures, and rerun them in an environment that supports them when the result matters.
- Report exactly which checks passed, skipped, failed, or were interrupted. An incomplete run is not a passing full suite.

## Local package instructions

- Read a package-level `AGENTS.md` before changing files in that package. For example, `frontend/AGENTS.md` contains the frontend-specific framework rules.

## Scout fork

- This fork is `Nepritariel08/scout-workspace`; retain upstream licensing and attribution.
- Read `SCOUT-ADOPTION.md` before Scout integration work. The primary outcome tracker is `Nepritariel08/ssc-ai-enablement#4`, under architecture issue #8; link source PRs there instead of creating another outcome tracker.
- Keep one active writer per branch/file set and runtime target. The DSH/Odoo queue and Community migration have separate owners; this fork does not acquire those targets.
- The first Scout integration is a draft task round trip through the existing Odoo queue and DSH worker. Preserve requester identity, work-item IDs, leases, cancellation and receipts. Do not add a second scheduler for the same jobs.
- Native OpenRouter chat does not imply tool, MCP or computer capabilities. Do not enable unsupported capability flags to bypass the missing execution adapter.
- Source/CI success does not establish provider access, deployment, business-action authority or runtime acceptance. Reconcile the owning queue contract and live bindings before integration or activation.
