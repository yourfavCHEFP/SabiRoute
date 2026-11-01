# Batch 2 Branch Reconciliation — Planning Note (no merge performed)

Prepared 2026-10-22 during the W6 audit. **This is a plan, not an action.**
No merge, rebase, cherry-pick, reset, or history rewrite was performed on
either branch.

## 1. Exact identities

| Role | Ref | Commit | Tree | Paths |
|---|---|---|---|---|
| Local working branch | `feat/sabiroute-routing-foundation` | `b360ffc9e804e19eaf99ec8e470a13a00c733ba5` | `6626167e7b48474ecf412f00c2a52b0e654f7738` | 167 |
| Remote feature tip | `origin/feat/sabiroute-routing-foundation` | `0cb053d9025bc11c0cb44217390c31b8c3594a3f` | `b0089e45fbb99644675d2ce80d2df8e3de272c32` | 96 |
| Remote main tip | `origin/main` | `e4ddc8d958af4ddf87f5b7912068b9cd3838061d` | — | — |
| Local main | `main` | `2802bd20c9dd23a680188b24600b759f193d13c9` | — | — |
| **Merge base** | — | `303032756aa0b195fc57b3ed630a1cbef2a96398` | — | 13 |

Ahead/behind (`origin/feat...local`): **origin 3 ahead, local 2 ahead — diverged.**

## 2. Complete ancestry

```
3030327  core: publish shared gateway, Free Pool policy, quotas, shutdown kill-switch…  (merge base)
├── local  814e6a9  core: restore shared gateway, Free Pool policy, quotas, shutdown kill-switch… (152 paths)
│    └── local  b360ffc  test: document SabiChat integration and web boundary… (2 paths)
└── origin cf957c2  core: Batch 1 core-only release candidate (84 paths)
     └── origin d5a6268  Batch 2: F-04 docs policy, F-05 body/message limits, F-06 credential validation, F-07 purge scheduling, F-08 topology docs, PG CI coverage
          └── origin 0cb053d  Batch 2: candidate-specific core README, core documentation set, provenance boundary
```

## 3. Remote-only commits (3)

| Commit | Subject | Paths | Disposition |
|---|---|---|---|
| `cf957c2` | core: Batch 1 core-only release candidate (84 paths) | 84 | Core payload — **keep** |
| `d5a6268` | Batch 2: F-04 docs policy, F-05 body/message limits, F-06 credential validation, F-07 purge scheduling, F-08 topology docs, PG CI coverage | 13 | Core security/reliability remediation — **keep** |
| `0cb053d` | Batch 2: candidate-specific core README, core documentation set, provenance boundary | 11 | Core release-integrity repair — **keep** |

## 4. Local-only commits (2)

| Commit | Subject | Paths | Note |
|---|---|---|---|
| `814e6a9` | core: restore shared gateway, Free Pool policy, quotas, shutdown kill-switch and deployment contract | 152 | The owner's re-assembled full tree. Includes 32 SabiChat-product paths (see §6) |
| `b360ffc` | test: document SabiChat integration and web boundary; exercise Free Pool eligibility | 2 | `tests/test_sabichat_web.py`, `tests/test_chat_deadline_precedence.py` |

## 5. Overlap and conflicts

- Identical blobs across both trees: **76** · differing: **91**
- Files present only in origin: `.dockerignore`, `src/sabiroute/api/body_limit.py`, `tests/test_request_limits.py`
- Files present only locally: 71 (21 `config/models/*.yaml`, `config/policies/*`, `artifacts/*`, `docs/architecture.md`, `docs/troubleshooting.md`, `docs/controlled-failure-injection.md`, `docs/diagrams/readme-hero.svg`, `docs/phase13-natural-observation-v0.1.md`, `.vscode/settings.json`, `CHANGELOG.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `config/litellm-test.yaml`, `litellm-test.yaml`)
- **A merge is NOT clean.** `git merge-tree --write-tree` reports conflicts on **11 paths**:
  `.env.example`, `.github/workflows/ci.yml`, `Dockerfile`, `README.md`, `docs/deployment.md`, `docs/proxy-retry-visibility.md`, `docs/security.md`, `src/sabiroute/api/completions.py`, `src/sabiroute/chat/store.py`, `src/sabiroute/config/validation.py`, `src/sabiroute/providers/base.py`

## 6. Scope finding: the two lineages differ in kind

`0cb053d` is the **curated Core-only** tree. The local branch is the owner's
**full composite** tree. They differ in substance, not just in file count:

| Capability | local HEAD | origin `0cb053d` |
|---|---|---|
| F-04 documentation-exposure policy (`SABIROUTE_DOCS_ENABLED`) | **absent** | present (`main.py` sets `docs_url`/`redoc_url`/`openapi_url` to `None` unless enabled) |
| F-05 body/message limits (`BodySizeMiddleware`, 1 MiB default) | **absent** | present (`api/body_limit.py` + `tests/test_request_limits.py`) |
| 300 s hard request deadline | **present** (`DEFAULT_REQUEST_DEADLINE_SECONDS = 300.0`) | present (identical) |
| Per-route `max_attempts` (1/2/2/2/2/3) | **present** | present — **identical per route** |
| `RETRYABLE_STATUS_CODES = {401, 403, 429}` | **present** | present (identical) |
| SabiChat product surface (32 paths) | **present** | excluded by design |

## 7. Safest proposed next step (requires owner decision — NOT taken)

**Do not merge.** A merge would silently mix two intentional boundaries: the
curated Core-only release tree and the owner's full composite tree, and would
leave 11 conflicted paths to resolve at the worst possible time.

Recommended sequence, for owner selection:

1. **Keep `0cb053d` as the Core release reference** (already the case; it is
   published and CI-green on run `39694298888`).
2. **Decide the role of the local branch.** It is a *development* line carrying
   the full composite plus the owner's uncommitted work. It should be pushed
   as a clearly named development branch, **not** merged into the release
   branch, unless the owner decides the composite should become the new
   baseline.
3. **If the composite must be rebased onto Core**, do it in a disposable
   worktree as an explicit re-application — not as a merge — so that the
   11 conflicted paths are each re-decided deliberately, and so that F-04/F-05
   are never dropped from the release line.
4. **Before any push**, the local branch's 2 commits need the 96 remaining
   untracked paths accounted for (see the W6 report's exclusion list), and
   the F-04/F-05 gap in the local lineage must be either closed or explicitly
   recorded as a local-lineage limitation.

**Status: no reconciliation performed. Both branches unchanged. No remote
operation of any kind.**
