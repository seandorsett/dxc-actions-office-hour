# Presenter demo guide

Delivery: October 13, 2026. Selected catalog IDs: 1, 2, 7, 8, 9.
The live segment ends at minute 50, followed by 10 minutes of Q&A.

## Rehearsal and preparation

Publish this package to the default branch of a restricted demo repository.
Use the README for credentials/environment setup and run **Validate Office Hour
package**. GitHub workflows must be rehearsed after publication; local tests
cannot establish service enforcement.

Seed the artifact-expiry workflow immediately after publication, preferably
October 10-11. Record the seed run ID and actual expiry. Rehearse inspection
after natural expiration and cleanup, no later than October 12 if possible.
Keep a successful seed run and inspect run open in browser tabs.

Launch cache/reporting/audit workflows before their segments if queues are
slow. Keep administrative changes scoped to the disposable repository. If a
demo is unavailable, state the blocker and use real, clearly identified
rehearsal evidence; do not invent successful results.

## Demo 1: Cache least privilege and reusable-workflow ceiling

**WOW moment:** The called workflow asks for write access, yet the caller's
`read` setting still prevents a cache save. A green cache step alone would
hide that distinction.

**Prerequisites:** github.com, Actions enabled, pinned first-party actions
allowed, ordinary hosted Ubuntu runners. No administrator secret is needed.

**Workflow:** `.github/workflows/demo-1-cache-modes.yml`.  
**Companion scripts:** `scripts/cache_probe.py`, `scripts/demo_api.py`.

1. Open the workflow YAML and its reusable helper.

   > **Say this:** "We are setting a service-enforced cache boundary, not
   > relying on developers to remember which save steps they should omit.
   > Notice that the caller chooses each mode while the called workflow asks
   > for write. The called workflow cannot elevate beyond its caller."

2. Select **Actions > Demo 1 - Cache least privilege > Run workflow**.
   Use the default branch. Explain the one seed, four parallel probes, and
   one independent verifier.

   > **Say this:** "These caches contain only a harmless marker. Unique
   > run-specific keys prevent yesterday's cache from making today's result
   > look successful. We assert the restored content rather than guessing
   > from step color."

3. Open the `read`, `write`, `write-only`, and `none` probe summaries. Then
   open the verifier summary and its `cache-mode-evidence` artifact.

   > **Say this:** "Read restores but cannot save. Write does both.
   > Write-only saves without restoring. None does neither. The verifier
   > queries the actual service inventory after the probes finish. This is
   > the evidence that the permission ceiling really affected saves."

4. Show the security caveat: explicitly granting writes on a low-trust event
   can override secure defaults. Do not introduce unsafe PR checkout code.

   > **Say this:** "This control helps only when our chosen trust boundary
   > is correct. We should not add write access to an untrusted trigger
   > simply to make a pipeline warning disappear."

**Troubleshooting**

| Symptom | Likely cause | Presenter action |
| --- | --- | --- |
| Workflow rejected before execution | Account/server lacks current syntax or actions are disallowed | Confirm github.com support and allowlisted pins; use a real rehearsal run |
| Save verifier mismatch | Service delay, failed seed, or stale implementation | Read probe logs and retry a new run; do not infer success from green save steps |
| Runner jobs queue beyond the budget | Hosted capacity/billing limits | Show the successful rehearsal run with its date clearly stated |

**Cleanup:** Optional; delete only cache entries matching the rehearsal's
`dxc-oh-RUN_ID-RUN_ATTEMPT` prefix in the repository cache UI.

**Transition:** "We have limited what a running job can do with its cache.
Next, we control whether a workflow is allowed to run at all."

## Demo 2: Execution policy scoped to one workflow

**WOW moment:** The same harmless YAML can execute for manual dispatch while
the central policy blocks its repository-dispatch trigger, without affecting
the control workflow.

**Prerequisites:** Disposable repository, `demo-admin` environment, approved
`DEMO_POLICY_ADMIN_TOKEN`, default branch. Enterprise Cloud is required only
for evaluate mode. Review inherited policies first.

**Workflows:** `.github/workflows/demo-2-policy-control.yml` and
`.github/workflows/demo-2-policy-target.yml`.  
**Companion script:** `scripts/demo_api.py`.

1. Run the control workflow with `operation=inspect`. If supported, create
   with `create-evaluate`; otherwise use `create-active`. Record the returned
   policy ID from the summary.

   > **Say this:** "The policy is narrowly targeted to this single demo
   > file. Our control workflow remains outside its scope, so we retain a
   > recovery path. Existing organization and enterprise policies still
   > apply. Evaluate lets us see impact before enforcing where our plan
   > supports it."

2. Run `probe-allowed` and `probe-blocked`. Find their generated probe labels
   in the target workflow and inspect Policy insights. In evaluate mode the
   disallowed event can still execute while recording the would-block result.

   > **Say this:** "An accepted API call means GitHub received the request;
   > it is not proof that the job ran. We must inspect the actual target
   > execution and policy evaluation."

3. If the policy is in evaluate mode, run `activate` with its ID. Repeat the
   probes. Show the actual error for the repository-dispatch attempt and the
   permitted manual execution.

   > **Say this:** "Now the rule is active. We have separated a permitted
   > event from a disallowed event without editing the protected workflow.
   > This is centrally enforced policy rather than a shell if statement."

4. Run `cleanup` with that same policy ID. Inspect again if needed.

   > **Say this:** "Cleanup removes only this demo-created, file-scoped
   > policy. We never remove a production or inherited policy to make a
   > demonstration work."

**Troubleshooting**

| Symptom | Likely cause | Presenter action |
| --- | --- | --- |
| HTTP 403/404 | Credential, administrator role, SSO, or account capability | Verify approved access; never fall back silently to a different credential |
| Evaluate rejected | Enterprise Cloud evaluate entitlement unavailable | Create active only in the disposable repository, or explain rather than simulate |
| Both probes fail or allowed probe cannot run | Inherited policy/event restriction | Inspect inherited policies; do not weaken them for the session |
| Blocked API request accepted but target result not yet visible | Dispatch acceptance precedes asynchronous evaluation | Open target Actions/insights and wait briefly; switch to genuine rehearsal evidence |

**Cleanup:** Control workflow, `operation=cleanup`, using the recorded ID.
Deletion refuses policies with a different name prefix or target scope.

**Transition:** "Policy protects execution. Operational evidence still has
a lifecycle, and that lifecycle now affects what the UI and API show us."

## Demo 3: Real artifact expiry with retained provenance

**WOW moment:** The expired target disappears, but its separately retained
receipt still proves which artifact existed and when it was due to expire.

**Prerequisites:** Successful seed created at least a day earlier, actual
expiry already passed, service cleanup completed, receipt still within its
14-day retention, seed logs/run still retained. Do not manually delete the
target artifact.

**Workflow:** `.github/workflows/demo-3-artifact-expiry.yml`.  
**Companion script:** `scripts/demo_api.py`.

1. Show the earlier seed run, including the one-day upload and retained
   receipt. Identify the target name, ID, `created_at`, and `expires_at`.

   > **Say this:** "The seed was run before today's session because natural
   > expiration is not instantaneous. This receipt comes from GitHub's
   > artifact API after a successful upload. The receipt has separate,
   > longer retention than the target."

2. Run the workflow with `operation=inspect` and the successful seed run ID.
   Open the observation summary once it finishes.

   > **Say this:** "The inspector first checks the original expiry, then
   > asks both the run's artifact-list endpoint and the artifact's direct
   > GET endpoint. It will report not ready rather than pretend a still
   > visible artifact has disappeared."

3. Show list absence and direct GET 404 alongside the retained receipt and
   original upload logs. Explain attribution honestly.

   > **Say this:** "This result is consistent with natural expiry because
   > we deliberately did not delete the artifact. Absence alone cannot
   > distinguish expiry from manual deletion. The change removes stale
   > UI/API entries; it does not introduce a new retention or billing rule."

4. Connect to DXC integration design: handle absence, preserve needed evidence
   under an approved policy, and do not make billing assertions from UI pills.

   > **Say this:** "An integration should tolerate the record being absent.
   > If a delivery or audit process needs longer-lived evidence, retention
   > and archival need to be designed explicitly."

**Troubleshooting**

| Symptom | Likely cause | Presenter action |
| --- | --- | --- |
| NOT READY before expiry | Seed too recent or actual expiry later than expected | Use an older genuine seed; do not shorten the clock in code |
| NOT READY after expiry | Asynchronous service cleanup has not finished | Rehearse later or show previously captured natural-expiry evidence |
| Receipt download fails | Wrong seed ID, missing seed completion, or receipt retention passed | Use the recorded successful seed ID; prepare another seed |
| Artifact GET is 403 | Permission issue, not proof of expiry | Fix Actions read access; do not label a forbidden response expired |

**Cleanup:** Allow natural expiry. Receipts expire after 14 days; reports after
7 days. Retention caps can shorten these windows.

**Transition:** "An absent record is one reporting challenge. A large query
returning a bounded count is another."

## Demo 4: Bounded reporting without false completeness

**WOW moment:** The client treats a bounded count and the filtered retrieval
cap as different concerns, splitting time windows before the 1,000-record cap.

**Prerequisites:** At least a few workflow/rehearsal runs in the demo
repository, Actions read permission, explicit UTC dates. A true live 2,500+
count demonstration additionally needs a high-volume repository; this package
does not generate thousands of paid runs.

**Workflow:** `.github/workflows/demo-4-bounded-reporting.yml`.  
**Companion script:** `scripts/demo_api.py`.  
**Offline fixtures:** `tests/test_demo_api.py`.

1. Run reporting with dates covering the seed/rehearsals and `per_page=2`.
   Show the `created` filter and request/page handling in the script.

   > **Say this:** "Two items per page makes pagination visible in this
   > small repository. The production-friendly setting is 100 items per
   > page with appropriately bounded date ranges."

2. Open the summary and downloaded JSON. Show distinct run IDs, actual
   returned counts, requests, and whether splitting was actually needed.

   > **Say this:** "This is live data from our demo repository. If the
   > summary says no large count was observed, we have not demonstrated
   > the 2,500-plus threshold here. We have demonstrated the reporting
   > pattern and ordinary pagination."

3. Explain the offline large-count unit test, clearly identifying it as a
   synthetic response fixture. Show how it creates adjacent UTC windows
   without gaps/overlap and stops rather than silently truncating.

   > **Say this:** "This test is a simulation of a bounded response, not
   > live GitHub behavior. Counts above 2,500 become bounded, while a
   > filtered query can return at most 1,000 records. More pages do not
   > remove that cap; smaller time windows do."

**Troubleshooting**

| Symptom | Likely cause | Presenter action |
| --- | --- | --- |
| Zero runs | Dates do not cover publication/rehearsal | Set inclusive UTC dates that include the demo runs |
| Request budget reached | Page size too small for volume or overly broad date range | Use page size 100 and narrower dates |
| Saturated minimum window | More than the cap in one second or unstable response | State completeness is unresolved; narrow further using additional API filters outside this demo |
| Count differs while inspecting | API is not an atomic snapshot | Explain concurrent creation/deletion and record observation time |

**Cleanup:** No API data was changed; report artifacts expire after 7 days.

**Transition:** "Our final operational example also favors explicit service
data over assumptions: runner upgrade deadlines."

## Demo 5: Separate runner registration and runtime readiness

**WOW moment:** A version can pass a registration threshold while still
failing the higher requirement for executing jobs.

**Prerequisites:** Approved `RUNNER_READ_TOKEN` in `demo-admin`, administrator
identity where required, default branch. Organization scope additionally needs
`RUNNER_AUDIT_ORG` and appropriate organization runner permissions. A real
inventory is optional.

**Workflow:** `.github/workflows/demo-5-runner-readiness.yml`.  
**Companion script:** `scripts/demo_api.py`.

1. Run repository scope with the default explicit version list and inventory
   disabled. Explain that the job itself runs on a hosted runner.

   > **Say this:** "We do not need to downgrade a customer runner to
   > inspect the enforcement dates. This is a read-only API lookup for
   > explicit versions."

2. Open the report. Compare registration and runtime dates independently.
   Treat null values as unknown, not supported.

   > **Say this:** "Two-point-three-two-nine-zero is the registration
   > minimum in the announcement, not the runtime minimum. We look at
   > both dates. No date returned is not a blanket support guarantee."

3. If approved and rehearsed, repeat with inventory enabled to add visible
   fleet versions. Highlight unknown versions separately.

   > **Say this:** "When we include a real inventory, missing version
   > information stays visible as a data-quality issue. This audit does
   > not stop, upgrade, register, or remove any runner."

**Troubleshooting**

| Symptom | Likely cause | Presenter action |
| --- | --- | --- |
| Missing credential or HTTP 403 | Default token cannot access runner administration | Supply approved read-scoped runner credential |
| Deprecation endpoint 404 | Account scope, authorization, capability, or unknown version | Confirm access and exact version; do not invent deadlines |
| Empty fleet or null versions | No visible self-hosted runners or incomplete metadata | Present explicit-version lookups and label inventory limitations |

**Cleanup:** No fleet changes were made. Remove/revoke the temporary
read credential and let the report artifact expire.

**Transition:** "We can now turn these five updates into a concrete DXC
adoption checklist and hand the final ten minutes over to questions."

## Hard stop and fallback

At minute 45, stop starting new jobs. Use minutes 45-50 for actions/takeaways and buffer.
At minute 50, switch to Q&A even if a workflow is still queued.

Fallback narration:

> "This live prerequisite is not available in our current demo environment.
> Here is the successful rehearsal run and its timestamp, or the configuration
> we would use. I will distinguish observed evidence from examples."

Do not present synthetic fixtures, an HTTP acceptance response, manual artifact
deletion, or a green cache step as proof of the corresponding released feature.
