PRAGMA foreign_keys = ON;
CREATE TABLE zones (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
CREATE TABLE issues (
 id INTEGER PRIMARY KEY, zone_id INTEGER NOT NULL REFERENCES zones(id),
 title TEXT NOT NULL, landmark TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','assigned','resolved')),
 priority TEXT NOT NULL DEFAULT 'normal' CHECK(priority IN ('normal','urgent'))
);
CREATE TABLE reports (
 id INTEGER PRIMARY KEY, source_ref TEXT NOT NULL UNIQUE,
 issue_id INTEGER REFERENCES issues(id),
 reporter_label TEXT NOT NULL, description TEXT NOT NULL, reported_landmark TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE crews (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
CREATE TABLE assignments (
 id INTEGER PRIMARY KEY, issue_id INTEGER NOT NULL REFERENCES issues(id),
 crew_id INTEGER NOT NULL REFERENCES crews(id),
 assigned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, completed_at TEXT,
 CHECK(completed_at IS NULL OR datetime(completed_at) >= datetime(assigned_at))
);
CREATE UNIQUE INDEX one_active_assignment_per_issue ON assignments(issue_id) WHERE completed_at IS NULL;
CREATE TABLE issue_events (
 id INTEGER PRIMARY KEY, issue_id INTEGER NOT NULL REFERENCES issues(id),
 event_type TEXT NOT NULL, detail TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX reports_issue_idx ON reports(issue_id);
CREATE INDEX issues_zone_idx ON issues(zone_id);
CREATE INDEX assignments_crew_idx ON assignments(crew_id);
CREATE INDEX issue_events_issue_created_idx ON issue_events(issue_id, created_at);
