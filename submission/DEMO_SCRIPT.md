# WaterFault presentation script

Use the core cut for a presentation just under three minutes. Add the optional context segment to meet the active event's 3-5 minute requirement. Do not exceed five minutes.

## Core cut: about 2 minutes 50 seconds

### 0:00-0:25 - Problem

"Several people can report one leaking pipe using different words and nearby landmarks. If each report becomes a separate job, repair work fragments and no one has a clear view of ownership. WaterFault is a coordinator prototype that turns those repeated reports into one accountable repair record."

Show the board header, summary numbers, and prototype notice.

### 0:25-0:55 - Report intake

"The intake keeps a reporter label, landmark, and observation. I am using fictional data, and this prototype does not send anything to a utility. When I log this report, WaterFault saves it to SQLite before suggesting any duplicate."

Submit the prefilled Demo reporter D form. Point out the saved report reference and duplicate suggestion.

### 0:55-1:35 - Human-confirmed duplicate linking

"The suggestion is advisory. Similar landmark and fault words explain why this issue may match, but a coordinator must confirm the link. I will link the two waiting reports. Notice that their original references, reporters, descriptions, and landmarks remain visible under the shared issue."

Confirm the two seeded duplicate reports. Show the report count under the shared issue and the new history events.

### 1:35-2:10 - Clear ownership

"The issue already belongs to Demo Crew A. WaterFault allows only one active team per issue, so the assignment control is blocked while that team is working. This is enforced in the application and by a partial unique index in SQLite, not only by the button."

Show the active crew card and disabled assignment control.

### 2:10-2:38 - Resolution history

"When the coordinator marks the repair resolved, WaterFault completes the active assignment instead of deleting it, changes the issue status, and records a resolution event. The history remains after refresh or server restart."

Select "Mark repair resolved" and show the resolved status and newest timeline entry.

### 2:38-2:50 - Close

"WaterFault's value is simple: preserve every voice, coordinate one repair, and make responsibility visible. The next step would be a small authorized pilot with privacy controls and real coordinator feedback."

## Optional active-event context: add about 35 seconds

Insert after the problem segment:

"The idea is deliberately narrow and plausible. It does not attempt automatic leak detection or claim an official integration. It solves the coordination gap after reports arrive: duplicates are reviewed by a person, one team owns the issue, and each state change remains auditable. The visual system also separates pending review, active ownership, and resolution so the workflow can be understood quickly."

With this segment, the full presentation is about 3 minutes 25 seconds.

## Recording checklist

- Keep the browser zoom at 100% and use a desktop viewport wide enough to show the issue and ownership columns.
- Reset the demo immediately before recording.
- Avoid copyrighted music, real resident details, and third-party utility logos.
- Show the real working interface, not static screenshots.
- State the prototype and synthetic-data caveat aloud.
- Add the final prototype and repository links to Devpost only after they are public and tested.
