# SabiRoute Pre-Roadmap Audit (independent, evidence-backed)

Mode: investigation only. No fixes implemented, no runtime behavior changed,
no commits, no deploys, no provider calls, no production access. All
credentials in this report are placeholder names or openly fake test values;
no real secret is printed.

Baseline: repo `/Users/airm2/My ML Hub/SabiRoute`,
branch `feat/sabiroute-routing-foundation`, HEAD `c50a349b723633fa933e49eb2ff4619f57a198ab`
(verified, matches reported), upstream `origin/feat/sabiroute-routing-foundation`
in sync (0 ahead, 0 behind). 11 tracked files modified (Sprints 1–5 + docs),
untracked additions (freepool, chat, web, 5 test files, ADR, Dockerfile
content, CI, reports) all preserved. `git diff --check` clean.

## 0. Tree inventory vs Sprint 1–5 reports

The code matches the reported checkpoint plus the reported consolidation
(ADR, PG gate, README closeout): no unreported feature work found, nothing
missing that was claimed. `reports/implementation_12h.md` and
`reports/my_scorecard.md` are **gitignored** (verified via `git check-ignore`)
— they exist only on this machine. Machine loss deletes the entire sprint
history (see AUD-09). `reports/provider_verification.json` is tracked.

## 1. Tool register

| Tool | Installed | Instructions inspected | Used for | Result / limitation |
|---|---|---|---|---|
| `review` (gstack skill) | yes | yes (full SKILL.md) | — | NOT APPLICABLE: pre-landing PR workflow with fix cycles; audit forbids implementation. No preamble/telemetry ran. |
| `playwright-cli` | yes (0.1.22) | yes (prior session) | Desktop + mobile smoke | Ran: register/chat/isolation/HTML-safety/logout on desktop; register/chat on mobile Pixel-class viewport. 2 genuine screenshots (`/tmp`, outside repo). |
| repo pytest/ruff/mypy/node/docker | yes | n/a (native) | Full battery | 308 passed / 4 skipped (env-gated Redis), ruff/mypy/diff/`node --check` clean — fresh runs, exit 0. |
| `investigate`, `test-audit`, `plan-ceo-review`, `plan-eng-review`, `ui-ux-pro-max`, `frontend-design`, REA/`reverse-engineer-anything`, Strix, SkillUI, `security-guidance` plugin | not in available-skills list | no (unavailable) | — | Not used; no claim made from them. |
| MCP servers | none observed in this environment | — | — | None used. |
| pip-audit / dep scanner | not installed | — | — | Not run (installing tools is out of scope); dependency risk un-scanned — see AUD-13. |

Rule-10 compliance: only `playwright-cli` and native tools are claimed as used.

## 2. Architecture: current (verified) vs intended

Current, traced in code: `POST /v1/chat/completions` → client-key auth →
usage admission → rate limit → alias/policy → classification → capability →
health → (Free Chat: allowlist gate) → budget reserve → attempt loop over
`Router.choose_deployment` → LiteLLM proxy → `finish()` reconcile. SabiChat
(`/v1/auth/*`, `/v1/conversations/*`) authenticates users itself and calls
that same path in-process with a memory-only service key. Admin boundary is
a separate env secret. Provenance: code-inspected end to end, integration-
tested (stub + sqlite + local PG 16), browser-smoke-tested.

Intended but absent: catalogue→registry mapping, quotas, per-user gateway
identity, billing, monitoring/alerting, backups policy, hosted control
plane. The thesis holds in code (one router, one execution boundary, chat
as client), and trust boundaries are genuinely separated (service keys ≠
user sessions ≠ admin secret). Local-first holds: sqlite-compatible stores,
no hosted dependency for configured capabilities.

## 3. Security-control matrix (scope: local code + tests + smoke)

legend: V = verified within scope · P = partially implemented · NV = not verified · N/A with reason.

- History/tree secret scan (50-commit grep for key formats): V, zero hits
  outside placeholders/tests. `.env` untracked+ignored: V. `.env.example`
  placeholder-only: V. Image excludes `.env`: V (unit-tested).
- Password hashing PBKDF2/600k/salt-16, generic failures, dummy-verify: V.
- Session expiry/revocation/logout: V (tests + browser). No cookies → no
  CSRF surface: V by design. Token in memory only: V (browser: storages 0).
- Ownership enforcement (conversations, cross-user 404s): V (tests +
  browser, second user sees nothing).
- Admin boundary (separate secret, rejects key-equality): V (code-inspected
  + tests, from prior verification; unchanged since).
- XSS/model-output rendering (textContent only): V (static test + browser
  with live `<img onerror>`/`<script>` payloads — inert).
- Attribution spoof resistance (server-forced marker, fixed enum): V.
- Free Pool confinement incl. fallback: V. Budget reserve/reconcile: V.
- Rate limiting: P — per-key Redis bucket real; chat/auth limiters are
  single-process memory (multi-replica bypass, see AUD-03).
- Security headers/CORS policy: P — none configured; absent CORS is
  deny-by-default (safe) but implicit (AUD-06).
- Quotas/spend caps/kill-switch: NV — absent (AUD-01, AUD-02).
- TLS to managed PG: NV by this audit (documented passthrough only).
- Dependency vulnerabilities: NV — no scanner available (AUD-13).
- Zero-findings scanners: none run; nothing certified.

## 4. Quality, tests, routing invariants

Suite 308/4 fresh; doubles are honest fakes (purpose-built stub client,
in-memory key store, real sqlite/PG for persistence). Negative coverage is
real (denials, 401/403/404/429/503 paths, spoof, fallback confinement,
legacy-unknown, migration-failure recovery). Invariants 1–10 (§5 of the
charter) hold on stub/sqlite/PG evidence except: quotas (unimplemented),
live-provider behavior (documentary only), Redis concurrency (skipped
locally), PG partial-failure (untested). Deterministic-v1 and training
gates untouched — verified by diff (no scoring/ML files in scope changed
beyond the empty gated placeholders, which remain empty).

Blind spots: transport-timeout browser path; screen-reader pass; image
contents beyond listing scan; GH Actions run; full-stack compose `up`.

## 5. UI/UX + accessibility register

Functional: all journeys pass on desktop Chromium and one mobile viewport
(genuine screenshots retained outside the repo). Usability: identical
"New conversation" titles confuse switching (cosmetic); reload signs out
(documented trade-off). Accessibility issues: no aria-live for incoming
messages; no focus-visible styling audit; no reduced-motion handling;
contrast unmeasured — all P2, none blocking local use. No visual-inconsistency
defects found beyond title duplication.

## 6. Deployment/ops separation

Image builds (2.71 GB) + smokes green: verified this audit cycle's evidence
stands (re-ran suite/lint; image + compose config re-validated in the
consolidation turn). CI config valid locally; hosted run: NV. Local PG 16
gate 19/19 stands; managed PG: NV. Backup creation: verified locally;
restore: verified locally; managed backup policy: NV. Container health ≠
production readiness — staging, monitoring, rollback, incident policy: NV.

## 7. Strategy challenge

The shared core is justified by real boundaries (one router, one gateway
path, separated credentials), not by aspiration. Local-first is real.
Developer-alpha first is correct ordering (gateway is the most proven
surface). SabiChat beta needs per-user quotas + abuse brakes first.
Free Pool pilot needs quotas + kill-switch + per-provider ToS review.
Differentiators vs OpenRouter/OmniRoute: NO comparative claims are made
anywhere in the repo, and none are supported — correctly absent.
Paid hosting economics: no metering exists, so unit economics are
unmodelled — I is correctly last. Milestone order A→I stands; no reorder
justified by code dependencies found.

## 8. Findings (P0–P3; confidence = code/test evidence, not tools)

- AUD-01 (P1, 9/10): no per-user quotas or spend caps; one service key funds
  all chat. Blocks beta scale + Free Pool pilot. Fix: quota design + enforce
  in gate; accept: exhaustion tests live. Effort: high. Needs owner approval
  (product/billing scope).
- AUD-02 (P1, 9/10): no emergency shutdown for shared inference. Fix: admin
  kill-switch + test. Effort: low. Approval: product scope.
- AUD-03 (P1, 8/10): auth/chat limiters are single-process memory.
  Fix: Redis-backed limits in staging. Effort: medium.
- AUD-04 (P1, 8/10): single gateway service key; restart re-mints; no
  per-user gateway attribution. Fix: key-per-user design decision. Effort:
  medium. Approval: architecture choice.
- AUD-05 (P1, 9/10): managed PG/TLS, backup policy, GH run, compose-up E2E
  all unproven. Fix: milestones C–D. Effort: high.
- AUD-06 (P2, 8/10): no security headers; CORS implicit. Fix: header
  middleware + test. Effort: low.
- AUD-07 (P2, 8/10): no automated browser suite; a11y gaps (§5). Fix:
  Playwright suite + aria-live. Effort: medium.
- AUD-08 (P2, 9/10): 2.71 GB image. Fix: slimming pass. Effort: low.
- AUD-09 (P2, 9/10): sprint history gitignored — machine loss deletes it.
  Fix: owner decides (track reports vs back up elsewhere). Effort: low.
  Approval: required (ignore-rule change).
- AUD-10 (P2, 8/10): telemetry process-local; resets on restart.
- AUD-11 (P3, 7/10): `ruff format` flags 29 files (not enforced; matches
  repo convention — hygiene only).
- AUD-12 (P3, 7/10): hardcoded `/srv/sabiroute` probe fallback in `_web_dir`.
- AUD-13 (P3, 6/10): dependencies never vulnerability-scanned.
- AUD-14 (P2, 8/10): full conversation text persists with no retention,
  export, or deletion story; telemetry itself redacts properly. Fix: retention
  + user export/delete alongside closed beta. Effort: medium.

No P0. No confirmed defect beyond the P1–P3 above; hypotheses are labelled
as gaps, not findings. Tests could pass while vulnerable in: transport
paths, multi-replica limits, PG partial failure, provider behavior — stated,
not hidden.

## 9. Decision gate

1. Verified implemented: gateway+routing+fallback loop, Free Pool gate,
   attribution+ledger (local PG proven), SabiChat backend+UI, container+CI
   config, 308-test suite.
2. Partial/unverified: quotas, catalogue, billing, monitoring, backups
   policy, mobile/a11y depth, GH run, managed PG, staging.
3. Security blockers for exposure: AUD-01–04.
4. Quality/architecture blockers: AUD-05 (evidence), AUD-06/07 (hardening).
5. Developer alpha: CONDITIONAL GO (local, own keys; needs C+D evidence).
6. SabiChat closed beta: CONDITIONAL GO after AUD-01+AUD-02+abuse brakes.
7. Free Pool pilot: NO-GO until AUD-01+AUD-02+ToS review.
8. Public deployment: NO-GO (Phase 20 gate stands).
9. Fix/defer/abandon: fix P1s in milestone order; defer image slimming,
   format hygiene; abandon nothing — nothing is dead code beyond already-
   removed items.
10. Smallest next milestone: quota design + kill-switch + GH green + managed-PG
    validation (C+D slice). 11. Owner must approve: AUD-09 reports fate,
    quota/billing scope, session-persistence trade-off, catalogue model.

## 10. Handoff

Tools used §1; unavailable §1. Commands: pytest 308/4 exit 0; ruff/mypy/
diff/`node --check` exit 0; browser desktop+mobile smoke with 2 genuine
screenshots; secrets history scan zero hits. Worktree preserved; HEAD
`c50a349`. Blind spots §4. No fixes, commits, deploys, or Sprint 6 start.

## 11. Continuation pass (same tree, `c50a349`)

Status: prior audit stood complete; this pass closed its listed browser
leftovers. `security-guidance` probe → `Unknown skill`, verified
unavailable (recorded; nothing claimed from it). Prior "stall" verdict:
snapshot round-trip latency against 2–8s stubs plus tool-turn overhead —
no application defect found; fast-stub interactions respond promptly.

New browser evidence (disposable DBs, stub, port 8020): invalid credentials
→ generic "Invalid email or password.", stays on auth; register → logout →
sign-in returns to the owning account; console holds only the expected 401
fetch log, zero JS errors. Telemetry privacy re-verified: snapshots store
byte counts with `[redacted]` values and never return request text
(`dataset.py:115-125,141,304-317`); full conversation text persists only in
owner-scoped `sabichat_messages` by product design — no retention/export
policy exists (new P2 AUD-14). Sprint 13/15 artifacts inspected: deadline
experiments, 429 drills, and the sync-DB P1 assessment are explicitly
proposal/drill/assessed-NOT-remediated documents with fake creds and no
egress — names establish nothing, and the files say so themselves; note the
P1 assessment predates the uncommitted 16A/16B executor remediation (owner
decision pending on that work). Battery re-run: 308/4 exit 0, ruff/mypy/
diff clean exit 0. Added finding: AUD-14 (P2) chat-history retention/export
gap. Scores held (no new capability). No fixes, commits, or Sprint 6 start.
