#!/usr/bin/env python3
"""GitHub Actions Office Hour API demonstrations.

Usage: python scripts/demo_api.py --help
Prerequisites: Python 3.10+, github.com, GITHUB_REPOSITORY and GITHUB_TOKEN.
Supply credentials only through environment variables, never CLI arguments.
Outputs: safe JSON in demo-output and Markdown in GITHUB_STEP_SUMMARY.
Policy cleanup is explicit: policy --operation cleanup --policy-id ID.
Cache cleanup is optional through the repository Actions cache UI; never delete
other repository caches. Artifact receipts expire naturally after 14 days.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, time, timedelta, timezone
import json
import os
from pathlib import Path
import re
import sys
import time as clock
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

UTC = timezone.utc
POLICY_TARGET = ".github/workflows/demo-2-policy-target.yml"
POLICY_PREFIX = "dxc-office-hour-demo-2-"
MODES = {"read": (True, False), "write": (True, True),
         "write-only": (False, True), "none": (False, False)}


class APIError(RuntimeError):
    def __init__(self, status: int, message: str):
        super().__init__(f"GitHub API HTTP {status}: {message}")
        self.status = status


def repository(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", value):
        raise ValueError("Repository must be owner/repo.")
    return value


def timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timestamps must include a timezone.")
    return parsed.astimezone(UTC)


def iso(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class GitHub:
    def __init__(self, repo: str, token: str, max_requests: int = 100):
        self.repo = repository(repo)
        if not token:
            raise ValueError("Required credential is missing. See README secret setup.")
        self.token = token
        self.requests = 0
        self.max_requests = max_requests

    def call(self, path: str, method: str = "GET",
             body: dict[str, Any] | None = None) -> Any:
        if not path.startswith("/") or path.startswith("//"):
            raise ValueError("Only relative GitHub API paths are supported.")
        if self.requests >= self.max_requests:
            raise RuntimeError("API request budget reached; narrow the date range or scope.")
        self.requests += 1
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2026-03-10",
            "User-Agent": "DXC-Actions-Office-Hour",
        }
        data = None if body is None else json.dumps(body).encode()
        if data is not None:
            headers["Content-Type"] = "application/json"
        request = Request("https://api.github.com" + path, data=data,
                          headers=headers, method=method)
        try:
            with urlopen(request, timeout=30) as response:
                content = response.read()
                return json.loads(content) if content else None
        except HTTPError as error:
            content = error.read(8192).decode("utf-8", errors="replace")
            try:
                message = json.loads(content).get("message", "Request failed")
            except json.JSONDecodeError:
                message = "Request failed; consult GitHub API documentation."
            raise APIError(error.code, str(message).replace(self.token, "[redacted]")) from error
        except URLError as error:
            raise RuntimeError(f"GitHub API transport failure: {error.reason}") from error

    def pages(self, path: str, key: str) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        joiner = "&" if "?" in path else "?"
        for page in range(1, 51):
            data = self.call(f"{path}{joiner}per_page=100&page={page}")
            rows = data[key]
            items.extend(rows)
            if len(rows) < 100:
                return items
        raise RuntimeError("Inventory exceeded 5,000 records; narrow the scope.")


def report(name: str, data: Any, markdown: str) -> None:
    target = Path("demo-output")
    target.mkdir(exist_ok=True)
    (target / f"{name}.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    (target / f"{name}.md").write_text(markdown + "\n", encoding="utf-8")
    print(markdown)
    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(summary, "a", encoding="utf-8") as stream:
            stream.write(markdown + "\n")


def policy_body(name: str, enforcement: str) -> dict[str, Any]:
    return {
        "name": name, "enforcement": enforcement,
        "conditions": {"workflow_path": {"include": [POLICY_TARGET], "exclude": []}},
        "rules": [{"type": "restrict_action_events",
                   "parameters": {"allowed_events": ["workflow_dispatch"]}}],
    }


def assert_demo_policy(data: dict[str, Any]) -> None:
    expected = policy_body("", "")["conditions"]
    if (not data["name"].startswith(POLICY_PREFIX)
            or data.get("conditions") != expected):
        raise ValueError("Refusing to modify a policy not owned by this scoped demo.")


def run_policy(api: GitHub, operation: str, policy_id: str) -> None:
    base = f"/repos/{api.repo}/actions/policies"
    if operation.startswith("create-"):
        enforcement = operation.removeprefix("create-")
        run_id = os.environ["GITHUB_RUN_ID"]
        attempt = os.environ.get("GITHUB_RUN_ATTEMPT", "1")
        name = f"{POLICY_PREFIX}{run_id}-{attempt}"
        data = api.call(base, "POST", policy_body(name, enforcement))
        assert_demo_policy(data)
        if data["enforcement"] != enforcement:
            raise RuntimeError("Created policy enforcement did not match the request.")
        report("policy", {"id": data["id"], "name": data["name"],
                         "enforcement": data["enforcement"], "target": POLICY_TARGET},
               f"## Demo policy created\n\nPolicy ID: **{data['id']}**\n\n"
               f"Mode: **{enforcement}**. Target: `{POLICY_TARGET}` only.\n\n"
               "Record this ID for activation and cleanup. Other policies still apply.")
    elif operation in ("activate", "cleanup"):
        if not re.fullmatch(r"[1-9]\d*", policy_id):
            raise ValueError("A positive policy ID from this demo is required.")
        path = f"{base}/{policy_id}"
        assert_demo_policy(api.call(path))
        if operation == "cleanup":
            api.call(path, "DELETE")
            report("policy", {"deleted_policy_id": policy_id},
                   f"## Cleanup completed\n\nDeleted only demo policy **{policy_id}**.")
        else:
            updated = api.call(path, "PUT", {"enforcement": "active"})
            if updated["enforcement"] != "active":
                raise RuntimeError("Policy activation was not confirmed.")
            report("policy", {"id": updated["id"], "enforcement": "active"},
                   f"## Policy active\n\nDemo policy **{policy_id}** now enforces its event allowlist.")
    elif operation in ("probe-allowed", "probe-blocked"):
        label = f"demo-{os.environ['GITHUB_RUN_ID']}-{os.environ.get('GITHUB_RUN_ATTEMPT', '1')}"
        if operation == "probe-allowed":
            api.call(f"/repos/{api.repo}/actions/workflows/demo-2-policy-target.yml/dispatches",
                     "POST", {"ref": os.environ["DEFAULT_BRANCH"],
                              "inputs": {"probe_label": label}})
        else:
            api.call(f"/repos/{api.repo}/dispatches", "POST",
                     {"event_type": "office-hour-policy-probe",
                      "client_payload": {"probe_label": label}})
        report("policy-trigger", {"probe_label": label, "operation": operation,
                                  "request_accepted": True},
               f"## Probe request accepted\n\nFind **{label}** in the target workflow.\n\n"
               "HTTP acceptance is NOT proof of execution or policy enforcement. "
               "Inspect the target run error and Policy insights. In evaluate mode "
               "both events may execute; in active mode repository_dispatch is disallowed.")
    elif operation == "inspect":
        items = api.pages(base + "?has_parents=true", "policies")
        safe = [{"id": p["id"], "name": p["name"], "enforcement": p["enforcement"],
                 "source_type": p["source_type"], "conditions": p.get("conditions"),
                 "rules": p.get("rules")} for p in items]
        report("policies", safe,
               f"## Policy inventory\n\nRead **{len(safe)}** policies, including inherited policies.\n\n"
               "Inspect demo-output/policies.json. No policy was changed.")
    else:
        raise ValueError("Unsupported policy operation.")


def artifact_receipt(api: GitHub, artifact_id: str) -> None:
    if not re.fullmatch(r"[1-9]\d*", artifact_id):
        raise ValueError("Upload action did not return a valid artifact ID.")
    data = api.call(f"/repos/{api.repo}/actions/artifacts/{artifact_id}")
    run_id = int(os.environ["GITHUB_RUN_ID"])
    expected_name = f"expiry-demo-{run_id}"
    if data["name"] != expected_name or data["workflow_run"]["id"] != run_id:
        raise RuntimeError("Uploaded artifact identity did not match the seed run.")
    receipt = {
        "repository": api.repo, "seed_run_id": run_id, "artifact_id": data["id"],
        "artifact_name": data["name"], "created_at": data["created_at"],
        "expires_at": data["expires_at"],
        "note": "Harmless demo data; do not manually delete the target artifact.",
    }
    report("receipt", receipt,
           f"## Expiry seed created\n\nSeed run ID: **{run_id}**\n\n"
           f"Artifact ID: **{data['id']}**. Natural expiration: **{data['expires_at']}**.\n\n"
           "The separate receipt lasts 14 days. Re-run in inspect mode only after "
           "expiration and service cleanup. Do not delete the artifact manually.")


def inspect_artifact(api: GitHub, receipt: dict[str, Any], seed_run_id: str,
                     now: datetime) -> None:
    seed_id = int(seed_run_id)
    if (receipt["repository"] != api.repo or receipt["seed_run_id"] != seed_id
            or receipt["artifact_name"] != f"expiry-demo-{seed_id}"):
        raise ValueError("Receipt is not for the selected seed run in this repository.")
    artifact_id = receipt["artifact_id"]
    if not isinstance(artifact_id, int) or isinstance(artifact_id, bool) or artifact_id < 1:
        raise ValueError("Invalid artifact ID in receipt.")
    seed = api.call(f"/repos/{api.repo}/actions/runs/{seed_id}")
    if (seed["conclusion"] != "success"
            or seed["path"].split("@")[0] != ".github/workflows/demo-3-artifact-expiry.yml"):
        raise RuntimeError("Expected a successful artifact demo seed run.")
    expires = timestamp(receipt["expires_at"])
    if now < expires:
        raise RuntimeError(f"NOT READY: natural expiration is {iso(expires)}. No expiry claim made.")
    items = api.pages(f"/repos/{api.repo}/actions/runs/{seed_id}/artifacts", "artifacts")
    present_in_list = any(a["id"] == artifact_id for a in items)
    try:
        api.call(f"/repos/{api.repo}/actions/artifacts/{artifact_id}")
        present_directly = True
    except APIError as error:
        if error.status != 404:
            raise
        present_directly = False
    result = {"receipt": receipt, "observed_at": iso(now),
              "present_in_list": present_in_list, "get_returns_404": not present_directly,
              "attribution": "Consistent with expiry only if no manual deletion occurred."}
    report("artifact-observation", result,
           f"## Artifact expiry observation\n\nSeed: **{seed_id}**; artifact: **{artifact_id}**.\n\n"
           f"Present in run artifact list: **{present_in_list}**.\n\n"
           f"Direct GET returns 404: **{not present_directly}**.\n\n"
           "Compare with the retained receipt and seed logs. Absence alone cannot "
           "distinguish natural expiry from manual deletion. This is not a billing change.")
    if present_in_list or present_directly:
        raise RuntimeError("NOT READY: artifact remains visible. Allow service cleanup, then retry.")


def count_requires_split(value: Any) -> bool:
    if isinstance(value, bool):
        raise ValueError("Invalid workflow-run total_count.")
    if isinstance(value, int):
        if value < 0:
            raise ValueError("Negative workflow-run total_count.")
        return value >= 1000
    if isinstance(value, str) and re.fullmatch(r"[\d,]+\+?", value):
        return value.endswith("+") or int(value.replace(",", "")) >= 1000
    raise ValueError(f"Unexpected workflow-run total_count type: {type(value).__name__}")


def enumerate_runs(api: GitHub, start: datetime, end: datetime,
                   per_page: int = 100) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Enumerate half-open UTC windows; split before the filtered 1,000-run cap."""
    if start >= end or not 1 <= per_page <= 100:
        raise ValueError("Invalid time range or per-page value.")
    runs: dict[int, dict[str, Any]] = {}
    windows: list[dict[str, Any]] = []

    def visit(left: datetime, right: datetime, depth: int) -> None:
        query = {"created": f"{iso(left)}..{iso(right - timedelta(seconds=1))}",
                 "per_page": per_page}
        path = f"/repos/{api.repo}/actions/runs?"
        first = api.call(path + urlencode({**query, "page": 1}))
        count = first["total_count"]
        split = count_requires_split(count)
        windows.append({"start": iso(left), "end_exclusive": iso(right),
                        "reported_total_count": count, "split": split})
        if split:
            seconds = int((right - left).total_seconds())
            if seconds < 2 or depth >= 24:
                raise RuntimeError("Saturated smallest time window; completeness cannot be proven.")
            middle = left + timedelta(seconds=seconds // 2)
            visit(left, middle, depth + 1)
            visit(middle, right, depth + 1)
            return
        page, payload, returned = 1, first, 0
        while True:
            rows = payload["workflow_runs"]
            returned += len(rows)
            if returned >= 1000:
                raise RuntimeError("Filtered cap reached despite reported count; rerun narrower.")
            for row in rows:
                created = timestamp(row["created_at"])
                if not left <= created < right:
                    raise RuntimeError("API returned a run outside its requested window.")
                runs[row["id"]] = {key: row.get(key) for key in
                                   ("id", "name", "event", "status", "conclusion",
                                    "created_at", "html_url")}
            if len(rows) < per_page:
                break
            page += 1
            payload = api.call(path + urlencode({**query, "page": page}))
    visit(start, end, 0)
    return sorted(runs.values(), key=lambda row: (row["created_at"], row["id"])), windows


def reporting(api: GitHub, start_date: str, end_date: str, per_page: int) -> None:
    start = datetime.combine(date.fromisoformat(start_date), time.min, UTC)
    end = datetime.combine(date.fromisoformat(end_date) + timedelta(days=1), time.min, UTC)
    rows, windows = enumerate_runs(api, start, end, per_page)
    capped = any(w["split"] for w in windows)
    report("workflow-report", {"repository": api.repo, "runs": rows, "windows": windows,
                              "requests": api.requests, "large_count_observed": capped,
                              "caveat": "Non-atomic API enumeration; records may change during queries."},
           f"## Live workflow-run reporting\n\nDate range: **{start_date} through {end_date}**, UTC.\n\n"
           f"Enumerated **{len(rows)}** distinct run IDs using **{api.requests}** requests.\n\n"
           f"A count requiring time-window splitting was observed: **{capped}**.\n\n"
           "Review workflow-report.json for actual returned counts. If false, this "
           "repository did NOT demonstrate the large-volume threshold. Synthetic "
           "unit tests exercise that branch separately. Enumeration is not an atomic snapshot.")


def deadline(value: str | None, now: datetime) -> str:
    if value is None:
        return "No date returned; support not guaranteed"
    return ("Deadline passed" if timestamp(value) <= now else "Upcoming") + f": {value}"


def runner_audit(api: GitHub, versions: str, scope: str, organization: str,
                 include_inventory: bool, now: datetime) -> None:
    if scope == "organization":
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", organization):
            raise ValueError("Set a valid organization for organization scope.")
        base = f"/orgs/{organization}/actions/runners"
    else:
        base = f"/repos/{api.repo}/actions/runners"
    requested = {v.strip() for v in versions.split(",") if v.strip()}
    if not requested or len(requested) > 10:
        raise ValueError("Supply between one and ten runner versions.")
    inventory = api.pages(base, "runners") if include_inventory else []
    for runner in inventory:
        if runner.get("version"):
            requested.add(runner["version"])
    if len(requested) > 30:
        raise ValueError("More than 30 distinct fleet versions; narrow the audit.")
    rows = []
    for version in sorted(requested):
        if not re.fullmatch(r"\d+\.\d+\.\d+", version):
            raise ValueError("Runner versions must be numeric major.minor.patch.")
        data = api.call(f"{base}/deprecations/{version}")
        if data["runner_version"] != version:
            raise RuntimeError("Deprecation endpoint returned a different runner version.")
        rows.append({"version": version,
                     "registration": deadline(data["registration_deprecates_at"], now),
                     "runtime": deadline(data["runtime_deprecates_at"], now)})
    safe_inventory = [{"id": r["id"], "name": r["name"], "status": r["status"],
                       "version": r.get("version")} for r in inventory]
    unknown = sum(not r["version"] for r in safe_inventory)
    table = "\n".join(f"| {r['version']} | {r['registration']} | {r['runtime']} |" for r in rows)
    report("runner-audit", {"scope": scope, "versions": rows, "inventory": safe_inventory,
                           "unknown_inventory_versions": unknown, "observed_at": iso(now)},
           "## Read-only runner readiness audit\n\n"
           "| Version | Registration | Job runtime |\n| --- | --- | --- |\n" + table +
           f"\n\nInventory requested: **{include_inventory}**. Runners without a version: **{unknown}**.\n\n"
           "2.329.0 is the registration minimum, NOT the runtime minimum. "
           "No runner was registered, downgraded, stopped, or deleted.")


def verify_cache(api: GitHub, base_key: str) -> None:
    if not re.fullmatch(r"dxc-oh-\d+-\d+", base_key):
        raise ValueError("Unexpected demo cache key prefix.")
    observed: dict[str, bool] = {}
    for attempt in range(6):
        observed = {}
        for mode in MODES:
            key = f"{base_key}-{mode}"
            data = api.call(f"/repos/{api.repo}/actions/caches?" + urlencode({"key": key}))
            observed[mode] = any(c["key"] == key for c in data["actions_caches"])
        if all(observed[mode] == allowed[1] for mode, allowed in MODES.items()):
            break
        if attempt < 5:
            clock.sleep(5)
    rows = [{"mode": mode, "expected_save": allowed[1], "cache_present": observed[mode]}
            for mode, allowed in MODES.items()]
    table = "\n".join(f"| {r['mode']} | {r['expected_save']} | {r['cache_present']} |" for r in rows)
    report("cache-verification", rows, "## Service-enforced cache saves\n\n"
           "| Caller mode | Save permitted | Cache actually exists |\n| --- | --- | --- |\n" +
           table + "\n\nThe called workflow requests write, but cannot exceed its caller's cache access.")
    if any(r["expected_save"] != r["cache_present"] for r in rows):
        raise RuntimeError("Cache state did not match the four permission modes.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    policy = sub.add_parser("policy")
    policy.add_argument("--operation", required=True, choices=[
        "inspect", "create-evaluate", "create-active", "activate",
        "probe-allowed", "probe-blocked", "cleanup"])
    policy.add_argument("--policy-id", default="")
    seed = sub.add_parser("artifact-seed")
    seed.add_argument("--artifact-id", required=True)
    artifact = sub.add_parser("artifact-inspect")
    artifact.add_argument("--receipt", required=True)
    artifact.add_argument("--seed-run-id", required=True)
    query = sub.add_parser("reporting")
    query.add_argument("--start-date", required=True)
    query.add_argument("--end-date", required=True)
    query.add_argument("--per-page", type=int, default=10)
    fleet = sub.add_parser("runners")
    fleet.add_argument("--versions", required=True)
    fleet.add_argument("--scope", choices=["repository", "organization"], default="repository")
    fleet.add_argument("--organization", default="")
    fleet.add_argument("--include-inventory", action="store_true")
    cache = sub.add_parser("cache-check")
    cache.add_argument("--base-key", required=True)
    args = parser.parse_args()
    api = GitHub(os.environ.get("GITHUB_REPOSITORY", ""), os.environ.get("GITHUB_TOKEN", ""))
    now = datetime.now(UTC)
    if args.command == "policy":
        run_policy(api, args.operation, args.policy_id)
    elif args.command == "artifact-seed":
        artifact_receipt(api, args.artifact_id)
    elif args.command == "artifact-inspect":
        receipt = json.loads(Path(args.receipt).read_text(encoding="utf-8"))
        inspect_artifact(api, receipt, args.seed_run_id, now)
    elif args.command == "reporting":
        reporting(api, args.start_date, args.end_date, args.per_page)
    elif args.command == "runners":
        runner_audit(api, args.versions, args.scope, args.organization, args.include_inventory, now)
    elif args.command == "cache-check":
        verify_cache(api, args.base_key)


if __name__ == "__main__":
    try:
        main()
    except (APIError, RuntimeError, ValueError, KeyError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)

