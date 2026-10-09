"""Offline tests use synthetic responses, never customer data or live tokens."""

from contextlib import redirect_stdout
from datetime import datetime, timedelta
from io import StringIO
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from demo_api import (APIError, GitHub, MODES, POLICY_TARGET, UTC, assert_demo_policy,
                      count_requires_split, deadline, enumerate_runs,
                      inspect_artifact, policy_body, repository, runner_audit,
                      timestamp, verify_cache)


class FakeAPI:
    repo = "demo-owner/demo-repository"

    def __init__(self, responder):
        self.responder = responder
        self.requests = 0

    def call(self, path, method="GET", body=None):
        self.requests += 1
        return self.responder(path, method, body)

    def pages(self, path, key):
        return self.call(path)[key]


class WorkingDirectoryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous = Path.cwd()
        os.chdir(self.temp.name)
        self.env = patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": ""})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        os.chdir(self.previous)
        self.temp.cleanup()


class TestInputs(unittest.TestCase):
    def test_repository_rejects_path_or_url_injection(self):
        self.assertEqual(repository("owner/repo-name"), "owner/repo-name")
        for value in ("https://github.com/o/r", "o/r?token=x", "o/r/../../users", ""):
            with self.assertRaises(ValueError):
                repository(value)

    def test_missing_credential_is_error(self):
        with self.assertRaisesRegex(ValueError, "credential"):
            GitHub("o/r", "")

    def test_timezones_required_and_normalized(self):
        self.assertEqual(timestamp("2026-10-09T11:00:00-07:00").hour, 18)
        with self.assertRaises(ValueError):
            timestamp("2026-10-09T11:00:00")

    def test_counts_at_retrieval_cap_are_not_assumed_complete(self):
        for count in (1000, 2500, 9999, "2,500+", "1000"):
            self.assertTrue(count_requires_split(count))
        for count in (0, 42, 999):
            self.assertFalse(count_requires_split(count))
        for invalid in (None, True, -1, "many"):
            with self.assertRaises(ValueError):
                count_requires_split(invalid)

    def test_policy_is_scoped_to_one_harmless_workflow(self):
        body = policy_body("dxc-office-hour-demo-2-123-1", "evaluate")
        assert_demo_policy(body)
        self.assertEqual(body["conditions"]["workflow_path"]["include"], [POLICY_TARGET])
        self.assertEqual(body["rules"][0]["parameters"]["allowed_events"], ["workflow_dispatch"])
        for change in ({"name": "customer-production-policy"}, {"conditions": {}}):
            with self.assertRaises(ValueError):
                assert_demo_policy({**body, **change})

    def test_registration_and_runtime_dates_are_independent(self):
        now = timestamp("2026-10-13T12:00:00Z")
        self.assertIn("Deadline passed", deadline("2026-09-29T00:00:00Z", now))
        self.assertIn("Upcoming", deadline("2026-11-01T00:00:00Z", now))
        self.assertIn("not guaranteed", deadline(None, now))


class TestReporting(unittest.TestCase):
    start = datetime(2026, 10, 1, tzinfo=UTC)
    end = datetime(2026, 10, 3, tzinfo=UTC)

    def test_small_repository_paginated_and_deduplicated(self):
        def respond(path, method, body):
            page = int(parse_qs(urlsplit(path).query)["page"][0])
            rows = {1: [self.row(1), self.row(2)], 2: [self.row(3)]}[page]
            return {"total_count": 3, "workflow_runs": rows}
        api = FakeAPI(respond)
        rows, windows = enumerate_runs(api, self.start, self.end, per_page=2)
        self.assertEqual([r["id"] for r in rows], [1, 2, 3])
        self.assertEqual(api.requests, 2)
        self.assertFalse(windows[0]["split"])

    @staticmethod
    def row(number):
        return {"id": number, "created_at": f"2026-10-01T00:00:0{number}Z",
                "name": "synthetic offline run", "conclusion": "success"}

    def test_large_count_bisects_into_nonoverlapping_time_windows(self):
        queries = []
        def respond(path, method, body):
            query = parse_qs(urlsplit(path).query)["created"][0]
            queries.append(query)
            if len(queries) == 1:
                return {"total_count": "2,500+", "workflow_runs": []}
            if len(queries) == 2:
                return {"total_count": 1, "workflow_runs": [self.row(1)]}
            return {"total_count": 0, "workflow_runs": []}
        rows, windows = enumerate_runs(FakeAPI(respond), self.start, self.end)
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(windows), 3)
        self.assertTrue(windows[0]["split"])
        self.assertTrue(queries[1].endswith("2026-10-01T23:59:59Z"))
        self.assertTrue(queries[2].startswith("2026-10-02T00:00:00Z"))

    def test_saturated_single_second_fails_instead_of_truncating(self):
        api = FakeAPI(lambda *args: {"total_count": 1001, "workflow_runs": []})
        with self.assertRaisesRegex(RuntimeError, "completeness"):
            enumerate_runs(api, self.start, self.start + timedelta(seconds=1))

    def test_wrong_window_run_fails(self):
        api = FakeAPI(lambda *args: {"total_count": 1, "workflow_runs": [
            {"id": 1, "created_at": "2026-09-01T00:00:00Z"}]})
        with self.assertRaisesRegex(RuntimeError, "outside"):
            enumerate_runs(api, self.start, self.end)

    def test_request_budget_enforced_before_network(self):
        api = GitHub("o/r", "synthetic-not-a-token", max_requests=0)
        with self.assertRaisesRegex(RuntimeError, "budget"):
            api.call("/repos/o/r/actions/runs")


class TestArtifact(WorkingDirectoryTest):
    receipt = {"repository": FakeAPI.repo, "seed_run_id": 123, "artifact_id": 456,
               "artifact_name": "expiry-demo-123", "expires_at": "2026-10-10T00:00:00Z"}

    def api(self, present=False, direct_status=404):
        def respond(path, method, body):
            if path.endswith("/runs/123"):
                return {"conclusion": "success",
                        "path": ".github/workflows/demo-3-artifact-expiry.yml"}
            if path.endswith("/artifacts/456"):
                if direct_status == 200:
                    return {"id": 456}
                raise APIError(direct_status, "synthetic offline response")
            return {"artifacts": [{"id": 456}] if present else []}
        return FakeAPI(respond)

    def test_inspect_before_expiry_fails(self):
        with self.assertRaisesRegex(RuntimeError, "NOT READY"):
            inspect_artifact(self.api(), self.receipt, "123", timestamp("2026-10-09T00:00:00Z"))

    def test_absent_artifact_requires_list_and_get_evidence(self):
        with redirect_stdout(StringIO()):
            inspect_artifact(self.api(), self.receipt, "123", timestamp("2026-10-13T00:00:00Z"))
        data = json.loads(Path("demo-output/artifact-observation.json").read_text())
        self.assertFalse(data["present_in_list"])
        self.assertTrue(data["get_returns_404"])
        self.assertIn("manual deletion", data["attribution"])

    def test_existing_artifact_not_success_shaped(self):
        with redirect_stdout(StringIO()):
            with self.assertRaisesRegex(RuntimeError, "NOT READY"):
                inspect_artifact(self.api(True, 200), self.receipt, "123",
                                 timestamp("2026-10-13T00:00:00Z"))

    def test_forbidden_is_not_misreported_as_expired(self):
        with self.assertRaises(APIError):
            inspect_artifact(self.api(direct_status=403), self.receipt, "123",
                             timestamp("2026-10-13T00:00:00Z"))

    def test_receipt_from_other_repository_rejected(self):
        with self.assertRaises(ValueError):
            inspect_artifact(self.api(), {**self.receipt, "repository": "other/repo"},
                             "123", timestamp("2026-10-13T00:00:00Z"))


class TestCacheAndRunner(WorkingDirectoryTest):
    def test_all_four_cache_modes_checked_against_actual_inventory(self):
        def respond(path, method, body):
            key = parse_qs(urlsplit(path).query)["key"][0]
            mode = key.removeprefix("dxc-oh-1-1-")
            return {"actions_caches": [{"key": key}] if MODES[mode][1] else []}
        with redirect_stdout(StringIO()):
            verify_cache(FakeAPI(respond), "dxc-oh-1-1")
        self.assertEqual(len(json.loads(Path("demo-output/cache-verification.json").read_text())), 4)

    def test_runner_audit_reports_unknown_version_without_guessing(self):
        def respond(path, method, body):
            if "/deprecations/" in path:
                return {"runner_version": path.rsplit("/", 1)[1],
                        "registration_deprecates_at": "2026-09-29T00:00:00Z",
                        "runtime_deprecates_at": None}
            return {"runners": [{"id": 1, "name": "synthetic-runner", "status": "offline",
                                 "version": None}]}
        with redirect_stdout(StringIO()):
            runner_audit(FakeAPI(respond), "2.329.0", "repository", "", True,
                         timestamp("2026-10-13T00:00:00Z"))
        data = json.loads(Path("demo-output/runner-audit.json").read_text())
        self.assertEqual(data["unknown_inventory_versions"], 1)
        self.assertIn("not guaranteed", data["versions"][0]["runtime"])


class TestWorkflowStructure(unittest.TestCase):
    def test_workflows_have_safe_triggers_permissions_timeout_and_pins(self):
        files = list((ROOT / ".github" / "workflows").glob("*.yml"))
        self.assertGreaterEqual(len(files), 8)
        for file in files:
            with self.subTest(file=file.name):
                data = yaml.load(file.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
                self.assertIn("permissions", data)
                self.assertNotIn("pull_request_target", data["on"])
                self.assertNotIn("schedule", data["on"])
                for job in data["jobs"].values():
                    if "runs-on" in job:
                        self.assertIn("timeout-minutes", job)
                    for step in job.get("steps", []):
                        if use := step.get("uses"):
                            self.assertRegex(use, r"^actions/[\w/-]+@[0-9a-f]{40}$")
                        if script := step.get("run"):
                            self.assertNotIn("${{ inputs.", script)
                            self.assertNotIn("${{ secrets.", script)


if __name__ == "__main__":
    unittest.main()

