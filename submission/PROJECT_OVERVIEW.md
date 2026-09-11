# WaterFault submission draft

## One-line description

WaterFault helps a community coordinator turn repeated reports about the same water-service fault into one accountable repair record without losing the original reports.

## The problem

When residents report the same leak using different words or nearby landmarks, coordinators can mistake the reports for separate faults. Work becomes fragmented, responsibility is unclear, and residents cannot see whether the underlying issue was assigned or resolved.

## The solution

WaterFault preserves every incoming report, suggests possible duplicate issues, and requires a person to confirm each link. Related reports then appear under one issue with one active repair team and a visible event history. The current prototype demonstrates the workflow with fictional landmarks and crews; it is not connected to a utility.

## What the prototype does

- Logs a reporter label, landmark, and short observation to SQLite.
- Suggests likely duplicate issues using transparent landmark and description overlap.
- Keeps the original report when a coordinator confirms a duplicate.
- Enforces one active team per issue in both domain logic and the database.
- Completes, rather than deletes, an assignment when the issue is resolved.
- Persists the status and event history across browser and server restarts.

## How it is implemented

The local application uses browser-native HTML, CSS, and JavaScript with a dependency-free Python HTTP server. A normalized SQLite database stores zones, issues, reports, crews, assignments, and events. Validated domain operations write inside transactions, and a partial unique index prevents two active assignments for the same issue. Automated tests cover the main workflow and API.

## Why this approach is plausible

The prototype focuses on coordination rather than claiming to detect leaks or integrate with a utility. Its smallest valuable behavior is making duplicate review explicit while giving each shared issue a clear owner and durable history. A production pilot could add authentication, privacy controls, real service-area data, multilingual intake, notifications, and an authorized utility integration.

## Demonstration claim

The demonstration shows three synthetic incoming reports becoming one actionable issue with one owner and a retained resolution trail. It does not claim measured impact, live dispatch, or official utility support.

## Event fit and caveat

Target category: open-ended problem solution / ideathon. The active Practice to Create event accepts prototypes and evaluates originality, presentation, visuals, and plausibility. Eligibility remains conditional because the event is limited to students aged 13+ and the entrant's student status has not been confirmed.

## Suggested tags

`civic-tech`, `water`, `workflow`, `sqlite`, `community`, `prototype`
