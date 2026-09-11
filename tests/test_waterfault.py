import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from server import PROJECT_ROOT, create_server
from waterfault import DomainError, WaterFaultStore


class WaterFaultWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "waterfault.db"
        self.store = WaterFaultStore(self.database_path, PROJECT_ROOT)
        self.store.initialize()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_seed_exposes_two_duplicate_candidates(self) -> None:
        state = self.store.get_state()
        self.assertEqual(state["summary"]["total_reports"], 3)
        self.assertEqual(state["summary"]["unlinked_reports"], 2)
        self.assertTrue(all(report["suggestions"] for report in state["unlinked_reports"]))

    def test_confirmed_duplicate_link_preserves_both_reports(self) -> None:
        self.store.link_report(2, 1)
        state = self.store.get_state()
        issue = state["issues"][0]
        self.assertEqual([report["id"] for report in issue["reports"]], [1, 2])
        self.assertEqual(state["summary"]["total_reports"], 3)
        self.assertEqual(issue["events"][0]["event_type"], "report_linked")

    def test_second_active_assignment_is_rejected(self) -> None:
        with self.assertRaises(DomainError) as context:
            self.store.assign_crew(1, 2)
        self.assertEqual(context.exception.status, 409)
        self.assertIn("already the active crew", str(context.exception))

    def test_resolution_and_completed_assignment_persist(self) -> None:
        self.store.resolve_issue(1)
        reopened = WaterFaultStore(self.database_path, PROJECT_ROOT)
        state = reopened.get_state()
        issue = state["issues"][0]
        self.assertEqual(issue["status"], "resolved")
        self.assertIsNone(issue["active_assignment"])
        self.assertIsNotNone(issue["assignments"][0]["completed_at"])
        self.assertEqual(issue["events"][0]["event_type"], "issue_resolved")

    def test_http_api_creates_a_persisted_report(self) -> None:
        server = create_server(port=0, database_path=self.database_path)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"
        try:
            request = Request(
                f"{base_url}/api/reports",
                data=json.dumps(
                    {
                        "reporter_label": "Demo reporter D",
                        "reported_landmark": "Demo Market side gate",
                        "description": "Water leaking beside the market gate",
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=2) as response:
                created = json.load(response)
            self.assertEqual(response.status, 201)
            self.assertTrue(created["suggestions"])

            with urlopen(f"{base_url}/api/state", timeout=2) as response:
                state = json.load(response)
            self.assertEqual(state["summary"]["total_reports"], 4)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
