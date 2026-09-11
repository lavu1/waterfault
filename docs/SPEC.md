# Task specification

## User and outcome

A community coordinator handling repeated reports about the same water-service fault.

Report a fault, link duplicate reports to one issue, assign a team and show the resolution history.

## Coordinator duties

1. Accept a short report and a broad location/landmark.
2. Suggest possible duplicate issues for human review.
3. Link related reports without deleting the originals.
4. Assign one active repair team and display progress.
5. Record status changes and show unresolved issues.

## Rules

- Do not claim an official water-utility connection or send reports to a utility.
- Duplicate suggestions require coordinator confirmation.
- Use synthetic landmarks and reporter labels in the public demo.
- Keep original reports and their relationship to the shared issue.
- Enforce one active assignment per issue; retain completed assignments.

## Acceptance criteria

- [x] Two reports can refer to one issue without losing either report.
- [x] One active assignment is shown and duplicate active assignments are rejected.
- [x] Resolution is persisted and appears in the event history.
- [x] The interface and demo script distinguish the prototype from an operational utility service.

## Interaction contract

- A newly logged report starts unlinked and may show ranked duplicate suggestions.
- Linking requires an explicit coordinator action and adds an event to the shared issue.
- An assigned issue exposes the active crew and prevents another assignment.
- Resolution completes the active assignment instead of deleting it.
- Refreshing or restarting the server preserves state in SQLite.
- Resetting the demo is a deliberate action that restores only the synthetic seed data.

## Demonstration value

Show how three incoming reports become one actionable issue with a clear owner and visible resolution.

Use the [sample scenarios](../data/scenarios.json) to define expected behavior. Sample organizations, records, timestamps, and landmarks are fictional. No measured impact, automatic dispatch, or live utility integration is claimed.
