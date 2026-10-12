# DXC GitHub Actions Office Hour: update selection

Session date: October 13, 2026  
Research cutoff: October 9, 2026  
Publication window: September 10 through October 9, 2026, inclusive  
Format: 50 minutes of presentation and demonstrations, followed by 10 minutes of Q&A  
Presentation template: `Session Presentation Deck Template.pptx`

## Research scope and evidence

The twelve entries below were verified against the official GitHub Actions
changelog RSS feed and their individual announcements. Feed page 1 contains ten
entries in the window. Feed page 2 contains the remaining two September 10
entries, followed by September 3 content outside the window. No later
Actions-tagged entry than October 2 was present in the feeds when researched.

- [Official Actions changelog](https://github.blog/changelog/label/actions/)
- [Actions RSS feed, page 1](https://github.blog/changelog/label/actions/feed/)
- [Actions RSS feed, page 2](https://github.blog/changelog/label/actions/feed/?paged=2)

This is a publication-date selection, not an assertion that every entry is a
new feature or that every announced migration has already happened. General
availability, public preview, behavior changes, enforcement notices, and future
retirement announcements are distinguished below. GitHub Enterprise Server
availability must not be inferred from a github.com announcement.

Demo feasibility is a design assessment, not a claim of successful execution.
After selection, the package was built for catalog IDs **1, 2, 7, 8, and 9**
and published at the user's request to the private repository
[seandorsett/dxc-actions-office-hour](https://github.com/seandorsett/dxc-actions-office-hour).
No GitHub demonstration has been live-run during preparation; rehearsal remains
required.

## Selection summary

| ID | Published | Update | Status at research cutoff | Demoable? | Proposed GitHub-hosted demonstration |
| --- | --- | --- | --- | --- | --- |
| 1 | Sep 10 | Cache access control with `cache-mode` | Generally available on all github.com plans | Yes: workflow-native | Seed a cache, then contrast restore/save behavior under `read`, `write`, `write-only`, and `none`; show reusable-workflow permission ceilings. |
| 2 | Sep 17 | Workflow execution protections | Generally available; evaluate mode requires Enterprise Cloud | Yes: conditional on administrator access | Target a harmless workflow with an event allowlist; compare permitted CI and blocked manual dispatch; show insights and policy-as-code REST calls. |
| 3 | Sep 17 | Ubuntu 26.04 runner images | Generally available; `ubuntu-latest` migration is still upcoming | Yes: workflow-native | Run the same smoke test on Ubuntu 24.04 and 26.04, report actual image/tool versions, and explain explicit image pinning. |
| 4 | Sep 23 | JavaScript actions move from Node 20 to Node 24 | Node 20 action runtime retired; old opt-out removed | Yes: workflow-native | Execute a tiny repository-local JavaScript action using `runs.using: node24`, assert its runtime, and compare with a separately selected application Node version. |
| 5 | Oct 2 | Stateless GitHub App installation tokens | Rollout complete | Yes: conditional on GitHub App setup | Mint a scoped installation token, perform an API call, and publish only safe metadata; run opaque-token compatibility tests without exposing credentials. |
| 6 | Oct 1 | Retention covers checks, runs, and statuses | Effective behavior change | Partial: audit/export is live; actual expiry is time-based | Produce an evidence/export artifact and explain the expanded retention boundary; use prepared historical evidence rather than claiming immediate expiry. |
| 7 | Sep 24 | Expired artifacts disappear from UI and API | Effective display/API change; billing and retention unchanged | Partial: requires pre-expired evidence | Seed a short-retention artifact before the session, then use a later workflow to show its absence from API results and its creation in retained logs. |
| 8 | Sep 25 | Workflow-run query counts become bounded | Rolling out on github.com and Enterprise Cloud | Partial: threshold needs a high-volume repository | Run bounded, date-filtered REST queries and demonstrate pagination; observe the large-count behavior only in a repository with over 2,500 matching runs. |
| 9 | Sep 28 | Self-hosted runner version enforcement date moves | Enterprise Cloud enforcement begins Sep 29 | Partial: safe fleet readiness audit | Query runner-version deprecation dates and flag registration/runtime deadlines; a real fleet inventory requires additional runner-management access. |
| 10 | Oct 1 | Actions Runner Controller 0.15.0 | Released | Conditional: real fleet behavior needs Kubernetes and runner credentials | Observe a real scale set's metrics and runner lifecycle; a workflow-only Helm render is configuration validation, not proof of autoscaling. |
| 11 | Sep 10 | Xcode 27 image moves to macOS 27 | Public preview; arm64 only | Yes: conditional on preview runner availability | Run a Swift smoke build on `xcode-27`, assert macOS/Xcode versions, and display an architecture/toolchain summary. |
| 12 | Oct 1 | macOS 14 retirement announcement | Retirement scheduled Nov 2; brownouts already scheduled | Partial: migration is live-demoable, retirement itself is not | Run a smoke test on a supported macOS label and scan workflow files for retiring labels; do not deliberately depend on a brownout failure. |

## Original recommended selection

The recommended selection is **1, 2, 3, and 4**, combining practical security
controls with immediate migration work. The policy demo is conditional on
administrator access and on the relevant capabilities being available in the
demo account.

| Elapsed time | Segment | Presentation | Demonstration |
| --- | --- | --- | --- |
| 00:00-05:00 | Welcome, objectives, publication window, and demo repository | 5 min | - |
| 05:00-17:00 | 1. Cache least privilege | 5 min | 7 min |
| 17:00-28:00 | 2. Workflow execution protections | 5 min | 6 min |
| 28:00-37:00 | 3. Ubuntu image migration | 4 min | 5 min |
| 37:00-46:00 | 4. Node 24 action runtime | 4 min | 5 min |
| 46:00-50:00 | DXC adoption checklist, upcoming dates, and buffer | 4 min | - |
| 50:00-60:00 | Q&A | 10 min | - |

An alternative requiring no policy administration is **1, 3, and 4**, with
deeper workflow demonstrations and an operational-change briefing in the
remaining presentation time.

Times are presenter budgets, not guarantees of runner queue or execution
latency. Prepare successful rehearsal runs and start independent jobs before
their segments so runner queues do not consume Q&A time.

## Selected session

The chosen topics are **1, 2, 7, 8, and 9**, implemented as demo numbers
**1, 2, 3, 4, and 5** in the package. The selected schedule is 3 minutes
opening, 12 minutes cache controls, 11 minutes execution policies, 8 minutes
artifact visibility, 6 minutes reporting, 5 minutes runner readiness, and
5 minutes takeaways/buffer. Q&A begins at minute 50 and lasts 10 minutes.

## Update details, constraints, and sources

### 1. Cache access control

**Why it matters for DXC:** Cache permissions can follow trust boundaries
instead of giving every job restore and save access.

Modes are `read` (restore only), `write` (restore and save), `write-only` (save
only), and `none` (neither). Job-level settings override workflow-level
settings. Called reusable workflows cannot exceed the cache access granted by
their callers.

**Demo design:** Use isolated, run-specific cache keys and harmless content.
Seed a cache in a permitted job, attempt restores and saves from each mode,
then validate observable cache state in a permitted verifier job. Cache misses
or warnings must not be treated as proof by themselves. Use safe manual
dispatch rather than checking out untrusted code in `pull_request_target`.

**Prerequisites:** GitHub Actions enabled; ordinary hosted Linux runners;
cache access permitted by the account. No external cloud subscription.

**Important caveat:** Explicit `write` or `write-only` on low-trust events
overrides secure defaults and increases cache-poisoning risk. This is not a
recommendation to enable writes for untrusted pull requests.

- [Announcement](https://github.blog/changelog/2026-09-10-control-github-actions-cache-access-with-cache-mode/)
- [Workflow syntax](https://docs.github.com/actions/reference/workflows-and-actions/workflow-syntax#cache-mode)

### 2. Workflow execution protections

**Why it matters for DXC:** Separate the ability to contribute code from the
ability to execute sensitive automation, and govern workflows individually.

The GA release adds workflow-file targeting, insights, and REST administration.
Actor rules and event rules are evaluated together. Evaluate mode is available
on Enterprise Cloud.

**Demo design:** Apply a narrowly scoped policy only to a disposable demo
workflow. Show a permitted event and a disallowed `workflow_dispatch`, then
inspect the actual policy failure and insights. If Enterprise Cloud evaluate
mode is available, show evaluate before active enforcement. A companion
policy-management workflow can use a separately supplied administrator
credential. Keep the management workflow outside the policy target and include
an explicit cleanup operation.

**Prerequisites:** Repository administrator access; an appropriate scoped App
token or fine-grained credential for API policy management; Enterprise Cloud
for evaluate mode. A regular `GITHUB_TOKEN` must not be assumed to administer
policies. Insights may require UI inspection even when policy setup and
triggering are workflow-driven.

**Important caveat:** Do not apply demo policies to all DXC repositories.
Public-repository default `pull_request_target` protection enforcement is
scheduled for November 2, not already enforced universally on October 13.

- [Announcement](https://github.blog/changelog/2026-09-17-workflow-execution-protections-in-github-actions-generally-available/)
- [Policy concepts](https://docs.github.com/en/actions/concepts/about-actions-policies)
- [Execution policy setup](https://docs.github.com/en/actions/how-tos/administer/control-workflow-execution)
- [Policy REST API](https://docs.github.com/en/rest/actions/policies)

### 3. Ubuntu 26.04 runner images

**Why it matters for DXC:** Floating runner labels can change underneath CI
pipelines; test migration before builds move automatically.

Use `ubuntu-26.04` for x64 and `ubuntu-26.04-arm` for arm64. The announced
`ubuntu-latest` migration from 24.04 to 26.04 runs October 19-November 19, 2026.
It has not begun as of the planned October 13 session.

**Demo design:** A matrix on explicit `ubuntu-24.04` and `ubuntu-26.04` runs
identical tests and reports OS, architecture, image release, and tool versions.
Show a repeatable compatibility gate, not an invented package breakage.
Optional arm64 runs depend on availability in the destination repository.

**Prerequisites:** Hosted Linux runners; no external credentials.

- [Announcement](https://github.blog/changelog/2026-09-17-ubuntu-26-generally-available-and-latest-migration)
- [Runner image change inventory](https://github.com/actions/runner-images/issues/14747)

### 4. Node 24 JavaScript action runtime

**Why it matters for DXC:** Organizations consuming or publishing JavaScript
actions need supported action releases and compatible self-hosted platforms.

The runner-provided Node 20 JavaScript-action runtime has been retired. Use
`runs.using: node24`. The `ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION` opt-out is
removed. This is distinct from the Node version selected to build an
application; it does not mean an application can no longer target Node 20.

**Demo design:** Check out a tiny local action with no dependency installation,
report and assert `process.version` inside the action, and contrast it with an
application runtime set separately. Inspect the actual action metadata. Do not
expect a legacy `node20` action to reproduce its old runtime.

**Prerequisites:** A current hosted runner, or a supported/current self-hosted
runner. Node 24 does not support macOS 13.4 and earlier or officially support
ARM32.

- [Announcement](https://github.blog/changelog/2026-09-23-node-20-is-no-longer-available-in-github-actions/)
- [Action metadata syntax](https://docs.github.com/actions/creating-actions/metadata-syntax-for-github-actions#runs-for-javascript-actions)

### 5. Stateless GitHub App installation tokens

**Why it matters for DXC:** Fixed-length token validation and storage can break
even when permissions and API behavior remain unchanged.

New tokens retain the `ghs_` prefix but are approximately 520 characters rather
than 40. Scoping, permissions, and the one-hour lifetime are unchanged. Treat
tokens as opaque strings, not fixed-length formats.

**Demo design:** Use a repository-scoped GitHub App installation to mint a
token and call a read-only API. Publish only token length and successful API
status, never token text, decoded payloads, private keys, or Authorization
headers. Use synthetic tokens for regression tests of validators/redaction.

**Prerequisites:** A GitHub App installed on the demo repository; App ID and
private key stored as Actions variables/secrets; approved repository access.

**Important caveat:** The temporary `X-GitHub-Stateless-S2S-Token` header is
scheduled for deprecation November 30, 2026.

- [Announcement](https://github.blog/changelog/2026-10-02-stateless-github-app-installation-tokens-rolled-out/)
- [Generating installation tokens](https://docs.github.com/apps/creating-github-apps/authenticating-with-a-github-app/generating-an-installation-access-token-for-a-github-app)

### 6. Expanded retention boundary

**Why it matters for DXC:** Evidence may disappear sooner than reporting,
auditing, and incident-response integrations expect.

Checks, workflow runs, and statuses now follow the Actions retention setting
alongside artifacts and logs, including checks/statuses from third-party apps.
Organization/enterprise caps apply; the public-repository maximum is 90 days.
Increasing retention does not restore deleted records.

**Demo design:** Produce an evidence inventory and export artifact in a
workflow, then review the configured retention boundary. An export artifact in
the same repository is also subject to retention; durable archive beyond the
limit requires an approved external archive or persistent Git content. Avoid
committing sensitive run logs. Natural expiration cannot be made instantaneous.

- [Announcement](https://github.blog/changelog/2026-10-01-actions-retention-now-covers-checks-runs-and-statuses/)

### 7. Expired artifact visibility

**Why it matters for DXC:** API consumers must handle an absent artifact, not
depend on an expired placeholder remaining visible.

**Demo design:** Create a uniquely identified artifact with one-day retention
well before the session. Record its ID/name and creation run. After actual
expiration and cleanup, a second workflow queries the API and presents absence
alongside the original logs, if still retained. Prepare evidence in advance;
manual deletion is not a faithful demonstration of expiration.

**Important caveat:** This update changes display/API behavior, not retention
settings or billing. Record disappearance is not immediate proof of billing
change.

- [Announcement](https://github.blog/changelog/2026-09-24-expired-github-actions-artifacts-no-longer-shown-in-ui-and-api/)

### 8. Bounded workflow-run query results

**Why it matters for DXC:** High-volume reporting must not interpret a bounded
count as an exact fleet activity total.

The announcement states that counts above 2,500 matching runs are reported as
"2,500+"; filtered query pagination remains limited to up to 1,000 items.
Use time windows and other filters rather than relying on a single broad
query. Do not assume that ordinary pagination removes that filtered cap.

**Demo design:** A read-only workflow performs narrow, date-filtered API
queries and paginates the returned records. Real threshold behavior requires
a pre-existing high-volume repository. Synthetic fixture tests can explain
client handling, but must be clearly labeled simulations rather than observed
GitHub results.

- [Announcement](https://github.blog/changelog/2026-09-25-changes-to-query-results-in-the-github-actions-api-and-ui/)
- [Workflow runs REST API](https://docs.github.com/rest/actions/workflow-runs#list-workflow-runs-for-a-repository)

### 9. Self-hosted runner enforcement

**Why it matters for DXC:** An outdated fleet can stop accepting jobs even
though its runner registration still appears valid.

Enterprise Cloud full enforcement begins September 29, 2026. Registration
requires at least `2.329.0`, but the minimum version for executing jobs is
higher. Do not use the registration threshold as the runtime threshold.
Enterprise Server is unaffected by this notice; Data Residency enforcement
began July 31.

**Demo design:** A hosted-runner workflow queries registration/runtime
deprecation dates and produces a readiness report. Inventory of a real fleet
is optional and requires an appropriate management credential. Do not
deliberately downgrade or disable a customer runner to demonstrate rejection.

**Scope caveat:** The deprecation API was announced September 3, outside this
publication window. It is supporting prior functionality for this new
enforcement notice, not a newly released September 28 API.

- [Announcement](https://github.blog/changelog/2026-09-28-self-hosted-runner-version-enforcement-date-has-moved/)
- [Supporting earlier API announcement](https://github.blog/changelog/2026-09-03-github-actions-early-september-2026-updates/#new-rest-api-for-runner-version-deprecations)

### 10. Actions Runner Controller 0.15.0

**Why it matters for DXC:** Large Kubernetes-hosted fleets gain improved
shutdown behavior, lower API churn, and configurable controller/listener
throughput.

The release includes in-place patch upgrades, improved scale-set
reregistration, patch-based API writes, metrics-based runner status
aggregation, configurable listener QPS/burst and controller concurrency,
event filtering, and faster cleanup after successful runner pod exit.

**Demo design:** A workflow can inspect a disposable Kubernetes environment,
capture relevant metrics and resource lifecycle, and trigger sample runner
jobs. Real behavior requires a reachable cluster and credentials for an ARC
scale set. Rendering Helm manifests on a hosted runner is possible without a
fleet, but only proves configuration shape.

**Prerequisites:** Disposable Kubernetes/ARC environment, supported chart
release, installed GitHub App/runner-registration credential, and permission
to create/delete demo resources. Cluster creation or customer-fleet upgrades
are not implied by selecting this topic.

- [Announcement](https://github.blog/changelog/2026-10-01-actions-runner-controller-release-0-15-0/)
- [ARC documentation](https://docs.github.com/actions/hosting-your-own-runners/managing-self-hosted-runners-with-actions-runner-controller)

### 11. Xcode 27 on macOS 27

**Why it matters for DXC:** Apple development teams can validate their
toolchains and applications against the new OS ahead of broad adoption.

The image is in public preview, arm64 only, using `xcode-27` or
`xcode-27-xlarge`.

**Demo design:** Compile/test a small Swift sample, report `sw_vers`,
`xcodebuild -version`, and architecture, and expose results in a job summary.
Preflight runner access and queue latency. Larger runners may introduce
additional cost and account requirements.

- [Announcement](https://github.blog/changelog/2026-09-10-xcode-27-runner-image-now-runs-on-macos-27/)
- [Runner images](https://github.com/actions/runner-images)

### 12. macOS 14 retirement notice

**Why it matters for DXC:** Explicit retiring labels can disrupt otherwise
unchanged build pipelines.

Retirement is scheduled November 2, 2026, including `macos-14`,
`macos-14-large`, and `macos-14-xlarge`. Scheduled brownouts begin before
retirement. The brownout immediately before this session is October 12,
14:00 UTC through October 13, 00:00 UTC. The session time has not been provided,
so do not claim it overlaps or does not overlap the actual delivery.

**Demo design:** Run a current supported-image smoke test and a read-only
workflow-label audit. Explain replacement labels from the announcement and
verify the chosen label at rehearsal. Do not present this as a completed
retirement or schedule a demo that relies on the old image failing.

- [Announcement](https://github.blog/changelog/2026-10-01-github-actions-macos-14-runner-image-retirement/)

## Local package deliverables

- A 24-slide PowerPoint deck using the supplied DXC presentation template, preserving its
  branding and layouts, with full presenter notes, source links, demo cues, and
  explicit timing through the 50-minute handoff to Q&A.
- Selected demos under `.github/workflows`, launchable from GitHub's Actions
  tab using `workflow_dispatch`, plus reusable workflows/local actions where
  the selected feature requires them.
- A presenter demo guide with prerequisites, expected observable outcomes,
  narration, troubleshooting, cleanup, and fallback rehearsal evidence.
- A repository README covering setup, Actions permissions, variables/secrets,
  execution order, costs, and any administrator-only steps.
- Generated-file verification locally. Execution/rehearsal on GitHub remains
  the presenter's next step after publication. Local checks are not a substitute
  for GitHub service enforcement or runner availability.

## Demo safety and reliability contract

Use least-privilege workflow permissions, harmless sample data, bounded
timeouts, isolated cache/artifact/resource names, and explicit manual triggers.
Pin external actions to verified full commit SHAs when implementations are
built. Never print credentials or embed secrets in Git or the deck.

Administrative changes require an explicitly selected disposable target.
Cleanup must remove only demo-created resources/policies, not broader customer
settings. GitHub Actions billing, account policies, hosted-runner availability,
and required plan entitlements must be checked before rehearsal.

If a live feature is unavailable, report it as blocked and use clearly labeled
rehearsal evidence or an explanatory example. A simulation must never be
represented as a successfully observed feature.
