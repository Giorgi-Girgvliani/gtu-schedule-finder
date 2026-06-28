const form = document.getElementById("search-form");
const queryInput = document.getElementById("query");
const suggestionsEl = document.getElementById("suggestions");
const resultsEl = document.getElementById("results");
const statusEl = document.getElementById("status");
const refreshBtn = document.getElementById("refresh-btn");

let suggestTimer = null;

function showStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.classList.remove("hidden", "error");
  if (isError) statusEl.classList.add("error");
}

function hideStatus() {
  statusEl.classList.add("hidden");
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

  const weekly = document.getElementById("weekly").checked;
  const exams = document.getElementById("exams").checked;

  showStatus("Searching and translating…");
  suggestionsEl.classList.add("hidden");

  try {
    const params = new URLSearchParams({ q, weekly, exams });
    const response = await fetch(`/api/search?${params}`);
    if (!response.ok) throw new Error("Search failed");
    const data = await response.json();
    hideStatus();
    showStatus(`Found ${data.count} result${data.count === 1 ? "" : "s"} for "${data.query}"`);
    renderResults(data);
  } catch (error) {
    showStatus(error.message || "Something went wrong.", true);
  }
}

async function loadSuggestions(value) {
  if (!value.trim()) {
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

refreshBtn.addEventListener("click", async () => {
  showStatus("Refreshing timetable data from GTU…");
  try {
    const response = await fetch("/api/refresh", { method: "POST" });
    const data = await response.json();
    showStatus(`Loaded ${data.entries} entries from ${data.teachers} teachers.`);
    if (data.errors?.length) {
      showStatus(`Loaded with warnings: ${data.errors.join(" | ")}`, true);
    }
  } catch (error) {
    showStatus("Refresh failed.", true);
  }
});

async function loadInitialStatus() {
  try {
    const response = await fetch("/api/status");
    const data = await response.json();
    showStatus(
      `Ready — ${data.teachers} lecturers, ${data.weekly_entries} weekly classes, ${data.exam_entries} exam slots indexed.`
    );
  } catch {
    showStatus("Could not reach the API. Start the server first.", true);
  }
}

loadInitialStatus();
