# DXC GitHub Actions Office Hour - October 13, 2026

Five selected updates: **cache permissions, workflow execution protections,
expired artifact visibility, bounded workflow reporting, and self-hosted
runner enforcement**. Research covers September 10-October 9, 2026.

**Presentation:** [DXC Office Hour deck](outputs/slides/dxc-actions-office-hour-2026-10-13.pptx)  
**Presenter:** [Demo guide](docs/presenter-demo-guide.md)  
**Research:** [Source-linked update catalog](docs/update-catalog-2026-10-13.md)  
**Timing and full notes:** [Slide content](presentation/slide-content.json)

## Status and scope

**Repository:** [seandorsett/dxc-actions-office-hour](https://github.com/seandorsett/dxc-actions-office-hour)
(private).

The package was prepared locally and published at your request. No live
GitHub demonstration has been executed on your behalf. Offline tests use
synthetic API responses and must not be represented as live GitHub results.

The package targets **github.com**, not GitHub Enterprise Server. All demo
workflows are manually initiated except the harmless policy target, which can
also receive a specifically named repository dispatch. There are no automatic
scheduled runs or cloud infrastructure deployments.

The deck retains the supplied DXC/EDGE template branding, including its **DXC
Internal** label. Use an appropriately restricted repository and follow DXC's
sharing policy; do not assume this material is approved for a public repository.

## Session schedule

| Minutes | Segment |
| --- | --- |
| 0-4 | Welcome, outcomes, and demo contract |
| 4-16 | Cache least privilege and reusable-workflow ceiling |
| 16-27 | Workflow execution protections and policy demonstration |
| 27-35 | Natural artifact expiration and retained evidence |
| 35-41 | Bounded reporting and time-window pagination |
| 41-46 | Read-only runner upgrade readiness |
| 46-50 | DXC adoption checklist and takeaways |
| 50-60 | Q&A |

Runner queue time is not included in promised execution times. Rehearse, launch
independent demos early, and retain successful run summaries. The deck includes
explicit fallback narration when live prerequisites are unavailable.

## Launch from GitHub

1. Open this repository's **Actions** tab. The package, including `.github`
   workflows, is stored on the default branch.
2. Confirm Actions is enabled and the pinned first-party actions below are
   permitted. Keep this repository restricted.
3. Run **Validate Office Hour package** from **Actions > Run workflow**.
4. Configure the administrator environment and credentials before demos 2 and 5.
5. Run the artifact demo in **seed** mode immediately, ideally by October 10 or
   11. Wait for its actual `expires_at` timestamp and cleanup, then rehearse
   **inspect** mode before October 13.

For reuse in another repository, upload the complete package, including hidden
`.github` files. Exclude local `.env` files, credentials, private keys, and
generated run data under `demo-output`.

No workflow contains a hardcoded owner/repository. API calls use the destination
repository's `GITHUB_REPOSITORY`. Run workflows from the default branch; the
administrative demos explicitly reject other branches.

### Workflow inventory

| Workflow file | Actions display name | Inputs / required setup |
| --- | --- | --- |
| `.github/workflows/demo-1-cache-modes.yml` | Demo 1 - Cache least privilege | No inputs or extra secrets |
| `.github/workflows/demo-1-cache-probe.yml` | Reusable helper, not a manual demo | Called by demo 1 for each cache mode |
| `.github/workflows/demo-2-policy-control.yml` | Demo 2 - Workflow policy control | `operation`, optional `policy_id`; admin secret |
| `.github/workflows/demo-2-policy-target.yml` | Demo 2 target - Harmless policy probe | Manual `probe_label`, or named repository dispatch |
| `.github/workflows/demo-3-artifact-expiry.yml` | Demo 3 - Natural artifact expiration | `operation`: seed/inspect; `seed_run_id` for inspect |
| `.github/workflows/demo-4-bounded-reporting.yml` | Demo 4 - Bounded workflow reporting | Inclusive UTC start/end dates and page size |
| `.github/workflows/demo-5-runner-readiness.yml` | Demo 5 - Runner upgrade readiness | Version list, repository/organization scope, inventory flag |
| `.github/workflows/validate-package.yml` | Validate Office Hour package | Offline unit tests and workflow structure checks |
| `.github/workflows/build-deck.yml` | Build DXC presentation | Rebuild PowerPoint from the committed DXC template/content |

## Administrator prerequisites

Create an Actions **environment named `demo-admin`** before running demos 2/5.
Restrict it to the default branch, configure required reviewers where your
plan supports them, and store the credentials below as **environment secrets**.
If required-reviewer controls are unavailable, restrict repository write access
and do not use production administrator credentials.

| Secret / variable | Purpose | Minimum intended access |
| --- | --- | --- |
| `DEMO_POLICY_ADMIN_TOKEN` | Create, inspect, activate, trigger, and remove only the isolated demo policy | Fine-grained PAT or approved App access to the disposable repository: Administration write for policy management, Actions write for workflow dispatch, Contents write for repository dispatch; read access to contents |
| `RUNNER_READ_TOKEN` | Read runner deprecation schedules and optional inventory | Repository Administration read for repository scope; organization Self-hosted runners read for organization scope, with an administrator identity where required |
| `RUNNER_AUDIT_ORG` | Organization scope for demo 5 | Environment variable containing the approved organization login; not needed for repository scope |

Confirm the API's current required permissions and account/SSO authorization
when provisioning credentials. Token permissions do not grant the underlying
user an administrator role. Enterprise/organization policies may still deny a
request. Missing access produces a visible error, not a simulated success.

Use short-lived credentials where possible and revoke temporary credentials
after delivery. The default `GITHUB_TOKEN` does **not** administer Actions
execution policies or read administrator-only runner endpoints.

**Evaluate mode requires GitHub Enterprise Cloud.** If unavailable, use
`create-active` directly in the disposable repository, or present the
policy explanation without claiming to demonstrate evaluate mode.

## Demo-specific constraints

### Demo 1: cache

Six hosted jobs execute: one seed, four parallel reusable-workflow probes,
and one verifier. Each probe attempts
an actual restore/save. The reusable workflow asks for `write`, but its caller
limits access. The verifier reads cache inventory and asserts which candidate
keys actually exist.

Expected restore/save results:

| Caller mode | Restore | Save |
| --- | --- | --- |
| read | Yes | No |
| write | Yes | Yes |
| write-only | No | Yes |
| none | No | No |

The run-specific prefix is `dxc-oh-RUN_ID-RUN_ATTEMPT`. A cache step remaining
green is **not** proof that it restored or saved: forbidden operations can log
an informational message and continue. Marker assertions and the independent
API verifier provide the evidence. No untrusted PR code is executed.

### Demo 2: policy

Use this sequence:

1. `inspect` to understand inherited policies.
2. `create-evaluate` where supported, or `create-active`.
3. Record the returned policy ID.
4. `probe-allowed` sends `workflow_dispatch`; `probe-blocked` sends the named
   `repository_dispatch`.
5. In evaluate mode, inspect insights and then use `activate` with the ID.
6. Repeat both probes under active enforcement.
7. Open the target workflow's actual error/insights. An accepted API request
   alone does not prove a workflow executed or a policy blocked it.
8. `cleanup` with the same ID.

The policy targets **only** `.github/workflows/demo-2-policy-target.yml`, and
allows only `workflow_dispatch`. The control workflow stays outside that
target. Cleanup refuses an unrelated policy name or workflow scope.
Repository, organization, and enterprise policies still layer; this demo
never weakens an inherited policy.

### Demo 3: artifact expiration

`seed` uploads `expiry-demo-RUN_ID` with one-day retention and obtains the
actual artifact ID, creation time, and expiry from GitHub's API. It also uploads
`expiry-receipt-RUN_ID` with **14-day retention**.

`inspect` downloads the retained receipt from the supplied seed run, checks
the seed identity, and refuses to claim expiry before its original
`expires_at`. It then checks both the artifact list and direct GET endpoint.
If cleanup has not completed, it reports **NOT READY** and fails explicitly.

Do not manually delete the target artifact. Absence cannot by itself
distinguish expiry from deletion. The retained receipt and original upload
logs provide provenance; logs/receipts also eventually expire. Keep the demo
repository's run/log retention above the preparation/session interval.
Never lower production retention settings for this demonstration.

### Demo 4: reporting

The live workflow reads only its own repository. Page size 2 makes pagination
visible after a few rehearsal runs. Requests use explicit UTC time windows.
Windows with a reported count of at least 1,000, or a non-exact `+` count, are
split before fetching beyond the filtered retrieval cap.

The feature announcement describes **2,500+ count reporting**; the API still
limits a filtered query to **1,000 returned records**. These are separate
limits. The client inspects actual response types rather than assuming that
the API will return the same string shown in the UI.

The script stops with an error at its request budget or an unsplittable
saturated one-second window. It never labels a truncated export complete.
The API is not an atomic snapshot: concurrent creation/deletion can change
results. For a large repository use page size 100 and narrower dates.

Synthetic unit tests cover bounded-count/time-splitting behavior. They are
**not** a live observation of 2,500+ matching runs. The workflow summary
explicitly says whether it actually observed a count requiring splitting.

### Demo 5: runner readiness

Default inputs query two explicit runner versions without touching a real
fleet. Optional inventory adds versions from visible runners, flags missing
versions, and remains read-only.

Use distinct registration and runtime dates returned by GitHub. The announced
`2.329.0` registration minimum must not be treated as the higher runtime
minimum. A null deprecation date means **no date was returned**, not a guarantee
that the runner is supported. Never downgrade a runner to reproduce failure.

## Local verification and deck generation

```powershell
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python -m pip install -r requirements-presentation.txt
python scripts/generate_deck.py
python scripts/check_deck.py
```

The deck generator uses the supplied `Session Presentation Deck Template.pptx`
as its actual base, not an approximation of its colors. It preserves masters,
layouts, images, and 16:9 slide dimensions. Speaker notes come verbatim from
`presentation/slide-content.json`.

**Build DXC presentation** can also generate/download the deck entirely in
GitHub Actions. It does not commit the generated binary automatically:
download the artifact and commit it if you want the built deck tracked in Git.
The prebuilt deck in this package is ready to commit.

## Costs, cleanup, and evidence handling

Hosted jobs, caches, and artifacts can consume Actions minutes/storage,
especially in private repositories. No larger runners or cloud services are
required for these five selected topics. Set an appropriate billing budget.

- Demo cache content is a few harmless text files. Delete only the keys with
  the specific rehearsal run prefix through the Actions cache UI if desired.
- Remove the specific demo policy with `cleanup`; do not remove all policies.
- Allow the one-day artifact to expire naturally. Receipts/reports expire after
  their configured 7/14 days unless constrained by account settings.
- Revoke temporary administrator credentials and remove the demo environment
  secrets after the session.
- Runner reports can include internal runner names/versions. Keep them in the
  restricted repository and sanitize any evidence before sharing elsewhere.

No secrets, private keys, Authorization headers, or token values should be
committed, displayed, or included in slides.

## Pinned first-party actions

| Action | Verified ref | Commit |
| --- | --- | --- |
| actions/checkout | v6 | `d23441a48e516b6c34aea4fa41551a30e30af803` |
| actions/cache (restore/save) | v5 | `caa296126883cff596d87d8935842f9db880ef25` |
| actions/upload-artifact | v7.0.2 | `cf430e030ddbb5b0abf93d22962f4752f3646cd9` |
| actions/download-artifact | v8.0.2 | `9000827ccba6bdab643e8b6fd33ac0654aef8333` |

Pins were resolved from official action repositories during package creation.
Account policies must permit these exact actions and commits.
