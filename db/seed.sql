-- Fictional area, reports and crews; no connection to a water utility.
INSERT INTO zones VALUES (1,'Demo North');
INSERT INTO issues VALUES (1,1,'Leaking pipe','Demo Market Gate','assigned','normal');
INSERT INTO reports (id,source_ref,issue_id,reporter_label,description,reported_landmark) VALUES
 (1,'DEMO-REPORT-001',1,'Demo reporter A','Water leaking at the market gate','Demo Market Gate'),
 (2,'DEMO-REPORT-002',NULL,'Demo reporter B','Pipe leaking near the entrance','Demo Market entrance'),
 (3,'DEMO-REPORT-003',NULL,'Demo reporter C','Steady water leak beside the public tap','Demo Market public tap');
INSERT INTO crews VALUES (1,'Demo Crew A'),(2,'Demo Crew B');
INSERT INTO assignments (id,issue_id,crew_id,assigned_at) VALUES (1,1,1,'2026-09-11T10:00:00+02:00');
INSERT INTO issue_events (id,issue_id,event_type,detail,created_at) VALUES
 (1,1,'issue_created','Coordinator opened the issue from DEMO-REPORT-001.','2026-09-11T09:45:00+02:00'),
 (2,1,'crew_assigned','Demo Crew A assigned to investigate.','2026-09-11T10:00:00+02:00');
