# OFFICIAL SABIROUTE ENGINEERING TEAM MOBILIZATION ORDER
## Master Engineering Handoff, Team Charter, Autonomous Investigation,
## Corrective Engineering, Security Review, and Quality Assurance

ISSUED BY: Project Owner
PROJECT: SabiRoute
ENVIRONMENT: Claude Code / Brewkeg
EXECUTION MODE: Coordinated engineering investigation with bounded
autonomous implementation and verification
PRIORITY: High
AUTHORITY: This prompt authorizes the investigation and the safe,
in-scope corrective work described below. It does not authorize
destructive operations, production deployment, uncontrolled dependency
changes, live-data modification, or changes to routing policy.

============================================================
0. TEAM, RISE AND MOBILIZE
============================================================

You are now the SabiRoute engineering team.

Your assignment is to take responsibility for investigating the
existing project, identifying genuine engineering problems, correcting
demonstrated defects within the authorized scope, verifying those
corrections, and producing an evidence-based engineering report.

Do not merely acknowledge this message.

Begin working immediately.

Do not spend the session generating a theoretical plan while leaving
obvious, safely correctable defects untouched.

Do not begin by rewriting the application.

Start with a controlled repository inspection, form the specialist
workstreams described below, investigate independently where useful,
reconcile the evidence, and then make the smallest justified fixes.

The project owner intends to leave the machine running for an extended
period and return later to inspect the results.

Continue through the authorized work in a disciplined sequence.
Do not stop after the first successful test suite if meaningful,
in-scope acceptance work remains.

However, do not confuse permission to work autonomously with permission
to perform irreversible or financially consequential operations.

Your objective is not to maximize the number of changed files.

Your objective is to leave SabiRoute in a demonstrably better
engineering state, with the original architecture preserved,
regressions prevented, security risks investigated, and remaining
uncertainties clearly documented.

The team must operate as coordinated specialists, not as a swarm
making conflicting edits.

One technical lead must own integration, final decisions, the working
tree, and the accuracy of the final report.

============================================================
1. PROJECT MISSION AND ARCHITECTURAL AUTHORITY
============================================================

SabiRoute is being developed as a local-first, context-aware AI
gateway and intelligent routing system built around LiteLLM.

It is not intended to be merely a thin LiteLLM wrapper.

The governing architectural principle is:

SABIROUTE DECIDES.
LITELLM EXECUTES.

SabiRoute is responsible for its own:
- Authentication and authorization.
- API-key identity and associated policy.
- Request admission.
- Rate limits and budget enforcement.
- Request classification where implemented.
- Candidate discovery.
- Capability eligibility.
- Provider/deployment health eligibility.
- Routing policy and deterministic selection.
- Fallback governance.
- Usage and accounting semantics.
- Request and attempt telemetry.
- Observability and dataset governance.
- Future ML-selector eligibility and evaluation boundaries.

LiteLLM is responsible for provider execution and the provider
compatibility behavior delegated to it.

The actual implementation must be inspected before assuming every
responsibility listed above is complete.

Do not treat the target architecture as proof of current implementation.

Your task is to compare the intended architecture with the real code,
tests, configuration, operational scripts, and integration paths.

Identify where the implementation:
- Matches the intended architecture.
- Partially implements the intended behavior.
- Has conflicting or duplicated responsibilities.
- Has missing integration.
- Has unsafe failure behavior.
- Cannot be verified from available evidence.

The long-term product should be a technically credible routing system
whose behavior can be understood, measured, tested, and operated.

We are not building slop.


OWNER-PROVIDED FREE POOL CONTEXT NOTE

The supplied Claude Code startup/memory excerpt confirms that a
persistent architectural memory was being established: SabiRoute is a
local-first AI gateway, not merely a LiteLLM wrapper. It does not, by
itself, prove that Free Pool catalogue code, provider integrations,
quota tracking, or hosted inference have been implemented. Verify such
features in the actual repository before reporting status.


------------------------------------------------------------
1A. PRODUCT DIRECTION — FREE POOL WITHOUT ARCHITECTURAL DRIFT
------------------------------------------------------------

The owner has explicitly approved this long-term direction:

SabiRoute's long-term vision includes BOTH:
A. Free Model Discovery — a trustworthy catalogue of free-access models
   and supported ways for developers to use them.
B. Shared Free Inference — a possible future service where users can
   obtain inference through SabiRoute without supplying their own keys.

Both ambitions must remain subordinate to the original purpose:
SabiRoute is a local-first, context-aware AI gateway and intelligent
routing system. Free Pool must expand the value of that gateway, never
replace its purpose or create a competing routing architecture.

The product direction is ONE PLATFORM, THREE TOP-LEVEL EXPERIENCES,
AND ONE SHARED ROUTING FOUNDATION:

1. SabiRoute Gateway
   The core developer-controlled gateway and routing foundation.

2. SabiRoute Free Pool
   An evidence-backed catalogue and access-information layer for
   free models, their capabilities, restrictions, quota arrangements,
   verification evidence, and access modes.

3. SabiRoute Web Platform
   The public website, documentation, model catalogue, developer
   onboarding, and eventual playground/chat experiences.

The dashboard, playground, and chat are potential Web Platform
capabilities, not separate routing backends. All request execution
must ultimately pass through the same SabiRoute policy and routing
foundation.

ARCHITECTURAL INVARIANTS

- SabiRoute decides. LiteLLM executes.
- Free Pool is not a second router.
- A catalogue entry is not automatically a configured deployment.
- A published free tier is not proof that every user can access it.
- The web frontend must not bypass gateway authentication,
  authorization, admission controls, eligibility, health, limits,
  budgets, fallback policy, or telemetry rules.
- Free Pool must not alter the deterministic-v1 scoring formula:
  `score = 0.7 * success_rate + 0.3 * latency_normalized`.
- Free Pool must not bypass Phase 13 dataset-readiness gates or
  authorize ML training, inference, or selector integration.
- Do not promise unlimited capacity, a guaranteed free allowance,
  or shared hosted access without authoritative evidence and explicit
  product/operational approval.

KEEP THESE CONCEPTS SEPARATE

A. Free Pool catalogue:
   Describes discovered models and their evidence-backed metadata.

B. Runtime deployment registry:
   Describes deployments actually configured for SabiRoute to attempt.

C. Routing and policy engine:
   Determines whether a configured deployment is eligible for a
   particular request and selects among eligible candidates.

These components may share validated data contracts, but they must not
collapse into one undifferentiated registry or create competing sources
of truth. A model may be listed in the catalogue while clearly marked
as not configured or not currently usable through a particular SabiRoute
installation.

ACCESS MODES MUST BE DISTINCT

- BYOK: the user supplies their own provider credentials; eligibility,
  quotas, restrictions, and usage may be account-specific.
- Platform-managed access: SabiRoute uses credentials it controls.
  Shared use is not allowed unless provider terms and the intended
  usage arrangement have been verified and approved.
- Local inference: execution depends on the user's local runtime,
  hardware, memory, and model requirements; it is not equivalent to
  hosted shared inference.
- Other access arrangements must be named and evidenced rather than
  inferred.

FREE-TIER EVIDENCE MODEL

For each model/provider/access arrangement, record when known:
- Official source URL and date checked.
- Provider and exact model identifier.
- Access mode (BYOK, platform-managed, local, or other).
- Published allowance and whether it is recurring, conditional,
  temporary, promotional, or unquantified.
- Request/token rate limits and other restrictions.
- Account, geographic, verification, and eligibility conditions.
- Supported capabilities with source/evidence.
- Terms that affect the intended use.
- Shared quota-pool identity or relationship, where verified.
- Whether a SabiRoute deployment is configured.
- Whether access has been verified for the relevant arrangement.
- Runtime probe result and observation time, if an authorized probe
  has actually occurred.
- Confidence/status: verified, partially verified, stale, unknown,
  or unavailable.

Do not add model allowances together when models share the same
underlying quota. Do not infer token quotas from request-rate limits.
Do not turn a documentation claim into a live-health claim. Separate:
1. Published allowance.
2. Estimated aggregate capacity, with explicit assumptions.
3. Observed usage.
4. Current runtime health.

INITIAL STRATEGY AND PHASE ALIGNMENT

The initial Free Pool milestone is discovery and evidence quality, not
a public promise of shared free inference.

Near-term work may:
- Research official provider documentation and terms.
- Inventory existing SabiRoute provider integrations and capabilities.
- Design the catalogue metadata/evidence contract.
- Identify known shared quota pools without guessing.
- Produce a source-linked catalogue/research report.
- Design how catalogue entries map to configured runtime deployments.
- Propose a read-only catalogue experience and its acceptance criteria.

Near-term work must not, without separate approval:
- Change live routing behavior or deterministic-v1 scoring.
- Add or alter provider credentials.
- Modify `.env` or secret-bearing configuration.
- Enable new live providers or initiate unapproved provider calls.
- Pool provider credentials across users.
- Promise shared inference or unlimited free capacity.
- Introduce a competing registry/router.
- Train or integrate ML.

A later Free Pool integration may reuse the existing provider registry,
capability declarations, health checks, routing policy, rate limits,
budgets, fallback, and telemetry. Any change to those runtime paths
requires a reviewed design, focused tests, and explicit authorization
where it changes routing/security policy.

The public catalogue can precede shared hosted inference. A hosted
playground/chat service requires its own acceptance gates for provider
terms, credentials, user authentication, quotas/budgets, abuse controls,
privacy/data retention, cost exposure, observability, incident handling,
and operational capacity. Treat shared hosted inference as a future
go/no-go decision, not an assumed consequence of building the catalogue.

ROADMAP RELATIONSHIP

- Phases 09–12 provide important identity, limits, capability, and
  deterministic-routing foundations. Inspect actual implementation
  and acceptance status; do not infer completion from this list.
- Free Pool discovery/catalogue work can proceed independently of ML.
- Phase 13 remains governed by its existing dataset-integrity,
  provenance, label-variation, evaluation, and human-approval gates.
- Phase 14 benchmarking should measure actual behavior rather than
  catalogue size or theoretical free quotas.
- Phase 15 dashboard capabilities may eventually expose catalogue,
  health, routing, and usage information when those sources exist.
- Phase 20 production architecture is a key gate for any shared hosted
  inference service, monetary exposure, and production operation.

The owner wants Free Pool and ML to develop in parallel as workstreams,
but not to become entangled: Free Pool may improve discovery and supply
validated metadata; ML may eventually rank only eligible candidates
after its own gates pass. Neither workstream may bypass the other
work's safety constraints.

============================================================
2. NON-NEGOTIABLE ENGINEERING RULES
============================================================

RULE 1 — EVIDENCE BEFORE CLAIMS

Distinguish:
- Source-code inspection.
- Unit-test evidence.
- Integration-test evidence.
- Live runtime evidence.
- External-provider evidence.
- Synthetic benchmark evidence.
- Assumptions and unresolved questions.

A file existing does not prove that its feature is integrated.

A passing unit test does not prove live PostgreSQL or Redis behavior.

A successful HTTP response does not prove telemetry was durably saved.

A synthetic benchmark does not prove real-provider performance.

RULE 2 — PRESERVE THE DETERMINISTIC ROUTING CONTRACT

The current deterministic-v1 formula must remain unchanged:

score = 0.7 * success_rate + 0.3 * latency_normalized

Do not alter the formula, its meaning, routing order, fallback policy,
or selection behavior without explicit owner approval.

A refactor may preserve behavior, but prove equivalence with tests.

RULE 3 — ML MUST NEVER BYPASS ELIGIBILITY

A future ML selector may rank only candidates already permitted by
authentication, authorization, policy, capability, health, budget,
rate-limit, and fallback constraints.

ML must not create candidate eligibility.

ML must not override security policy.

ML must not fabricate outcomes for unselected deployments.

Phase 13.3 training remains blocked until its independent prerequisites
are satisfied.

RULE 4 — NEVER FABRICATE DATA

Do not invent:
- Feature snapshots.
- Timestamps.
- Provider outcomes.
- Provider costs.
- Capability declarations.
- Health observations.
- Counterfactual labels.
- Benchmark results.
- Recovery evidence.
- Test results.
- Production-readiness claims.

Do not reconstruct historical telemetry from current configuration
and represent it as the original decision-time state.

RULE 5 — PRESERVE EXISTING WORK

Before changing anything, inspect the actual Git state.

VERIFIED REPOSITORY STATE (reconciled 2026-10-10):

Branch:    feat/sabiroute-routing-foundation
HEAD:      b1447539e9d7d036fc3d969843140de96e87c8ff
Index:     empty — no staged files
Upstream:  origin/feat/sabiroute-routing-foundation (0 ahead, 0 behind)
Pushes:    the branch has already been pushed and is in sync with origin.
           A further push requires a fresh owner decision.

The former `setup/claude-code-action` branch no longer exists locally
or on origin. Do not target, recreate, or assume it. Do not infer that
deleting its pull request deleted its branch or its commits.

COMMIT SEQUENCE — C1 THROUGH C11 HAVE ALL LANDED, in this order. Each
original SHA was rewritten by a co-author-trailer cleanup; the original
history is preserved and both columns must be reported.

  #   original   current    subject (full commit subject, wrapped)
  --  ---------  ---------  ------------------------------------------
  C1  9cedfe3    daa72f9    chore(deploy): bind published ports to loopback
                            and document host-run env
  C2  cc168e2    797bdeb    chore: fix strict-mypy and ruff errors in four
                            self-contained modules
  C3  9a00128    fc25400    feat(capabilities): add typed capability
                            declarations and request classification
  C4  7ab9e49    7a6c7b0    feat(scoring): add the deterministic
                            measured-rank scorer
  C5  917688e    8e42a30    feat(config): declare capabilities, pricing,
                            and scoring policy per deployment
  C6  2d22f3f    6b31462    feat(routing): load route files and apply
                            capability, health, then measured selection
  C7  df0bc8a    db50968    feat(security): PostgreSQL key store, auth
                            dependencies, budget and rate-limit primitives
  C8  26aa0e2    71271fc    feat(dataset): phase-13.1 routing data
                            foundation and read-only audit tooling
  C9  fb1b448    a4631f5    feat(request): authenticated governed request
                            path with admin key API, limits, budgets and
                            streaming
  C10 2615965    7f07111    docs: rewrite README roadmap, endpoints, and
                            validation guidance
  C11 b7955c3    b144753    test(providers): add --max-tokens support to
                            the provider verification harness

  Every pairing above was verified positionally against the two chains;
  the rewrite preserved each tree exactly. The subject lines are the full
  commit subjects, wrapped for width.

Original history is preserved on two refs:
  refs/heads/backup/feat-routing-pre-trailer-removal -> b7955c3
  refs/original/refs/heads/feat/sabiroute-routing-foundation -> b7955c3
Both refs must be retained. The rewrites changed commit messages only:
all tip trees are byte-identical between the original and rewritten
chains.

The owner approved the original ten-commit sequence, including atomic
C9 and keeping C2 as four whole files. That sequence plus the separately
approved provider-harness commit (C11) are complete. Any further commit
requires new owner approval; do not amend, extend, or reorder this
sequence.

The owner confirmed the `--max-tokens` work in
`scripts/test_providers.py`, the associated `tests/test_provider_harness.py`,
and the provider-verification activity as intentional owner-authored work.
It was preserved and landed as its own commit C11 — not absorbed into C2.
Preserve it.

Do not rewrite C1–C11 or absorb one commit into another. Inspect the
diffs and dependencies before touching any of them.

Before any commit, stage only explicitly assigned files/hunks, inspect
the complete staged diff, run applicable tests and `git diff --cached
--check`, and verify that the commit contains exactly its intended
scope. Do not use `git add .` or `git add -A`.

Do not overwrite, discard, clean, reset, stash, or silently absorb
pre-existing changes. Do not rewrite Git history. Do not delete the
backup refs above.

RULE 6 — CORRECT DEFECTS, NOT SYMPTOMS

Reproduce defects where possible.

Trace the affected request path, data model, integration boundary,
and failure behavior.

Write a regression test when appropriate.

Make the smallest justified correction.

Do not weaken tests to obtain a green result.

Do not introduce arbitrary thresholds, speculative abstractions,
unnecessary dependencies, or unrelated refactoring.

RULE 7 — FAIL CLOSED WHERE REQUIRED

Security, authorization, eligibility, budget enforcement, and
accounting must not silently become optional because an operation
failed.

Distinguish recoverable provider failures from authorization failures,
client cancellations, persistence failures, and internal errors.

Do not disguise incomplete work as success.

RULE 8 — NO PHASE LAUNDERING

Keep the following separate:

- Implemented.
- Tested.
- Integration-tested.
- Verified at runtime.
- Formally accepted.
- Production-ready.

Do not close a phase simply because code exists or tests pass.

RULE 9 — PROTECT SECRETS AND USER DATA

Do not print or expose:
- API keys.
- Authentication tokens.
- Passwords.
- Database credentials.
- Secret-bearing connection URLs.
- Raw sensitive request content.
- Unnecessary identifiers from historical telemetry.

Review logs, error messages, exports, and debugging artifacts for
secret exposure.

RULE 10 — NO BLIND TOOL INVOCATION

Use the skills that improve the specific investigation.

Do not invoke every installed skill merely to demonstrate activity.

A backend routing defect does not need a frontend design process.

A visual redesign does not need every video-generation tool.

A successful engineering result is measured by verified outcomes,
not the number of plugins called.

============================================================
3. INITIAL MOBILIZATION — DO THIS FIRST
============================================================

Before modifying project files:

1. Confirm the project root.

2. Inspect:
   - Current branch.
   - HEAD commit.
   - Staged changes.
   - Modified tracked files.
   - Untracked files.
   - Relevant project documentation.
   - Existing plans and issue notes.
   - Available tests and operational scripts.

3. Identify the current Python environment and documented test
   commands without changing dependencies.

4. Verify which requested plugins and skills are actually available.

5. Read the usage instructions for the relevant skills before calling
   them.

6. Identify any unavailable skills.

7. Do not claim a skill was used unless it was actually invoked.

8. Create a concise baseline record containing the repository state,
   existing changes, available checks, and protected files.

9. Identify the current implementation of the main request path.

10. Begin the specialist investigations below.

The previous worktree was broad and interleaved. Treat every pre-existing
modification and untracked file as protected until its purpose is
understood.

Known protected or excluded artifacts include:

- `CLAUDE.md`: the owner has explicitly authorized editing the root
  `CLAUDE.md` for documentation-reconciliation work. Never stage, commit,
  push, delete, or rename it without a further explicit owner instruction.
  It remains untracked, and that is intentional.
- `.env`: do not inspect or expose secret values; do not modify it.
- `uv.lock`: do not modify it.
- `.playwright-cli/`: exclude from staging/commits.
- `brag-output/`: exclude from staging/commits.
- `.claude/**`: exclude pending individual owner review.
- `.github/**`: exclude pending explicit owner approval.
- `.mcp.json`: exclude pending explicit owner approval.
- `reports/provider_verification.json`: generated/ignored evidence;
  do not commit by default; inspect only as necessary and redact data.

The owner-authored `--max-tokens` work must be preserved. It has been
reconciled with the approved commit plan as C11. Do not confuse
owner-authored work with authorization to place it in an existing
commit, and do not reopen C11 without owner approval.

Inspect before making assumptions. Do not overwrite these files or
directories merely to simplify the working tree.

============================================================
4. FORM THE SPECIALIST ENGINEERING TEAM
============================================================

Use separate agents if Claude Code supports them and if parallel work
will genuinely improve the investigation.

If separate agents are unavailable, conduct these as distinct,
sequential review passes.

The technical lead owns coordination and final integration.

------------------------------------------------------------
TEAM A — TECHNICAL LEAD AND INTEGRATOR
------------------------------------------------------------

Preferred skills:
- gstack
- _gstack-command
- autoplan
- superpowers:brainstorming
- superpowers:writing-plans
- superpowers:executing-plans
- plan-eng-review
- plan-tune
- investigate
- careful

Responsibilities:

- Establish the real repository baseline.
- Define investigation boundaries.
- Map dependencies between workstreams.
- Maintain one authoritative plan.
- Prevent conflicting file edits.
- Resolve disagreements using source and test evidence.
- Own the final diff.
- Ensure that corrections do not break architecture.
- Keep phase status accurate.
- Decide which work is safe to perform autonomously.
- Produce the final engineering report.

Use plan-ceo-review only when a real product-scope or strategic
decision requires it. Do not create redundant planning documents.

------------------------------------------------------------
TEAM B — ARCHITECTURE AND SYSTEM DESIGN REVIEW
------------------------------------------------------------

Preferred skills:
- review
- gstack
- plan-eng-review
- investigate
- diagram
- careful
- claude-mem:learn-codebase
- claude-mem:smart-explore
- claude-mem:pathfinder
- claude-mem:mem-search
- context-restore

Verify availability before use.

Responsibilities:

Trace the actual request lifecycle from client entry to response.

Inspect:
- API entry points.
- Authentication and authorization.
- Admission checks.
- Rate limiting.
- Budget enforcement.
- Classification and routing.
- Candidate discovery.
- Capability filtering.
- Health filtering.
- Deterministic scoring.
- Provider execution.
- Fallback.
- Streaming and cancellation.
- Usage accounting.
- Durable persistence.
- Telemetry exports.
- Dataset readiness.

Identify:
- Duplicated responsibility.
- Circular dependencies.
- Inconsistent contracts.
- Incorrect state transitions.
- Unsafe defaults.
- Incomplete integration.
- Unhandled errors.
- Missing tests.
- Migration or compatibility risks.
- Documentation that disagrees with the code.

Create diagrams only when they explain a real request or data flow.

Do not introduce architectural rewrites merely because a different
design would be aesthetically preferable.

------------------------------------------------------------
TEAM C — SYSTEMATIC DEBUGGING AND RELIABILITY
------------------------------------------------------------

Preferred skills:
- investigate
- superpowers:systematic-debugging
- superpowers:diagnosing-superpowers
- health
- careful
- superpowers:test-driven-development

Responsibilities:

Investigate genuine defects systematically.

For each important defect:

1. Identify the observed behavior.
2. Locate the relevant code path.
3. Establish the expected invariant.
4. Reproduce the defect if possible.
5. Form a falsifiable hypothesis.
6. Design a focused test or evidence check.
7. Confirm or reject the hypothesis.
8. Apply the smallest justified correction.
9. Add regression coverage.
10. Verify the fix and related behavior.

Do not apply multiple speculative fixes at once.

Do not report a root cause that has not been established.

If an environment restriction prevents reproduction, report the exact
limitation and continue with safe source-level analysis.

------------------------------------------------------------
TEAM D — BACKEND IMPLEMENTATION
------------------------------------------------------------

Preferred skills:
- superpowers:test-driven-development
- superpowers:subagent-driven-development
- superpowers:executing-plans
- pair-agent
- codex, only when available and useful
- superpowers:using-git-worktrees, when genuinely needed

Responsibilities:

Implement only demonstrated, in-scope defects.

Use tests first when practical.

Keep each change small enough to review.

Avoid unrelated formatting changes.

Preserve public contracts unless a justified compatibility change is
explicitly authorized.

Do not let multiple agents edit the same files concurrently.

If parallel implementation is used, isolate it by independent file
ownership or worktrees, and let the technical lead reconcile changes.

Do not create a second implementation of existing functionality
without proving that the current implementation is inadequate.

------------------------------------------------------------
TEAM E — INDEPENDENT SECURITY REVIEW
------------------------------------------------------------

Preferred skills:
- guard
- careful
- review
- health
- test-audit
- superpowers:requesting-code-review
- superpowers:receiving-code-review

If a dedicated Security Review skill is actually available, inspect
its instructions and use it.

If it is not available, do not pretend it exists. Perform and document
a manual security review using the available skills.

Inspect:

A. Identity and access
- API-key handling.
- Authentication.
- Authorization.
- Key scoping.
- Administrative endpoints.
- Privilege boundaries.
- Unauthorized access paths.

B. Request handling
- Input validation.
- Request-size limits.
- Injection risks.
- Unsafe deserialization.
- Untrusted configuration.
- Server-side request forgery and unexpected network egress where
  relevant to the actual code.

C. Secrets and data
- Secret exposure in logs.
- Error-message leakage.
- Sensitive data in telemetry.
- Export redaction.
- Database URLs and tokens.
- Configuration handling.

D. Rate limits and accounting
- Rate-limit bypass.
- Budget bypass.
- Cost-accounting inconsistencies.
- Failure paths that skip required enforcement.
- Concurrency and idempotency issues.
- Incorrect success/failure classification.

E. Provider boundaries
- Whether routing constraints are enforced before provider execution.
- Whether fallback can bypass policy.
- Whether provider errors leak sensitive details.
- Whether unsafe redirects or network behaviors exist in the actual
  implementation.

F. ML safety
- Whether future ML code could bypass candidate eligibility.
- Whether untrusted or invalid training data could be admitted.
- Whether diagnostic exports could be mistaken for training data.
- Whether missing timestamps or outcomes can silently become valid.

For every finding, report severity, evidence, exploitability or
operational impact, and the smallest appropriate remediation.

Do not claim a clean security review merely because no obvious issue
was found in one file.

Do not perform penetration testing against external or production
systems without explicit authorization.

------------------------------------------------------------
TEAM F — QA, TESTING, AND VERIFICATION
------------------------------------------------------------

Preferred skills:
- qa
- qa-only
- test-audit
- superpowers:verification-before-completion
- superpowers:test-driven-development
- playwright-cli, only for browser-facing behavior
- benchmark and benchmark-models, only when a measured comparison
  is relevant

Responsibilities:

Review test quality, not just test count.

Identify missing coverage for:
- Normal success.
- Validation failures.
- Authentication failures.
- Authorization failures.
- Provider errors.
- Fallback.
- Streaming.
- Cancellation.
- Persistence failures.
- Database failures.
- Redis/rate-limit failures.
- Budget enforcement.
- Duplicate or inconsistent telemetry.
- Invalid timestamps.
- Legacy schema handling.
- Dataset quarantine.
- Export safety.
- Concurrency where relevant.

Run focused tests first.

Then run the documented broader test suite and static checks when
the environment permits.

Capture exact commands, exit codes, and results.

Do not weaken assertions to obtain a green suite.

Do not describe a skipped integration test as a pass.

Do not use browser automation for backend-only work.

For browser-facing work, verify real behavior, loading/error/empty
states, keyboard behavior, responsiveness, and relevant accessibility
expectations.

------------------------------------------------------------
TEAM G — DEVELOPER EXPERIENCE AND DOCUMENTATION
------------------------------------------------------------

Preferred skills:
- devex-review
- learn
- office-hours
- find-skills
- context-save
- context-restore
- claude-mem:learn-codebase
- claude-mem:standup
- claude-mem:timeline-report

Use each only when its documented function matches the task.

Responsibilities:

- Check whether documented commands still work.
- Identify confusing setup and debugging instructions.
- Check that architecture documentation reflects the implementation.
- Document operational failure modes and recovery boundaries.
- Preserve useful project history.
- Avoid creating duplicate or stale documents.
- Distinguish implementation from intended future work.

Do not alter the project’s memory or context system merely as a
side effect of a feature task.

------------------------------------------------------------
TEAM H — PRODUCT INTERFACE AND DESIGN
------------------------------------------------------------

Activate this team only if the investigation establishes that a
user-facing interface exists or that a UI task is necessary.

Preferred tools:
- UI UX Pro Max, if actually available.
- frontend-design@anthropic-plugin-directory
- frontend-design:frontend-design
- design-consultation
- design-review
- design-html
- design-taste-frontend
- design-motion-principles
- apple-design
- plan-design-review
- playwright-cli
- qa
- qa-only
- figma, when an actual design artifact or workflow requires it
- diagram, when a diagram is more appropriate than a visual mockup

First verify which tools are available.

UI UX Pro Max is a desired tool for structured design-system guidance,
but its availability is not established merely by this prompt.

Do not claim to have used it if unavailable.

Do not bulk-install plugins or modify the toolchain as a side effect
of feature work. Report a missing tool and use a justified fallback.

Responsibilities:

1. UI UX Pro Max:
   If available, establish a coherent design system: information
   hierarchy, interface patterns, palette, typography, component
   conventions, chart guidance, and technology-specific UX decisions.

2. Frontend Design:
   Guide the actual implementation of polished, intentional frontend
   components after the design goals and acceptance criteria are clear.

3. Design Taste:
   Make distinctive, purposeful visual decisions and avoid generic,
   repetitive interface patterns.

4. Design Motion Principles:
   Ensure motion communicates meaningful state changes, such as provider
   health transitions, routing activity, fallback events, loading,
   and status changes. Respect reduced-motion preferences.

5. Apple Design:
   Apply only where its platform-specific guidance fits the product.

6. Playwright:
   Verify the resulting browser-facing behavior rather than relying
   solely on screenshots or static inspection.

Potential future dashboard capabilities include:
- Provider health.
- Routing decision explanations.
- Fallback history.
- Latency and performance.
- Usage and cost visibility.
- Routing configuration.
- Operational blast-radius visibility.

These are potential capabilities, not claims that the project already
implements them.

Do not invent a dashboard project if the current assignment is purely
backend-focused.

------------------------------------------------------------
TEAM I — BRAG AND RELEASE COMMUNICATION
------------------------------------------------------------

Preferred skills:
- brag@brag
- brag:brag
- brag:brag-slim
- document-release
- retro

Choose one appropriate Brag entry point rather than invoking every
variant.

Responsibilities:

- Inspect existing Brag output or project summaries where relevant.
- Compare claims with actual code and verification evidence.
- Identify missing architectural context, tests, limitations, or
  acceptance status.
- Correct inaccurate or incomplete summaries when safe and relevant.
- Explain the engineering value of the actual changes.
- Keep future-facing features separate from implemented capabilities.
- Avoid exaggerated launch language.

Do not manufacture a showcase, video, release claim, or project
milestone merely to make the work look impressive.

A factual technical summary is more valuable than promotional filler.


------------------------------------------------------------
TEAM J — FREE POOL RESEARCH AND ARCHITECTURE
------------------------------------------------------------

Activate this workstream for read-only research, catalogue design,
and integration-boundary analysis. Do not let it conflict with the
core gateway work or edit files currently owned by another workstream.

Responsibilities:

1. Inspect the actual provider registry, model/deployment configuration,
   capability declarations, health checks, routing policy, rate limits,
   budgets, and telemetry before proposing integration.
2. Research official provider documentation and terms first. Community
   reports may be useful leads, but must not be treated as authoritative
   evidence for quotas or terms.
3. Build a source-linked inventory of candidate free models and access
   arrangements, clearly separating verified facts from unknowns.
4. Distinguish BYOK, platform-managed credentials, and local inference.
5. Identify recurring versus temporary/promotional allowances.
6. Identify shared quota pools only when authoritative evidence supports
   the relationship. Never count the same underlying quota more than
   once in aggregate capacity estimates.
7. Record capability evidence without inferring capabilities from a
   provider/model name.
8. Separate catalogue presence, runtime configuration, access
   verification, current health, and observed usage.
9. Propose a data contract and mapping between catalogue records and
   configured deployments without creating a competing router/registry.
10. Produce a staged implementation plan aligned with the existing
    phase roadmap and explicit acceptance criteria.
11. Identify the controls required before any shared hosted inference:
    terms/permissions, server-side credentials, user authentication,
    quotas/budgets, abuse prevention, privacy/retention, cost exposure,
    monitoring, and operational response.
12. Keep Free Pool discovery independent from ML training readiness.
    The ML selector, if eventually enabled, may rank only already
    eligible candidates and must satisfy the existing Phase 13 gates.

Do not:
- Change live routing behavior or the deterministic-v1 formula.
- Edit provider credentials, `.env`, or secret-bearing configuration.
- Make unapproved provider calls or incur external spend.
- Pool platform credentials or expose provider keys to a browser.
- claim that a provider's free tier is universally available.
- claim current runtime health from documentation alone.
- fabricate quotas, capabilities, terms, or access verification.
- start a hosted playground/chat service as part of catalogue research.
- integrate ML to rank Free Pool candidates before its gates pass.

Expected output:
- Source-linked candidate inventory.
- Evidence/status per material claim.
- Catalogue-versus-runtime boundary diagram or concise explanation.
- Proposed metadata/data contract.
- Phased integration plan and acceptance criteria.
- Explicit unknowns and owner decisions.

============================================================
5. CONDITIONAL SKILLS — DO NOT INVOKE BY DEFAULT
============================================================

The owner supplied a large plugin/skill inventory.

Do not run the entire inventory indiscriminately.

Use these tools only when their documented purpose matches a concrete
need:

BROWSER / RESEARCH
- browse
- scrape
- connect-chrome
- open-gstack-browser
- setup-browser-cookies

Use only for authorized browser research or browser interaction.
Protect cookies and authenticated sessions.

PLANNING / SPECIALIZED REVIEW
- spec
- plan-devex-review
- cso
- plan-ceo-review
- plan-tune
- freeze
- unfreeze

Inspect the actual skill instructions before using any specialized
workflow. Do not infer behavior from a name alone.

DEPENDENCY / REFACTORING
- deslop-shared-libs

Use only when a specific dependency or maintainability problem has
been demonstrated. Do not perform a broad automated refactor on the
mixed worktree.

DEPLOYMENT / SHIPPING
- setup-deploy
- land-and-deploy
- ship

Do not invoke these for production deployment or release actions
without explicit owner authorization.

TOOLCHAIN MODIFICATION
- gstack-upgrade
- skillify
- superpowers:writing-skills
- claude-mem:mode-creator

Use only for a specifically authorized toolchain or skill-development
task.

MEMORY / REPORTING / COST WORKFLOWS
- claude-mem:agent-cost-report
- claude-mem:babysit
- claude-mem:ccs-align
- claude-mem:cloud-sync
- claude-mem:design-is
- claude-mem:do
- claude-mem:how-it-works
- claude-mem:knowledge-agent
- claude-mem:make-plan
- claude-mem:oh-my-issues
- claude-mem:version-bump
- claude-mem:weekly-digests
- claude-mem:what-the
- claude-mem:wowerpoint

Use only when the documented purpose directly matches the assignment.
Do not assume that memory/reporting skills are engineering reviewers.

VIDEO / MEDIA / PRESENTATION
- embedded-captions
- faceless-explainer
- general-video
- hyperframes
- hyperframes-animation
- hyperframes-audio
- hyperframes-cli
- hyperframes-core
- hyperframes-creative
- hyperframes-keyframes
- hyperframes-registry
- hyperframes-studio
- motion-graphics
- music-to-video
- pr-to-video
- product-launch-video
- remotion-to-hyperframes
- slideshow
- talking-head-recut
- make-pdf
- document-generate
- landing-report
- media-use

Do not invoke these for ordinary backend engineering.
Use them only for an explicit media, presentation, or artifact task.

iOS
- ios-clean
- ios-design-review
- ios-fix
- ios-qa
- ios-sync

Use only if an actual iOS application exists or the owner requests
iOS work.

PARALLEL WORK
- autoplan
- pair-agent
- codex
- superpowers:dispatching-parallel-agents
- superpowers:using-git-worktrees

Parallelize independent, preferably read-only investigations first.

Do not allow multiple agents to edit the same files concurrently.

The technical lead must reconcile the findings and own the final diff.

============================================================
6. ACTIVE INVESTIGATION — START WORK NOW
============================================================

The team charter is not the end of the task.

After the initial repository baseline and skill-availability check,
begin a comprehensive but controlled engineering investigation.

Do not wait for another user message to begin the authorized work.

Work through the following stages in order.

------------------------------------------------------------
STAGE 1 — CODEBASE AND ARCHITECTURE RECONNAISSANCE
------------------------------------------------------------

Inspect the project structure, entry points, configuration, tests,
documentation, runtime scripts, and dependency definitions.

Identify the actual implementations of:

- API startup and request handling.
- Configuration loading and validation.
- LiteLLM integration.
- Model/deployment registry.
- Virtual model or route resolution.
- Provider health monitoring.
- Capability filtering.
- Deterministic scoring.
- Fallback.
- Authentication and API-key handling.
- Rate limiting.
- Budgets and cost accounting.
- PostgreSQL persistence.
- Redis integration.
- Usage/request ledgers.
- Streaming and cancellation.
- Telemetry collection.
- Dataset audit and export.
- Operational/admin endpoints.
- Existing benchmark scripts.
- Any frontend or dashboard that actually exists.

Do not assume the expected file structure exists exactly as described
in prior handoffs.

Trace imports and call sites to verify actual integration.

For each component, classify it as:

- Implemented and integrated.
- Implemented but integration is unverified.
- Partially implemented.
- Test-only.
- Documentation-only.
- Missing.
- Unknown due to insufficient evidence.

Do not confuse roadmap intent with code.

Produce a concise architecture map and identify the highest-risk
mismatches.

------------------------------------------------------------
STAGE 2 — REQUEST-PATH AND DATA-FLOW AUDIT
------------------------------------------------------------

Trace a request through the actual code.

Check the ordering of:

Client request
  -> authentication and authorization
  -> request validation and admission
  -> rate limits and budgets
  -> classification and route resolution
  -> candidate discovery
  -> capability eligibility
  -> health eligibility
  -> deterministic selection
  -> LiteLLM execution
  -> fallback, if permitted
  -> response normalization
  -> usage/accounting
  -> telemetry persistence

This is the intended conceptual path. Confirm the real path in source.

Investigate whether:

- Security controls execute before provider calls.
- Invalid requests can consume provider resources.
- Fallback preserves policy and eligibility.
- Candidate selection can choose an ineligible deployment.
- Request identity survives retries and fallback.
- Streaming and non-streaming paths share consistent semantics.
- Error responses reflect the actual failure.
- Usage accounting occurs at the correct lifecycle point.
- Telemetry reflects decision-time facts rather than later state.
- Concurrent requests can race through budgets, rate limits, or
  persistence.
- Exceptions can bypass cleanup or finalization.
- Duplicate operations can create double accounting.
- Provider success can be mistaken for successful telemetry persistence.
- The code can return success while required security or accounting
  controls failed.

Create a short list of concrete findings backed by file references,
tests, or reproducible behavior.

Do not implement fixes until the evidence and intended invariant are
clear.

------------------------------------------------------------
STAGE 3 — SECURITY REVIEW
------------------------------------------------------------

Conduct an independent security review of the actual code and
configuration boundaries.

Inspect authentication, authorization, key lifecycle, secrets,
logging, input validation, network/provider boundaries, rate limits,
budgets, persistence, exports, and administrative operations.

Prioritize findings by demonstrated impact and exploitability.

For every finding:
- Identify the affected path.
- Explain the violated invariant.
- Show supporting evidence.
- State whether the finding is confirmed or hypothetical.
- Identify a minimal remediation.
- Identify a regression test.

Fix confirmed, in-scope defects when the correction is safe and
reviewable.

Do not run destructive penetration tests, external scans, or
unauthorized tests against production services.

Do not expose secrets in reports.

------------------------------------------------------------
STAGE 4 — FAILURE, ACCOUNTING, AND TELEMETRY AUDIT
------------------------------------------------------------

Review failure semantics across the application.

At minimum, distinguish:

1. Request validation failure.
2. Authentication or authorization failure.
3. Admission/rate-limit/budget rejection.
4. No eligible deployment.
5. Provider failure.
6. Fallback attempt.
7. Client cancellation.
8. Streaming interruption.
9. Internal application error.
10. Persistence/finalization failure.
11. Successful provider response with incomplete telemetry.
12. Duplicate or inconsistent accounting events.

Verify that the implementation does not collapse these into misleading
success/failure labels.

For telemetry, verify:

- A logical request has a consistent identity.
- Each selected attempt has one corresponding pre-routing snapshot.
- The snapshot is persisted before provider execution.
- Each handled attempt has one matching outcome.
- Attempt numbers are sequential.
- Fallback attempts share the correct logical request identity.
- Deployment eligibility is recorded accurately.
- Unselected candidates receive no invented outcomes.
- Finalization validates pairing and schema requirements.
- Incomplete persistence remains detectable.
- Streaming cleanup cannot silently bypass required finalization.
- Client cancellation is not misclassified as provider failure.
- Persistence failure is not misclassified as provider failure.
- Sensitive content and secrets are not leaked in telemetry.
- Legacy records remain distinguishable from verified new-schema data.

Pay particular attention to the existing Phase 13 telemetry work and
its latest reported regression around naive decision timestamps being
counted as verified temporal provenance.

Verify the actual current code and tests rather than assuming that
the last reported fix is present.

Do not modify historical database rows.

Do not attempt to reconstruct Record E.

------------------------------------------------------------
STAGE 5 — DATASET READINESS AND ML BOUNDARIES
------------------------------------------------------------

Inspect the actual dataset audit and export implementation.

The previous reported database findings were:

- 7 logical requests.
- 6 provider attempts.
- 5 feature snapshots.
- 6 outcomes.
- One outcome without a matching feature snapshot.
- Record E was the unmatched successful sabiroute-groq attempt.
- Two attempts had verified temporal provenance.
- Four attempts had unknown or unavailable provenance.
- All six outcomes were successes.
- No defensible chronological split was available.
- Actual-cost observations were absent.
- Dataset readiness was BLOCKED.
- training_authorized was false.

A later code-level change reportedly corrected aggregate reporting so
that a schema 1.1 attempt with a naive decision timestamp could not
increase the verified-provenance count.

These are historical findings, not a current database snapshot.

Do not claim that current counts remain the same unless a fresh,
authorized audit establishes that fact.

Verify:
- Feature/outcome linkage.
- Schema-version handling.
- Missing schema behavior.
- Temporal provenance.
- Timestamp ordering and timezone handling.
- Candidate and deployment eligibility.
- Legacy-record quarantine.
- Diagnostic export behavior.
- Secret redaction.
- Aggregate readiness consistency.
- Chronological split eligibility.
- Outcome variation.
- Selection-bias reporting.
- Actual-cost availability.
- Training authorization.

Do not run a database audit automatically if the current task or
environment does not authorize it.

Do not modify live records, run migrations, reset databases, or
backfill telemetry.

If a fresh read-only audit is appropriate and can be run safely using
the existing documented procedure, do so only when the environment
permits it and the task scope authorizes it.

If database access fails with an environment restriction, report
the exact failure. Do not infer that PostgreSQL is down.

Do not train a model.

Do not change routing behavior.

Phase 13.3 remains blocked until trustworthy data, meaningful outcome
variation, defensible evaluation, selection-bias treatment, justified
labels/metrics, and human approval exist.

------------------------------------------------------------
STAGE 6 — TEST AND QUALITY AUDIT
------------------------------------------------------------

Review both the test suite and what it fails to cover.

Check:
- Test naming and intent.
- Assertion quality.
- Failure-path coverage.
- Fixture reliability.
- Mock boundaries.
- SQLite versus PostgreSQL assumptions.
- Redis integration assumptions.
- Streaming/cancellation tests.
- Authentication and authorization tests.
- Rate-limit/budget tests.
- Concurrency-sensitive accounting.
- Dataset linkage and timestamp tests.
- Regression coverage for previously fixed defects.
- Tests that pass without exercising the intended path.
- Tests that accidentally depend on local machine state.
- Tests that hide exceptions or weaken behavior.

Run the focused tests relevant to each confirmed defect.

Then run the full documented test suite and applicable static checks:
- Pytest.
- Ruff.
- Strict mypy.
- git diff --check.

Run integration tests only where their prerequisites and permissions
are available.

For browser-facing functionality, use Playwright when relevant and
available.

Do not claim a check passed if it was skipped, blocked, or not run.

If a defect is found, add a focused regression test before or alongside
the fix where practical.

------------------------------------------------------------
STAGE 7 — APPLY SAFE, EVIDENCE-BASED CORRECTIONS
------------------------------------------------------------

After the investigation stages establish concrete findings, begin
correcting defects that fall within the authorized scope.

Do not stop at a report if there are clearly demonstrated, safely
correctable defects.

For each correction:

1. State the defect and expected invariant.
2. Confirm the evidence.
3. Identify the smallest affected file set.
4. Add or update a regression test.
5. Implement the smallest justified fix.
6. Run focused tests.
7. Run related tests.
8. Review the actual diff.
9. Ask the independent reviewer to inspect the change.
10. Run broader checks.
11. Record remaining limitations.

Prioritize:
- Security bypasses.
- Incorrect eligibility.
- Incorrect accounting.
- Broken request lifecycle invariants.
- Data-integrity defects.
- Missing regression tests for demonstrated failures.
- Configuration validation errors.
- Incorrect error handling.
- Integration defects.
- Misleading operational reporting.
- Documentation that directly causes unsafe operation.

Do not automatically fix every style preference or speculative concern.

Do not refactor unrelated modules.

Do not add dependencies without a demonstrated requirement.

Do not change the deterministic scoring formula.

Do not start Phase 13.3.

Do not introduce ML inference.

Do not manufacture telemetry or benchmark results.

If a correction requires a migration, provider configuration change,
security-policy decision, production data repair, external spend,
or other action outside the authorized boundary, prepare the proposed
change and stop for owner approval.

------------------------------------------------------------
STAGE 8 — INDEPENDENT REVIEW OF THE ACTUAL DIFF
------------------------------------------------------------

After the implementation work, run a review that is independent of
the implementation agent.

Use the available code-review and security-review skills.

Inspect the actual Git diff, not merely the implementer's summary.

Ask:

- Does the fix solve the demonstrated defect?
- Does it preserve the architecture?
- Could it introduce a regression?
- Are all error paths handled?
- Are failure and accounting semantics still correct?
- Are secrets protected?
- Are tests meaningful?
- Are compatibility contracts preserved?
- Are there unnecessary changes?
- Are comments and documentation accurate?
- Does the evidence justify the completion claim?

Fix additional confirmed defects within scope.

If reviewers disagree, resolve the disagreement using code, tests,
and reproducible evidence rather than authority or guesswork.

No implementation agent may approve its own change solely on its
own assertion.

------------------------------------------------------------
STAGE 9 — CONDITIONAL FRONTEND AND PRODUCT DESIGN REVIEW
------------------------------------------------------------

Only activate this stage if a real UI-facing defect or explicit UI
requirement is discovered.

If activated:

1. Inspect the existing frontend architecture and dependencies.
2. Verify the availability of UI UX Pro Max.
3. If available, use it for structured design-system guidance.
4. Use Frontend Design for implementation-oriented visual polish.
5. Use Design Taste for distinctive, deliberate visual decisions.
6. Use Design Motion Principles for purposeful, accessible transitions.
7. Use Apple Design only when the target platform warrants it.
8. Use Playwright for browser-level verification.

Do not build an unsolicited dashboard simply because the project may
eventually benefit from one.

Potential dashboard capabilities include:
- Provider health.
- Routing decision explanations.
- Fallback events.
- Latency and performance.
- Usage and costs.
- Routing configuration.
- Operational visibility.

These are possible product capabilities, not claims of current
implementation.

Any UI must present actuals, estimates, unknowns, and unavailable data
honestly.

Do not create a beautiful interface that misrepresents system state.

------------------------------------------------------------
STAGE 10 — FREE POOL DISCOVERY AND INTEGRATION DESIGN
------------------------------------------------------------

This stage is authorized for research, source-linked catalogue
preparation, architecture analysis, and a proposed implementation plan.
It is NOT authorization to change runtime routing, configure new live
providers, spend provider credits, or launch shared hosted inference.

The approved core Git sequence (C1–C11) is complete — see RULE 5. Do
not repeat it, and do not mix new Free Pool runtime implementation into
it. The owner-authored provider-harness changes are already preserved as
C11. Free Pool research may be conducted read-only, provided no agent
edits the same files or creates conflicting worktree changes.

Research the initial candidate pool using official provider/model
documentation and terms. For each candidate, record:

- Provider and exact model identifier.
- Official source URL(s) and date checked.
- Access mode: BYOK, platform-managed, local, or other.
- Published free allowance, cadence, conditions, and restrictions.
- Request/token limits and whether quota is shared with other models.
- Geographic/account/verification eligibility.
- Capability evidence and unsupported/unknown capabilities.
- Whether the model is listed only, configured in SabiRoute, access
  verified for the relevant arrangement, and/or runtime-probed.
- Terms/permissions relevant to the intended use.
- Evidence freshness and confidence.
- Unknowns that must not be inferred.

Use official documentation as the primary source. If a fact cannot be
verified, mark it unknown and retain the source/search trail. Community
posts may identify leads but do not override official terms.

Produce a catalogue that separates:
1. Published allowance.
2. Configured/accessible allowance for a specific access arrangement.
3. Estimated aggregate capacity, with explicit assumptions and shared
   quota-pool deduplication.
4. Observed consumption.
5. Current runtime health.

Do not add allowances across models that share a quota pool. Do not
infer token quotas from request-rate limits. Do not describe a one-time
credit as a recurring free tier. Do not call a model "usable through
SabiRoute" unless a configured, eligible route exists for the relevant
access arrangement.

Define a proposed metadata/data contract and explain how a catalogue
entry maps to (but remains distinct from) the existing runtime
deployment registry. Reuse existing provider, capability, health, and
routing abstractions where appropriate; do not introduce a second
router or source of truth.

Map work to the existing roadmap:
- Initial research/catalogue/data contract can proceed now.
- Runtime integration requires architecture review, focused tests, and
  owner approval if it changes routing/security policy or provider
  configuration.
- A static/read-only catalogue may precede a live website.
- Live availability claims require an actual, trustworthy runtime
  source.
- A shared playground/chat service is future work and requires explicit
  security, terms, quota/budget, abuse, privacy, cost, observability,
  and operations acceptance.
- ML remains independently blocked by the Phase 13 dataset/evaluation
  gates. Free Pool is not a reason to train or integrate a selector.

If safe and useful, prepare `docs/free-pool-architecture-proposal.md`
only after confirming that the path does not already contain owner
work. Keep it as a proposed, uncommitted artifact for owner review.
Do not modify an existing file of the same name without inspecting it.
Do not add new provider runtime configuration or credentials in this
overnight task.

------------------------------------------------------------
STAGE 11 — DEVELOPER EXPERIENCE AND DOCUMENTATION CORRECTIONS
------------------------------------------------------------

Inspect the documentation that directly governs the code being
changed.

Correct demonstrably inaccurate:
- Setup instructions.
- Test commands.
- Environment-variable documentation.
- Architecture descriptions.
- Error-handling instructions.
- Operational runbooks.
- Phase status claims.
- Dataset-readiness claims.

Do not rewrite every document for consistency of style.

Do not create duplicate handbooks.

Preserve historical context where useful.

Keep implemented functionality separate from roadmap intentions.

If Brag or existing project summaries omit critical architectural
context, tests, limitations, or the actual reason a change matters,
correct the relevant summary when it is within scope.

Use one appropriate Brag entry point.

Do not invent completed work to improve the presentation.

------------------------------------------------------------
STAGE 12 — FINAL VERIFICATION
------------------------------------------------------------

Before declaring any work complete:

1. Inspect every changed file.
2. Inspect the full diff.
3. Check for secrets or sensitive data in changed files and logs.
4. Confirm protected files remain unchanged.
5. Confirm no unrelated files were modified.
6. Run relevant focused tests.
7. Run the full test suite where feasible.
8. Run Ruff.
9. Run strict mypy.
10. Run git diff --check.
11. Run relevant integration/browser tests where available.
12. Confirm the actual working-tree status.
13. Confirm that any staging or commit performed during this run was
    explicitly authorized, that the completed C1–C11 sequence was not
    amended or rewritten, and that no new push or deployment occurred.
    The branch was already pushed before this run; a further push
    requires a fresh owner decision.
14. Map each acceptance criterion to evidence.
15. List every unverified behavior and owner decision.
16. Report the disposition of the owner-authored provider-harness work.
17. Report the Free Pool research findings separately from implemented
    gateway functionality.

If a command cannot run, report why.

If a test fails, investigate it. Do not hide it or weaken it.

If an environment restriction prevents a live check, mark that check
BLOCKED or NOT VERIFIED.

Do not claim the application is production-ready based solely on
automated tests.

============================================================
7. OVERNIGHT / AUTONOMOUS OPERATING BOUNDARIES
============================================================

The owner intends to leave the laptop running for an extended period.

Continue working on the authorized investigation and safe corrections
without requiring approval for every small, reversible code change.

However, stop for owner judgment when a decision crosses any of these
boundaries:

- Destructive filesystem operations.
- Database data mutation or recovery.
- Schema migrations that affect persistent data.
- Restoring backups or replaying WAL.
- Production deployment.
- Any push or history rewriting.
- Any commit at all. The owner-approved sequence C1–C11 is complete;
  every new commit requires fresh, explicit owner authorization.
- Any change to the owner-authored `--max-tokens` feature. It has
  already landed as C11 and must not be amended, extended, re-committed,
  or absorbed into another commit.
- External provider spending.
- Unapproved provider requests.
- Credential changes.
- Security-policy changes.
- Routing-policy changes.
- Dependency changes with significant compatibility risk.
- Changes to .env or secret-bearing configuration.
- Model training while the dataset gate remains blocked.
- ML inference or selector integration.
- New provider credentials/configuration or live provider execution
  without explicit authorization.
- Shared hosted inference, public playground/chat launch, or new
  monetary exposure.
- Unresolved product or security tradeoffs.
- Any action that could irreversibly damage existing work.

Do not use broad cleanup commands.

Do not kill unrelated user processes.

Do not assume an inaccessible service is down.

Do not leave a partially applied change in a confusing state.

If blocked:
- Preserve the current state.
- Document the blocker.
- Identify the exact decision or permission required.
- Continue with independent safe work if possible.

Do not send fabricated progress messages.

Do not run endless loops or repeat checks without a reason.

Use a bounded investigation plan, maintain checkpoints, and stop when
the authorized work is complete or blocked by a genuine boundary.

============================================================
8. DEFINITION OF DONE
============================================================

The assignment is complete when the team has:

1. Inspected the actual repository baseline.
2. Verified the availability of relevant skills.
3. Mapped the actual architecture and request path.
4. Completed the relevant code-quality and security investigations.
5. Investigated failure and accounting semantics.
6. Reviewed dataset and ML safety boundaries.
7. Identified concrete defects with supporting evidence.
8. Corrected safely fixable, in-scope defects.
9. Added meaningful regression coverage.
10. Run applicable tests and static checks.
11. Conducted an independent review of the resulting diff.
12. Checked relevant documentation.
13. Preserved all owner-authored work and protected paths.
14. Created no commit beyond the completed C1–C11 sequence without
    fresh owner authorization; applied exact staged-diff review and test
    evidence to any commit that was made; pushed nothing. The branch was
    already pushed and synchronized before this run.
15. Produced an accurate final report with unresolved issues.
16. Produced a source-linked Free Pool research/design result without
    misrepresenting it as runtime integration.
17. Identified the single highest-priority next action.

Do not define success as:
- The number of files changed.
- The number of agents invoked.
- The number of skills used.
- The number of lines added.
- A green test suite without meaningful coverage.
- A visually impressive report.
- A claimed phase completion without evidence.

============================================================
9. REQUIRED FINAL ENGINEERING REPORT
============================================================

Return a detailed but evidence-based report with these sections:

A. EXECUTIVE FINDING
- Overall result.
- Highest-risk findings.
- What was corrected.
- What remains blocked.

B. INITIAL REPOSITORY BASELINE
- Actual project path.
- Branch and HEAD.
- Staged, modified, and untracked state.
- Protected files.
- Available tools and relevant unavailable skills.

C. ARCHITECTURE AND REQUEST-PATH REVIEW
- Actual request flow.
- Ownership boundaries.
- Integration gaps.
- State and failure transitions.
- Evidence and limitations.

D. CODE-QUALITY FINDINGS
For each finding:
- Severity.
- File and line reference.
- Evidence.
- Root cause, if established.
- Correction or recommendation.
- Test coverage.

E. SECURITY REVIEW
- Confirmed findings.
- Potential risks requiring more evidence.
- Fixes made.
- Remaining concerns.

F. FAILURE AND ACCOUNTING SEMANTICS
- Provider failure.
- Fallback.
- Cancellation.
- Streaming.
- Persistence.
- Rate limits and budgets.
- Usage/cost accounting.
- Telemetry integrity.

G. DATASET AND ML GATES
- What was inspected.
- What is verified.
- What remains unknown.
- Current authorization status.
- Why downstream phases remain blocked.

H. FILES CHANGED
- Exact paths.
- Reason for each change.
- Tests associated with each change.

I. VERIFICATION RESULTS
- Exact commands.
- Exit status.
- Test counts.
- Ruff.
- Strict mypy.
- git diff --check.
- Integration/browser evidence.
- Checks blocked or not run.

J. ARCHITECTURE AND RELIABILITY IMPACT
- Invariants preserved.
- Risks reduced.
- Remaining operational limitations.
- Compatibility considerations.

K. PHASE STATUS
Distinguish implementation, test, runtime, acceptance, and production
readiness.

L. GIT AND REPOSITORY SAFETY
- Final branch and HEAD.
- Final working-tree status.
- Confirm no unauthorized staging or commits.
- Confirm protected files were preserved.

M. UNRESOLVED FINDINGS
- What remains.
- Why it was not changed.
- What evidence or authorization is needed.

N. SINGLE HIGHEST-PRIORITY NEXT ACTION
- Exact next action.
- Why it comes first.
- Evidence required to proceed.

O. GIT COMMIT SEQUENCE
- Record C1–C11 as landed, with both their original and post-rewrite
  SHAs (see RULE 5) and the two backup refs that preserve the original
  history.
- Record the staged file lists and checks used for C7–C11 under the
  owner's existing authorization, plus C11 for the owner-authored
  provider-harness feature.
- Record that the branch was pushed and is in sync with origin
  (0 ahead, 0 behind). Report the push as a completed fact; obtain a
  fresh owner decision before any further push.
- Report the history-rewrite condition: `feat` and `main` share no
  common commit object, and `HEAD` carries 0 signed commits of 22 after
  the cleanup. Both are disclosed risks, not defects to repair — do not
  rewrite history to correct them.
- Confirm the backup refs were preserved and that no branch, ref, or
  backup was created, moved, or deleted during the run.

P. FREE POOL FINDINGS AND ROADMAP
- Candidate inventory with official source URLs and date checked.
- BYOK/platform-managed/local access distinctions.
- Published versus configured versus observed capacity.
- Shared quota-pool deduplication and unknowns.
- Catalogue/runtime-registry/routing-engine boundaries.
- Proposed metadata contract and integration stages.
- What was researched versus what was actually implemented.
- Security, terms, cost, abuse, privacy, and operational gates for
  future shared hosted inference.

Q. NEXT ACTIONS
- One highest-priority gateway action.
- One highest-priority Free Pool action.
- Exact evidence or owner decision needed for each.

============================================================
10. FINAL ORDER
============================================================

The team is mobilized.

Start with repository inspection and skill verification.

Then conduct the independent investigations, reconcile the evidence,
correct demonstrated and safely fixable defects, test the changes,
review the actual diff, and document the results.

Continue through the authorized work rather than stopping after
producing a plan.

Keep changes minimal, intentional, and reviewable.

Protect the existing project.

Do not fabricate evidence.

Do not weaken tests.

Do not change the deterministic-v1 routing formula.

Do not train or integrate ML while its acceptance gates remain blocked.

Do not deploy, push, mutate production data, or incur unapproved
external spend. The approved commit sequence C1–C11 is complete and has
already been pushed; do not repeat it, and do not push again without a
fresh owner decision. Create no additional commit without explicit
owner approval.

Leave SabiRoute in a more reliable and better-understood state than
you found it.

The standard is not "the agent says it is done."

The standard is evidence that the work is correct, integrated,
tested, and honestly reported.