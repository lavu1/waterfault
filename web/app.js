const elements = {
  metrics: document.querySelector("#metrics"),
  inbox: document.querySelector("#inbox"),
  inboxCount: document.querySelector("#inbox-count"),
  issueBoard: document.querySelector("#issue-board"),
  assignmentPanel: document.querySelector("#assignment-panel"),
  timeline: document.querySelector("#timeline"),
  reportForm: document.querySelector("#report-form"),
  resetButton: document.querySelector("#reset-demo"),
  toast: document.querySelector("#toast"),
};

let boardState = null;
let toastTimer = null;

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatDate(value) {
  if (!value) return "Pending";
  const date = new Date(value.includes("T") ? value : `${value.replace(" ", "T")}Z`);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function showToast(message, isError = false) {
  window.clearTimeout(toastTimer);
  elements.toast.textContent = message;
  elements.toast.classList.toggle("error", isError);
  elements.toast.classList.add("visible");
  toastTimer = window.setTimeout(() => elements.toast.classList.remove("visible"), 3600);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error || "WaterFault could not complete that action.");
  }
  return payload;
}

async function refresh() {
  boardState = await api("/api/state");
  render();
  return boardState;
}

function renderMetrics() {
  const items = [
    [boardState.summary.unresolved_issues, "Unresolved issues"],
    [boardState.summary.unlinked_reports, "Reports to review"],
    [boardState.summary.active_crews, "Active repair crews"],
    [boardState.summary.total_reports, "Original reports kept"],
  ];
  elements.metrics.innerHTML = items
    .map(([value, label]) => `<div class="metric"><strong>${value}</strong><span>${label}</span></div>`)
    .join("");
}

function renderInbox() {
  const reports = boardState.unlinked_reports;
  elements.inboxCount.textContent = reports.length;
  if (!reports.length) {
    elements.inbox.innerHTML = '<div class="empty-state">No unlinked reports. Every incoming report has been reviewed.</div>';
    return;
  }

  elements.inbox.innerHTML = reports
    .map((report) => {
      const suggestion = report.suggestions[0];
      const action = suggestion
        ? `<div class="suggestion">
            <div class="suggestion-row">
              <div class="suggestion-copy">
                <strong>Possible match: ${escapeHtml(suggestion.title)}</strong>
                <span>${escapeHtml(suggestion.reason)} at ${escapeHtml(suggestion.landmark)}</span>
                <span class="confidence">${Math.round(suggestion.score * 100)}% signal</span>
              </div>
              <button class="button button-signal button-small" type="button" data-link-report="${report.id}" data-issue-id="${suggestion.issue_id}">Confirm link</button>
            </div>
          </div>`
        : '<div class="suggestion-copy">No likely open issue found. Keep this report unlinked for coordinator review.</div>';
      return `<article class="report-card">
          <div class="report-meta">
            <span>${escapeHtml(report.source_ref)}</span>
            <span>${escapeHtml(report.reporter_label)}</span>
          </div>
          <blockquote>${escapeHtml(report.description)}</blockquote>
          <p class="landmark">Landmark: ${escapeHtml(report.reported_landmark)}</p>
          ${action}
        </article>`;
    })
    .join("");
}

function renderIssue() {
  const issue = boardState.issues[0];
  if (!issue) {
    elements.issueBoard.innerHTML = '<div class="empty-state">No issue has been opened yet.</div>';
    return;
  }
  const linked = issue.reports
    .map(
      (report) => `<div class="linked-report">
        <strong>${escapeHtml(report.source_ref)}<br>${escapeHtml(report.reporter_label)}</strong>
        <p>${escapeHtml(report.description)}<br><span class="landmark">${escapeHtml(report.reported_landmark)}</span></p>
      </div>`,
    )
    .join("");
  elements.issueBoard.innerHTML = `<article class="issue-record">
      <div class="issue-summary">
        <div class="issue-title-row">
          <div>
            <h3>${escapeHtml(issue.title)}</h3>
            <p>${escapeHtml(issue.zone_name)} / ${escapeHtml(issue.landmark)} / ${escapeHtml(issue.priority)} priority</p>
          </div>
          <span class="issue-status ${issue.status === "resolved" ? "resolved" : ""}">${escapeHtml(issue.status)}</span>
        </div>
      </div>
      <div class="linked-reports">${linked || '<div class="empty-state">No reports linked.</div>'}</div>
    </article>`;
}

function initials(name) {
  return name
    .split(/\s+/)
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function renderAssignment() {
  const issue = boardState.issues[0];
  if (!issue) {
    elements.assignmentPanel.innerHTML = '<div class="empty-state">Open an issue before assigning a team.</div>';
    return;
  }
  const active = issue.active_assignment;
  const completed = issue.assignments.find((assignment) => assignment.completed_at);
  const banner = issue.status === "resolved"
    ? `<div class="assignment-banner">
        <span class="crew-monogram">OK</span>
        <div><strong>Repair completed</strong><span>${escapeHtml(completed?.crew_name || "Assigned team")} is retained in the record.</span></div>
      </div>`
    : active
    ? `<div class="assignment-banner">
        <span class="crew-monogram">${escapeHtml(initials(active.crew_name))}</span>
        <div><strong>${escapeHtml(active.crew_name)}</strong><span>Active since ${escapeHtml(formatDate(active.assigned_at))}</span></div>
      </div>`
    : `<div class="assignment-banner"><span class="crew-monogram">?</span><div><strong>No active team</strong><span>This issue is waiting for an owner.</span></div></div>`;

  const options = boardState.crews
    .map((crew) => `<option value="${crew.id}">${escapeHtml(crew.name)}</option>`)
    .join("");
  const assignmentForm = `<form class="assignment-form" id="assignment-form">
      <label>Choose a team<select name="crew_id" ${active || issue.status === "resolved" ? "disabled" : ""}>${options}</select></label>
      <button class="button button-signal" type="submit" ${active || issue.status === "resolved" ? "disabled" : ""}>Assign team</button>
    </form>`;
  const note = issue.status === "resolved"
    ? `<p class="assignment-note">This issue is closed. Reassignment is disabled in this prototype.</p>`
    : active
    ? `<p class="assignment-note">One active assignment is allowed. Complete this repair before assigning another team.</p>`
    : `<p class="assignment-note">Assignment creates a visible ownership event.</p>`;
  const resolve = `<button class="button button-danger" type="button" data-resolve-issue="${issue.id}" ${!active || issue.status === "resolved" ? "disabled" : ""}>Mark repair resolved</button>`;

  elements.assignmentPanel.innerHTML = `${banner}${note}<div class="action-stack">${assignmentForm}${resolve}</div>`;
}

function renderTimeline() {
  const issue = boardState.issues[0];
  if (!issue || !issue.events.length) {
    elements.timeline.innerHTML = '<li class="empty-state">No events recorded.</li>';
    return;
  }
  elements.timeline.innerHTML = issue.events
    .map(
      (event) => `<li class="timeline-item">
        <strong>${escapeHtml(event.event_type.replaceAll("_", " "))}</strong>
        <p>${escapeHtml(event.detail)}</p>
        <time datetime="${escapeHtml(event.created_at)}">${escapeHtml(formatDate(event.created_at))}</time>
      </li>`,
    )
    .join("");
}

function render() {
  renderMetrics();
  renderInbox();
  renderIssue();
  renderAssignment();
  renderTimeline();
}

async function createReport(input) {
  const result = await api("/api/reports", { method: "POST", body: JSON.stringify(input) });
  await refresh();
  return result;
}

async function linkReport(reportId, issueId) {
  const result = await api(`/api/reports/${reportId}/link`, {
    method: "POST",
    body: JSON.stringify({ issue_id: issueId }),
  });
  await refresh();
  return result;
}

async function assignCrew(issueId, crewId) {
  const result = await api(`/api/issues/${issueId}/assign`, {
    method: "POST",
    body: JSON.stringify({ crew_id: crewId }),
  });
  await refresh();
  return result;
}

async function resolveIssue(issueId) {
  const result = await api(`/api/issues/${issueId}/resolve`, { method: "POST", body: "{}" });
  await refresh();
  return result;
}

elements.reportForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const submit = elements.reportForm.querySelector('button[type="submit"]');
  submit.disabled = true;
  try {
    const values = Object.fromEntries(new FormData(elements.reportForm));
    const result = await createReport(values);
    showToast(
      result.suggestions.length
        ? `${result.report.source_ref} saved. A possible duplicate is ready for review.`
        : `${result.report.source_ref} saved for coordinator review.`,
    );
  } catch (error) {
    showToast(error.message, true);
  } finally {
    submit.disabled = false;
  }
});

elements.inbox.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-link-report]");
  if (!button) return;
  button.disabled = true;
  try {
    await linkReport(Number(button.dataset.linkReport), Number(button.dataset.issueId));
    showToast("Duplicate confirmed. The original report now appears under the shared issue.");
  } catch (error) {
    showToast(error.message, true);
    button.disabled = false;
  }
});

elements.assignmentPanel.addEventListener("submit", async (event) => {
  if (event.target.id !== "assignment-form") return;
  event.preventDefault();
  const issue = boardState.issues[0];
  const values = Object.fromEntries(new FormData(event.target));
  try {
    const result = await assignCrew(issue.id, Number(values.crew_id));
    showToast(`${result.crew} now owns this repair.`);
  } catch (error) {
    showToast(error.message, true);
  }
});

elements.assignmentPanel.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-resolve-issue]");
  if (!button) return;
  button.disabled = true;
  try {
    await resolveIssue(Number(button.dataset.resolveIssue));
    showToast("Repair resolved. The completed assignment and full history were retained.");
  } catch (error) {
    showToast(error.message, true);
    button.disabled = false;
  }
});

elements.resetButton.addEventListener("click", async () => {
  const confirmed = window.confirm("Reset all local changes and restore the fictional demo data?");
  if (!confirmed) return;
  try {
    await api("/api/reset", { method: "POST", body: "{}" });
    await refresh();
    showToast("Synthetic demo data restored.");
  } catch (error) {
    showToast(error.message, true);
  }
});

function registerWebMcpTools() {
  const context = document.modelContext;
  if (!context?.registerTool) return;
  const signal = new AbortController().signal;
  const register = (tool) => Promise.resolve(context.registerTool(tool, { signal })).catch(() => undefined);

  register({
    name: "read_waterfault_state",
    title: "Read WaterFault board",
    description: "Read the current local issues, unlinked reports, assignments, and event history without changing them.",
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
    annotations: { readOnlyHint: true, untrustedContentHint: true },
    execute: async () => refresh(),
  });
  register({
    name: "create_fault_report",
    title: "Create fault report",
    description: "Save one new local demonstration report and return possible duplicate issues for review.",
    inputSchema: {
      type: "object",
      properties: {
        reporter_label: { type: "string" },
        reported_landmark: { type: "string" },
        description: { type: "string" },
      },
      required: ["reporter_label", "reported_landmark", "description"],
      additionalProperties: false,
    },
    annotations: { readOnlyHint: false, untrustedContentHint: true },
    execute: createReport,
  });
  register({
    name: "link_report_to_issue",
    title: "Confirm duplicate report",
    description: "Confirm that one unlinked report belongs to an existing open issue while preserving the original report.",
    inputSchema: {
      type: "object",
      properties: { report_id: { type: "integer" }, issue_id: { type: "integer" } },
      required: ["report_id", "issue_id"],
      additionalProperties: false,
    },
    annotations: { readOnlyHint: false, untrustedContentHint: false },
    execute: ({ report_id, issue_id }) => linkReport(report_id, issue_id),
  });
  register({
    name: "assign_repair_crew",
    title: "Assign repair crew",
    description: "Assign one crew to an open issue. The operation fails if another crew is already active.",
    inputSchema: {
      type: "object",
      properties: { issue_id: { type: "integer" }, crew_id: { type: "integer" } },
      required: ["issue_id", "crew_id"],
      additionalProperties: false,
    },
    annotations: { readOnlyHint: false, untrustedContentHint: false },
    execute: ({ issue_id, crew_id }) => assignCrew(issue_id, crew_id),
  });
  register({
    name: "resolve_water_issue",
    title: "Resolve water issue",
    description: "Complete the active crew assignment and mark the issue resolved while retaining the event history.",
    inputSchema: {
      type: "object",
      properties: { issue_id: { type: "integer" } },
      required: ["issue_id"],
      additionalProperties: false,
    },
    annotations: { readOnlyHint: false, untrustedContentHint: false },
    execute: ({ issue_id }) => resolveIssue(issue_id),
  });
}

refresh()
  .then(registerWebMcpTools)
  .catch((error) => {
    showToast(error.message, true);
    elements.inbox.innerHTML = '<div class="empty-state">The local database is unavailable. Restart the WaterFault server and try again.</div>';
  });
