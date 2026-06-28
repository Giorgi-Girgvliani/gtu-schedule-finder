const form = document.getElementById("search-form");
const queryInput = document.getElementById("query");
const suggestionsEl = document.getElementById("suggestions");
const resultsEl = document.getElementById("results");
const statusEl = document.getElementById("status");
const searchBtn = document.getElementById("search-btn");

let suggestTimer = null;
let statusPollTimer = null;
let dataReady = false;

function showStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.classList.remove("hidden", "error", "updating");
  if (isError) statusEl.classList.add("error");
}

function setSearchEnabled(enabled) {
  searchBtn.disabled = !enabled;
  queryInput.disabled = !enabled;
}

function renderResults(data) {
  if (!data.results.length) {
    resultsEl.innerHTML = `
      <div class="empty-state">
        <p>No schedule entries found for <strong>${escapeHtml(data.query)}</strong>.</p>
        <p>Try the lecturer's surname in Georgian or English.</p>
      </div>`;
    return;
  }

  resultsEl.innerHTML = data.results
    .map((item) => {
      const isExam = item.schedule_type === "exam";
      const whenLabel = isExam ? "Date" : "Day";
      const whenValue = isExam ? item.day : item.day;
      return `
        <article class="card">
          <div class="card-header">
            <div>
              <p class="course-title">${escapeHtml(item.course)}</p>
              <p class="course-original">${escapeHtml(item.course_original)}</p>
            </div>
            <span class="badge ${isExam ? "exam" : "weekly"}">${isExam ? "Final exam" : "Weekly class"}</span>
          </div>
          <div class="meta-grid">
            <div class="meta-item"><span class="meta-label">Lecturer</span>${escapeHtml(item.teacher)}</div>
            <div class="meta-item"><span class="meta-label">${whenLabel}</span>${escapeHtml(whenValue || "—")}</div>
            <div class="meta-item"><span class="meta-label">Time</span>${escapeHtml(item.time || "—")}</div>
            <div class="meta-item"><span class="meta-label">Room</span>${escapeHtml(item.room || "—")}</div>
            ${item.group ? `<div class="meta-item"><span class="meta-label">Group</span>${escapeHtml(item.group)}</div>` : ""}
            ${item.faculty ? `<div class="meta-item"><span class="meta-label">Faculty</span>${escapeHtml(item.faculty)}</div>` : ""}
          </div>
        </article>`;
    })
    .join("");
}

function escapeHtml(text) {
  return String(text ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function runSearch() {
  const q = queryInput.value.trim();
  if (!q) return;

  if (!dataReady) {
    showStatus("Still loading GTU data — please wait a moment and try again.");
    pollStatus();
    return;
  }

  const weekly = document.getElementById("weekly").checked;
  const exams = document.getElementById("exams").checked;

  showStatus("Searching and translating…");
  suggestionsEl.classList.add("hidden");

  try {
    const params = new URLSearchParams({ q, weekly, exams });
    const response = await fetch(`/api/search?${params}`);
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Search failed");
    }
    showStatus(`Found ${data.count} result${data.count === 1 ? "" : "s"} for "${data.query}"`);
    renderResults(data);
  } catch (error) {
    showStatus(error.message || "Something went wrong.", true);
  }
}

async function loadSuggestions(value) {
  if (!value.trim() || !dataReady) {
    suggestionsEl.classList.add("hidden");
    return;
  }

  const response = await fetch(`/api/teachers?q=${encodeURIComponent(value.trim())}`);
  const data = await response.json();

  if (!data.teachers.length) {
    suggestionsEl.classList.add("hidden");
    return;
  }

  suggestionsEl.innerHTML = data.teachers
    .map(
      (name) =>
        `<button type="button" data-name="${escapeHtml(name)}">${escapeHtml(name)}</button>`
    )
    .join("");
  suggestionsEl.classList.remove("hidden");
}

async function pollStatus() {
  try {
    const response = await fetch("/api/status");
    if (!response.ok) throw new Error("Status request failed");
    const data = await response.json();

    if (data.loading && !data.ready) {
      dataReady = false;
      setSearchEnabled(false);
      showStatus(data.message || "Loading GTU timetable data…");
      statusPollTimer = setTimeout(pollStatus, 3000);
      return;
    }

    if (data.ready) {
      dataReady = true;
      setSearchEnabled(true);

      if (data.updating) {
        statusEl.classList.add("updating");
        const msg = data.message ||
          "Schedule files are being updated — this can take up to 5 minutes. " +
          "Search is still available using last week's data.";
        showStatus(msg);
        statusPollTimer = setTimeout(pollStatus, 3000);
        return;
      }

      let message = `Ready — ${data.teachers} lecturers, ${data.weekly_entries} weekly classes, ${data.exam_entries} exam slots.`;
      if (data.last_updated) {
        message += ` Data from ${data.last_updated}. Updates automatically every Saturday.`;
      }
      if (data.errors?.length) {
        message += ` (${data.errors.length} source warning${data.errors.length === 1 ? "" : "s"})`;
      }
      showStatus(message);
      return;
    }

    dataReady = false;
    setSearchEnabled(false);
    showStatus(data.message || "Waiting for schedule data…", true);
    statusPollTimer = setTimeout(pollStatus, 3000);
  } catch {
    dataReady = false;
    setSearchEnabled(false);
    showStatus("Could not reach the server. On Render free tier, wait ~30s for the site to wake up, then reload the page.", true);
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  runSearch();
});

queryInput.addEventListener("input", () => {
  clearTimeout(suggestTimer);
  suggestTimer = setTimeout(() => loadSuggestions(queryInput.value), 250);
});

suggestionsEl.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-name]");
  if (!button) return;
  queryInput.value = button.dataset.name;
  suggestionsEl.classList.add("hidden");
  runSearch();
});

setSearchEnabled(false);
pollStatus();
