# DXC GitHub Actions Office Hour

**Session:** October 13, 2026  
**Format:** 50 minutes of presentation and demos, followed by 10 minutes of Q&A  
**Release window:** September 10-October 9, 2026

[Download the presentation deck](dxc-actions-office-hour-2026-10-13.pptx).
The 24-slide deck uses the supplied DXC template and includes full speaking
notes, demo cues, setup instructions, and source links. Open it in PowerPoint
and use **Presenter View** to read the notes while presenting.

The repository contains the deck, this README, and ten small workflows:
**Before and After for each of five demos**. Each workflow is self-contained,
manually triggered, and runs one job. There are no helper scripts or package
installations.

## Updates covered

| Demo | Published | Update | Why it matters |
| --- | --- | --- | --- |
| 1 | Sep 10 | [Cache access control with `cache-mode`](https://github.blog/changelog/2026-09-10-control-github-actions-cache-access-with-cache-mode/) | Choose whether jobs may restore, save, both, or neither. Explicit read-only access can prevent unnecessary cache writes. Generally available on github.com. |
| 2 | Sep 17 | [Workflow execution protections](https://github.blog/changelog/2026-09-17-workflow-execution-protections-in-github-actions-generally-available/) | Centrally restrict actors and events, now with workflow-file targeting, insights, and REST administration. Evaluate mode requires Enterprise Cloud. |
| 3 | Sep 24 | [Expired artifacts disappear from the UI and API](https://github.blog/changelog/2026-09-24-expired-github-actions-artifacts-no-longer-shown-in-ui-and-api/) | Integrations must handle absent records rather than expect an expired entry to remain visible. This does not change retention settings or billing. |
| 4 | Sep 25 | [Bounded workflow-run query counts](https://github.blog/changelog/2026-09-25-changes-to-query-results-in-the-github-actions-api-and-ui/) | Large counts are reported as `2,500+`; a filtered query still returns at most 1,000 records. Use bounded time windows and pagination rather than assume one broad query is complete. |
| 5 | Sep 28 | [Self-hosted runner enforcement notice](https://github.blog/changelog/2026-09-28-self-hosted-runner-version-enforcement-date-has-moved/) | Enterprise Cloud full enforcement begins September 29. The `2.329.0` registration minimum is not the higher minimum for executing jobs; inspect both support deadlines. |

These include new capabilities **and operational changes**, not five
interchangeable new features. The demos target **github.com**, not GitHub
Enterprise Server.

**Before does not mean an older GitHub service version.** Both workflows run
on today's service. Before illustrates an older approach or establishes an
original artifact state; After demonstrates the improved configuration,
handling, or later observation.

## Start here

1. Open the repository's **Actions** tab. Confirm Actions, hosted runners, and
   the pinned first-party actions are allowed by your account.
2. Choose a numbered **BEFORE** workflow, click **Run workflow**, select
   **main**, and start it. Open the completed run's summary and job logs.
3. Run the corresponding **AFTER** workflow with the inputs described below.
   For demos 1 and 3, copy the numeric **Before run ID** from its summary, not
   the workflow's run number.
4. Compare the actual results. Use the deck's speaking notes for narration,
   expected outcomes, and transitions.

**Start Demo 3 BEFORE early:** its target artifact has one-day retention.
After needs real elapsed time and service cleanup, so prepare it at least a
day before presenting. Do not leave this seed run until the live session.

## Workflow pairs

| Demo | Before workflow | After workflow | After inputs / setup |
| --- | --- | --- | --- |
| 1. Cache permissions | [demo-1-before.yml](.github/workflows/demo-1-before.yml) | [demo-1-after.yml](.github/workflows/demo-1-after.yml) | `before_run_id` from the successful Before run |
| 2. Execution policy | [demo-2-before.yml](.github/workflows/demo-2-before.yml) | [demo-2-after.yml](.github/workflows/demo-2-after.yml) | Administrator configures the file-scoped policy below |
| 3. Artifact visibility | [demo-3-before.yml](.github/workflows/demo-3-before.yml) | [demo-3-after.yml](.github/workflows/demo-3-after.yml) | `before_run_id`; wait past its actual expiry and cleanup |
| 4. Bounded reporting | [demo-4-before.yml](.github/workflows/demo-4-before.yml) | [demo-4-after.yml](.github/workflows/demo-4-after.yml) | `utc_date` in `YYYY-MM-DD` format |
| 5. Runner readiness | [demo-5-before.yml](.github/workflows/demo-5-before.yml) | [demo-5-after.yml](.github/workflows/demo-5-after.yml) | Same `version`; `demo-admin` environment and `RUNNER_READ_TOKEN` |

### Demo 1: implicit writes versus explicit read-only cache

Run Before and copy its run ID. It saves harmless text using the trusted
manual trigger's default cache access. Run After with that `before_run_id`.
After adds **`cache-mode: read`**, restores the known text, attempts a new
save, and checks that the candidate cache key is absent.

Copy the **entire** numeric ID from Before's summary or its Actions run URL.
After validates that the ID belongs to a successful Demo 1 Before run in this
repository. A missing cache fails at the restore step instead of a later
missing-file check; confirm the Before cache still exists and use the same
branch as your Before run.

**Show:** restored content, the denied-save log, and the final summary.
A green cache step alone does not prove anything was saved. No extra secret
is needed.

### Demo 2: manual execution versus central policy enforcement

Run Before to show a harmless job reaching a runner. Then a repository
administrator prepares this policy in **Settings > Actions > Policies**:

| Setting | Value |
| --- | --- |
| Name | `dxc-office-hour-demo-2` |
| Workflow target | **Only** `.github/workflows/demo-2-after.yml` |
| Enforcement | **Active** |
| Allowed events | `push`, but **not** `workflow_dispatch` |

Manually trigger After. GitHub should block it **before its job executes**,
while Before remains outside this narrowly targeted demo policy.

**Show:** the actual GitHub policy error, or Policy insights if available.
The After YAML has a diagnostic step that fails if it reaches a runner.
That script failure means the intended policy did not actively block the
dispatch; it is **not** proof of central enforcement.

Evaluate mode and insights depend on Enterprise Cloud capabilities.
Inherited policies still apply. If policy settings or administrator access
are unavailable, explain the limitation rather than substitute a script-based
simulation. Delete only the named demo policy when finished.

### Demo 3: an artifact exists, then disappears after natural expiry

Run Before at least a day early. It uploads a **one-day target artifact** and
a separate **14-day receipt** recording its ID and actual `expires_at`.
Keep the successful run ID, receipt, and upload logs.

After the recorded expiry and service cleanup, run After with that
`before_run_id`. It downloads the receipt, validates the original run,
and checks that the target is absent from the artifact list and its direct
GET returns **404**.

**Show:** the original receipt beside After's API observations. If After
reports **NOT READY**, the artifact has not expired or cleanup has not
completed. Wait and retry. A permission error is not evidence of expiry.

Do not manually delete the target to manufacture this result. Absence alone
cannot distinguish deletion from natural expiry. Receipts and logs also
eventually expire; keep repository retention long enough for preparation and
delivery. Account retention caps can shorten the receipt's window.

### Demo 4: one broad page versus date-bounded pagination

Run Before to fetch only two records from one broad page. Run After with
the **UTC day containing your rehearsal runs**; this may differ from your
local calendar day. Its default is `2026-10-13`, so change it when rehearsing
on another date.

After adds a date filter, follows pages, and displays distinct run IDs.
It stops if the count is bounded or reaches the **1,000-record filtered cap**.
For a saturated day, choose a lower-volume day for this simple demo; a
production reporting implementation should narrow the API time interval
further.

**Show:** the query scope, actual returned counts, and IDs. A small repository
does not demonstrate the `2,500+` threshold. Pagination does not remove the
filtered cap, and concurrent record changes mean the API is not an atomic
snapshot. Neither workflow modifies remote data.

### Demo 5: registration-only assumption versus two live support dates

Run Before with `version=2.329.0` or another numeric `major.minor.patch`
version. It makes a **local comparison** with the announced registration
floor, not an actual registration attempt. Runtime readiness remains unknown.

Before running After, create an Actions **environment named `demo-admin`**:

1. Restrict deployment branches to **main**, and configure required reviewers
   where your plan supports them.
2. Store **`RUNNER_READ_TOKEN`** as an environment secret. Use an approved,
   narrowly scoped credential with repository **Administration: read** access.
   The identity must have administrator access where the endpoint requires it;
   confirm account authorization and SSO requirements.
3. Run After on **main**, using the same `version` as Before.

The normal `GITHUB_TOKEN` is insufficient for this administrator-only lookup.
After queries **`registration_deprecates_at`** and
**`runtime_deprecates_at`** separately and labels returned dates as passed or
upcoming. An omitted or null date means **no date returned**, not guaranteed
support.

**Show:** the local assumption beside the live API's two dates. This workflow
never registers, stops, upgrades, or removes a runner. Revoke the temporary
credential and remove its environment secret after the session.

## Safety and rehearsal

Keep this repository restricted: the deck retains the template's **DXC
Internal** classification. Hosted jobs, caches, and artifacts can incur
Actions minute/storage costs. No larger runners or cloud deployments are
required.

Use harmless demo data, scoped credentials, and the default branch. Do not
commit tokens or private keys. Optional cache cleanup should remove only the
specific `dxc-oh-simple-*` demo keys, not all repository caches.

Publishing workflow files does not verify live feature behavior. Rehearse
the pairs after setup and keep completed runs available as fallback evidence.
At minute **45**, stop starting new demos; at minute **50**, move to Q&A.
