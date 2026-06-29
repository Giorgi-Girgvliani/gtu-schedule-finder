const form = document.getElementById("search-form");
const queryInput = document.getElementById("query");
const suggestionsEl = document.getElementById("suggestions");
const resultsEl = document.getElementById("results");
const statusEl = document.getElementById("status");
const searchBtn = document.getElementById("search-btn");

let suggestTimer = null;
let statusPollTimer = null;
let dataReady = false;
let lastSearchData = null;
let lastStatusData = null;

function showStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.classList.remove("hidden", "error", "updating");
  if (isError) statusEl.classList.add("error");
}

function setSearchEnabled(enabled) {
  searchBtn.disabled = !enabled;
  queryInput.disabled = !enabled;
}

function courseDisplay(item) {
  const original = item.course_original || "";
  const translated = item.course || original;
  const hasCyrillic = /[\u0400-\u04FF]/.test(original);
  const hasGeorgian = /[\u10A0-\u10FF]/.test(original);

  if (getLang() === "ka" && hasGeorgian) {
    return { title: original, subtitle: translated !== original ? translated : "" };
  }
  if (getLang() === "ru" && hasCyrillic) {
    return { title: original, subtitle: translated !== original ? translated : "" };
  }
  return { title: translated, subtitle: original !== translated ? original : "" };
}

function renderResults(data) {
  if (!data.results.length) {
    resultsEl.innerHTML = `
      <div class="empty-state">
        <p>${t("emptyTitle", { query: escapeHtml(data.query) })}</p>
        <p>${t("emptyHint")}</p>
      </div>`;
    return;
  }

  resultsEl.innerHTML = data.results
    .map((item) => {
      const isExam = item.schedule_type === "exam";
      const whenLabel = isExam ? t("labelDate") : t("labelDay");
      const whenValue = isExam ? (item.day || t("dash")) : translateDay(item.day);
      const badge = isExam ? t("badgeExam") : t("badgeWeekly");
      const { title, subtitle } = courseDisplay(item);
      return `
        <article class="card ${isExam ? "card-exam" : "card-weekly"}">
          <div class="card-header">
            <div>
              <p class="course-title">${escapeHtml(title)}</p>
              ${subtitle ? `<p class="course-original">${escapeHtml(subtitle)}</p>` : ""}
            </div>
            <span class="badge ${isExam ? "exam" : "weekly"}">${badge}</span>
          </div>
          <div class="meta-grid">
            <div class="meta-item"><span class="meta-label">${t("labelLecturer")}</span>${escapeHtml(item.teacher)}</div>
            <div class="meta-item"><span class="meta-label">${whenLabel}</span>${escapeHtml(whenValue)}</div>
            <div class="meta-item"><span class="meta-label">${t("labelTime")}</span>${escapeHtml(item.time || t("dash"))}</div>
            <div class="meta-item"><span class="meta-label">${t("labelRoom")}</span>${escapeHtml(item.room || t("dash"))}</div>
            ${item.group ? `<div class="meta-item"><span class="meta-label">${t("labelGroup")}</span>${escapeHtml(item.group)}</div>` : ""}
            ${item.faculty ? `<div class="meta-item"><span class="meta-label">${t("labelFaculty")}</span>${escapeHtml(item.faculty)}</div>` : ""}
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

function formatSearchStatus(data) {
  const key = data.count === 1 ? "statusFound" : "statusFoundPlural";
  return t(key, { count: data.count, query: data.query });
}

function formatReadyStatus(data) {
  let message = t("statusReady", {
    teachers: data.teachers,
    weekly: data.weekly_entries,
    exam: data.exam_entries,
  });
  if (data.last_updated) {
    message += t("statusReadyUpdated", { date: data.last_updated });
  }
  if (data.errors?.length) {
    const wKey = data.errors.length === 1 ? "statusWarnings" : "statusWarningsPlural";
    message += t(wKey, { count: data.errors.length });
  }
  return message;
}

async function runSearch() {
  const q = queryInput.value.trim();
  if (!q) return;

  if (!dataReady) {
    showStatus(t("statusStillLoading"));
    pollStatus();
    return;
  }

  const weekly = document.getElementById("weekly").checked;
  const exams = document.getElementById("exams").checked;

  showStatus(t("statusSearching"));
  suggestionsEl.classList.add("hidden");

  try {
    const params = new URLSearchParams({ q, weekly, exams });
    const response = await fetch(`/api/search?${params}`);
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || t("statusSearchFailed"));
    }
    lastSearchData = data;
    showStatus(formatSearchStatus(data));
    renderResults(data);
  } catch (error) {
    showStatus(error.message || t("statusSomethingWrong"), true);
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

function applyStatusFromData(data) {
  lastStatusData = data;

  if (data.loading && !data.ready) {
    dataReady = false;
    setSearchEnabled(false);
    showStatus(data.message || t("statusLoading"));
    return "poll";
  }

  if (data.ready) {
    dataReady = true;
    setSearchEnabled(true);

    if (data.updating) {
      statusEl.classList.add("updating");
      showStatus(data.message || t("statusUpdating"));
      return "poll";
    }

    showStatus(formatReadyStatus(data));
    return "done";
  }

  dataReady = false;
  setSearchEnabled(false);
  showStatus(data.message || t("statusWaiting"), true);
  return "poll";
}

async function pollStatus() {
  try {
    const response = await fetch("/api/status");
    if (!response.ok) throw new Error("Status request failed");
    const data = await response.json();
    const next = applyStatusFromData(data);
    if (next === "poll") {
      statusPollTimer = setTimeout(pollStatus, 3000);
    }
  } catch {
    dataReady = false;
    setSearchEnabled(false);
    showStatus(t("statusServerError"), true);
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

document.querySelectorAll("[data-lang]").forEach((btn) => {
  btn.addEventListener("click", () => setLang(btn.dataset.lang));
});

window.addEventListener("languagechange", () => {
  if (lastSearchData) {
    renderResults(lastSearchData);
    showStatus(formatSearchStatus(lastSearchData));
  } else if (lastStatusData) {
    applyStatusFromData(lastStatusData);
  }
});

setSearchEnabled(false);
pollStatus();
