"""WaterFault domain operations and SQLite persistence."""

from __future__ import annotations

import re
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


class DomainError(Exception):
    """A safe, user-facing domain failure."""

    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.status = status


class WaterFaultStore:
    def __init__(self, database_path: Path | str, project_root: Path | str | None = None) -> None:
        self.database_path = Path(database_path)
        self.project_root = Path(project_root or Path(__file__).resolve().parent)
        self._lock = threading.RLock()

    def initialize(self, reset: bool = False) -> None:
        with self._lock:
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            if reset and self.database_path.exists():
                self.database_path.unlink()

            with self._connection() as connection:
                has_schema = connection.execute(
                    "SELECT 1 FROM sqlite_schema WHERE type = 'table' AND name = 'issues'"
                ).fetchone()
                if not has_schema:
                    connection.executescript((self.project_root / "db" / "schema.sql").read_text())
                    connection.executescript((self.project_root / "db" / "seed.sql").read_text())
                    connection.execute("PRAGMA optimize")

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        with self._lock, self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                yield connection
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def _require_text(payload: dict[str, Any], key: str, maximum: int = 180) -> str:
        value = str(payload.get(key, "")).strip()
        if not value:
            raise DomainError(f"{key.replace('_', ' ').capitalize()} is required.")
        if len(value) > maximum:
            raise DomainError(f"{key.replace('_', ' ').capitalize()} must be {maximum} characters or fewer.")
        return value

    @staticmethod
    def _tokens(value: str) -> set[str]:
        replacements = {"leaking": "leak", "leaked": "leak", "pipes": "pipe", "entrance": "gate"}
        words = re.findall(r"[a-z0-9]+", value.lower())
        ignored = {"a", "at", "by", "near", "the", "to", "of", "and", "water", "demo"}
        return {replacements.get(word, word) for word in words if word not in ignored}

    @staticmethod
    def _overlap(left: set[str], right: set[str]) -> float:
        if not left or not right:
            return 0.0
        return len(left & right) / len(left | right)

    def _suggestions_for(self, connection: sqlite3.Connection, report: dict[str, Any]) -> list[dict[str, Any]]:
        candidates = connection.execute(
            """
            SELECT i.id, i.title, i.landmark, i.status,
                   COALESCE(GROUP_CONCAT(r.description, ' '), '') AS report_text
            FROM issues i
            LEFT JOIN reports r ON r.issue_id = i.id
            WHERE i.status != 'resolved'
            GROUP BY i.id
            ORDER BY i.id
            """
        ).fetchall()
        report_landmark = self._tokens(str(report["reported_landmark"]))
        report_description = self._tokens(str(report["description"]))
        suggestions: list[dict[str, Any]] = []

        for candidate in candidates:
            location_score = self._overlap(report_landmark, self._tokens(candidate["landmark"]))
            description_score = self._overlap(
                report_description,
                self._tokens(f"{candidate['title']} {candidate['report_text']}"),
            )
            score = round((location_score * 0.68) + (description_score * 0.32), 2)
            if score < 0.20:
                continue
            reasons = []
            if location_score:
                reasons.append("landmark words overlap")
            if description_score:
                reasons.append("fault description is similar")
            suggestions.append(
                {
                    "issue_id": candidate["id"],
                    "title": candidate["title"],
                    "landmark": candidate["landmark"],
                    "status": candidate["status"],
                    "score": score,
                    "reason": " and ".join(reasons),
                }
            )

        return sorted(suggestions, key=lambda item: (-item["score"], item["issue_id"]))

    def get_state(self) -> dict[str, Any]:
        with self._connection() as connection:
            issue_rows = connection.execute(
                """
                SELECT i.id, i.title, i.landmark, i.status, i.priority,
                       z.id AS zone_id, z.name AS zone_name
                FROM issues i
                JOIN zones z ON z.id = i.zone_id
                ORDER BY CASE i.status WHEN 'assigned' THEN 0 WHEN 'open' THEN 1 ELSE 2 END, i.id
                """
            ).fetchall()
            report_rows = connection.execute("SELECT * FROM reports ORDER BY id").fetchall()
            assignment_rows = connection.execute(
                """
                SELECT a.id, a.issue_id, a.crew_id, c.name AS crew_name,
                       a.assigned_at, a.completed_at
                FROM assignments a
                JOIN crews c ON c.id = a.crew_id
                ORDER BY a.id
                """
            ).fetchall()
            event_rows = connection.execute(
                "SELECT * FROM issue_events ORDER BY datetime(created_at) DESC, id DESC"
            ).fetchall()
            crew_rows = connection.execute("SELECT id, name FROM crews ORDER BY name").fetchall()

            issues = [dict(row) for row in issue_rows]
            reports = [dict(row) for row in report_rows]
            assignments = [dict(row) for row in assignment_rows]
            events = [dict(row) for row in event_rows]

            for issue in issues:
                issue["reports"] = [report for report in reports if report["issue_id"] == issue["id"]]
                issue["assignments"] = [
                    assignment for assignment in assignments if assignment["issue_id"] == issue["id"]
                ]
                issue["active_assignment"] = next(
                    (
                        assignment
                        for assignment in issue["assignments"]
                        if assignment["completed_at"] is None
                    ),
                    None,
                )
                issue["events"] = [event for event in events if event["issue_id"] == issue["id"]]

            unlinked_reports = []
            for report in reports:
                if report["issue_id"] is None:
                    report_copy = dict(report)
                    report_copy["suggestions"] = self._suggestions_for(connection, report_copy)
                    unlinked_reports.append(report_copy)

            return {
                "summary": {
                    "unresolved_issues": sum(issue["status"] != "resolved" for issue in issues),
                    "unlinked_reports": len(unlinked_reports),
                    "active_crews": sum(issue["active_assignment"] is not None for issue in issues),
                    "total_reports": len(reports),
                },
                "issues": issues,
                "unlinked_reports": unlinked_reports,
                "crews": [dict(row) for row in crew_rows],
                "prototype_notice": "Synthetic local demonstration. No utility connection or real dispatch.",
            }

    def create_report(self, payload: dict[str, Any]) -> dict[str, Any]:
        reporter_label = self._require_text(payload, "reporter_label", 80)
        description = self._require_text(payload, "description", 240)
        landmark = self._require_text(payload, "reported_landmark", 120)

        with self._transaction() as connection:
            next_id = connection.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM reports").fetchone()[0]
            source_ref = f"DEMO-REPORT-{next_id:03d}"
            cursor = connection.execute(
                """
                INSERT INTO reports (source_ref, reporter_label, description, reported_landmark)
                VALUES (?, ?, ?, ?)
                """,
                (source_ref, reporter_label, description, landmark),
            )
            report = dict(
                connection.execute("SELECT * FROM reports WHERE id = ?", (cursor.lastrowid,)).fetchone()
            )
            suggestions = self._suggestions_for(connection, report)
        return {"report": report, "suggestions": suggestions}

    def link_report(self, report_id: int, issue_id: int) -> dict[str, Any]:
        with self._transaction() as connection:
            report = connection.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
            if report is None:
                raise DomainError("Report not found.", 404)
            if report["issue_id"] is not None:
                raise DomainError("This report is already linked to an issue.", 409)
            issue = connection.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
            if issue is None:
                raise DomainError("Issue not found.", 404)
            if issue["status"] == "resolved":
                raise DomainError("A new report cannot be linked to a resolved issue.", 409)

            connection.execute("UPDATE reports SET issue_id = ? WHERE id = ?", (issue_id, report_id))
            connection.execute(
                "INSERT INTO issue_events (issue_id, event_type, detail) VALUES (?, 'report_linked', ?)",
                (issue_id, f"Coordinator linked {report['source_ref']} after duplicate review."),
            )
        return {"report_id": report_id, "issue_id": issue_id, "linked": True}

    def assign_crew(self, issue_id: int, crew_id: int) -> dict[str, Any]:
        with self._transaction() as connection:
            issue = connection.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
            if issue is None:
                raise DomainError("Issue not found.", 404)
            if issue["status"] == "resolved":
                raise DomainError("Resolved issues cannot receive a new crew.", 409)
            active = connection.execute(
                """
                SELECT a.id, c.name FROM assignments a
                JOIN crews c ON c.id = a.crew_id
                WHERE a.issue_id = ? AND a.completed_at IS NULL
                """,
                (issue_id,),
            ).fetchone()
            if active is not None:
                raise DomainError(f"{active['name']} is already the active crew for this issue.", 409)
            crew = connection.execute("SELECT * FROM crews WHERE id = ?", (crew_id,)).fetchone()
            if crew is None:
                raise DomainError("Crew not found.", 404)

            cursor = connection.execute(
                "INSERT INTO assignments (issue_id, crew_id) VALUES (?, ?)", (issue_id, crew_id)
            )
            connection.execute("UPDATE issues SET status = 'assigned' WHERE id = ?", (issue_id,))
            connection.execute(
                "INSERT INTO issue_events (issue_id, event_type, detail) VALUES (?, 'crew_assigned', ?)",
                (issue_id, f"{crew['name']} assigned to investigate."),
            )
        return {"assignment_id": cursor.lastrowid, "issue_id": issue_id, "crew": crew["name"]}

    def resolve_issue(self, issue_id: int) -> dict[str, Any]:
        with self._transaction() as connection:
            issue = connection.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
            if issue is None:
                raise DomainError("Issue not found.", 404)
            if issue["status"] == "resolved":
                raise DomainError("This issue is already resolved.", 409)
            active = connection.execute(
                """
                SELECT a.id, c.name FROM assignments a
                JOIN crews c ON c.id = a.crew_id
                WHERE a.issue_id = ? AND a.completed_at IS NULL
                """,
                (issue_id,),
            ).fetchone()
            if active is None:
                raise DomainError("Assign a crew before resolving the issue.", 409)

            connection.execute(
                "UPDATE assignments SET completed_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now') WHERE id = ?",
                (active["id"],),
            )
            connection.execute("UPDATE issues SET status = 'resolved' WHERE id = ?", (issue_id,))
            connection.execute(
                "INSERT INTO issue_events (issue_id, event_type, detail) VALUES (?, 'issue_resolved', ?)",
                (issue_id, f"{active['name']} completed the repair; coordinator marked the issue resolved."),
            )
        return {"issue_id": issue_id, "status": "resolved", "completed_crew": active["name"]}
