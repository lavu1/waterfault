# WaterFault

WaterFault is a local, SQLite-backed prototype for a community coordinator handling repeated reports about the same water-service fault. It keeps every original report, makes duplicate linking a human decision, enforces one active repair crew per issue, and records the resolution history.

Target: [Practice to Create [Feedback To All Projects!]](https://practicetocreate.devpost.com/) | [Official rules](https://practicetocreate.devpost.com/rules)  
Track: Open-ended problem solution / ideathon  
Deadline: **25 September 2026 at 18:45 Africa/Lusaka (UTC+2)**, checked 11 September 2026.  
Eligibility: **Conditional.** The event is for students aged 13+; student status has not been confirmed.

This is a fictional demonstration. It is not connected to a water utility and does not dispatch real crews.

## Run the prototype

Python 3.10 or newer is the only requirement.

```sh
cd waterfault
python3 server.py --port 5183
```

Open `http://127.0.0.1:5183`. The server creates `.data/waterfault.db` from the normalized schema and synthetic seed data on first run. State survives restarts.

To restore the fictional demonstration data:

```sh
python3 server.py --port 5183 --reset
```

## Test the workflow

```sh
python3 -m unittest discover -s tests -v
```

The test suite covers duplicate suggestions and confirmed linking, rejection of a second active assignment, persisted resolution history, and the HTTP API.

## Demonstration flow

1. Review two unlinked reports that resemble the Demo Market Gate issue.
2. Confirm each duplicate link; the originals remain visible under the shared issue.
3. Observe that a second crew cannot be assigned while Demo Crew A is active.
4. Resolve the issue and verify that the completed assignment and event history remain.
5. Add a new report to show that the workflow persists real records in SQLite.

## Project map

- `server.py`: dependency-free HTTP and JSON API server.
- `waterfault.py`: validated domain operations and SQLite persistence.
- `web/`: responsive single-screen coordinator interface.
- `db/`: normalized schema, synthetic seed data, and constraint checks.
- `tests/`: automated workflow and API tests.
- `submission/`: overview copy, demo script, sources, disclosure, and checklist.
- `docs/`: specification, architecture, access caveats, and build record.

## Submission status

The application and draft presentation materials are prepared locally. No hosting, recording, public repository publication, or Devpost submission has been performed. The supplied historical Code with Kiro management URL currently returns a Devpost 404; public Kiro rules show that event closed on 15 September 2025, so it must not be treated as the active submission target.

