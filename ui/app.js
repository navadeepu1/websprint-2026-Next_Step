const API = "/api/v1";
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;",
}[char]));

let lastProfile = null;
let toastTimer;
const chatHistory = [];

function showToast(message) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 3200);
}

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    headers: { "Accept": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      message = body.message || body.detail || body.errors?.[0]?.message || message;
    } catch (_) {
      // The status text is the useful fallback for non-JSON errors.
    }
    throw new Error(message);
  }
  if (response.status === 204 || response.status === 304) return null;
  return response.headers.get("content-type")?.includes("text/") ? response.text() : response.json();
}

function setLoading(container, message = "Loading…") {
  container.innerHTML = `<div class="loading">${escapeHtml(message)}</div>`;
}

function setError(container, error) {
  container.innerHTML = `<div class="empty"><strong>Something went wrong</strong><br>${escapeHtml(error.message)}<br><button class="button ghost" data-retry>Try again</button></div>`;
  container.querySelector("[data-retry]")?.addEventListener("click", () => window.location.reload());
}

function navigate(view) {
  const target = document.getElementById(view) ? view : "dashboard";
  window.location.hash = target;
  $$(".view").forEach((section) => section.classList.toggle("active", section.id === target));
  $$(".main-nav a").forEach((link) => link.classList.toggle("active", link.dataset.view === target));
  if (target === "opportunities" && !$("#opportunity-list").dataset.loaded) loadOpportunities();
  if (target === "health-topics" && !$("#topic-list").dataset.loaded) loadTopics();
}

function profileFromForm() {
  const form = $("#profile-form");
  const data = new FormData(form);
  const needs = data.getAll("need");
  if (!needs.length) throw new Error("Choose at least one need.");
  const profile = {
    age: Number(data.get("age")),
    education_level: data.get("education_level"),
    occupation: data.get("occupation"),
    annual_income: Number(data.get("annual_income")),
    state: String(data.get("state")).trim().toUpperCase(),
    need: needs,
  };
  for (const field of ["has_land", "has_disability"]) {
    const value = data.get(field);
    if (value !== "") profile[field] = value === "true";
  }
  return profile;
}

function reasonMarkup(reason) {
  return `<div class="reason ${escapeHtml(reason.result)}"><b>${escapeHtml(reason.result)}</b>${escapeHtml(reason.message)}</div>`;
}

function eligibilityMarkup(payload) {
  const counts = payload.counts;
  const summary = `<div class="result-summary"><span class="count-chip good">✓ ${counts.ELIGIBLE} eligible</span><span class="count-chip warn">◐ ${counts.POSSIBLY_ELIGIBLE} possibly eligible</span><span class="count-chip">× ${counts.NOT_ELIGIBLE} not eligible</span></div>`;
  const cards = payload.results.length ? payload.results.map((item) => `<article class="result-card"><div class="result-top"><div><span class="card-tag">${escapeHtml(item.category.replaceAll("_", " "))}</span><h3>${escapeHtml(item.title)}</h3></div><span class="status ${escapeHtml(item.status)}">${escapeHtml(item.status.replaceAll("_", " "))}</span></div>${item.reasons.map(reasonMarkup).join("")}${item.near_miss ? `<p><strong>Near miss:</strong> ${escapeHtml(item.near_miss)}</p>` : ""}<p><strong>Documents:</strong> ${escapeHtml(item.documents.join(", ") || "Check the official portal")}</p>${item.official_url ? `<a class="text-link" href="${escapeHtml(item.official_url)}" target="_blank" rel="noreferrer">Open official source ↗</a>` : ""}</article>`).join("") : `<div class="empty">No matching opportunities were found for this profile.</div>`;
  return `${summary}${payload.explanation ? `<div class="notice">${escapeHtml(payload.explanation)}</div>` : ""}${cards}${payload.health_topics?.length ? `<div class="notice">${escapeHtml(payload.health_disclaimer)}</div>` : ""}`;
}

async function checkEligibility(event) {
  event.preventDefault();
  const error = $("#profile-error");
  error.hidden = true;
  try {
    lastProfile = profileFromForm();
    const area = $("#eligibility-results");
    area.hidden = false;
    setLoading(area, "Evaluating opportunities against your profile…");
    const payload = await request("/eligibility/check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(lastProfile),
    });
    area.innerHTML = eligibilityMarkup(payload);
    showToast("Eligibility results are ready.");
  } catch (problem) {
    error.textContent = problem.message;
    error.hidden = false;
  }
}

function opportunityMarkup(item) {
  return `<article class="opportunity-card"><span class="card-tag">${escapeHtml(item.category.replaceAll("_", " "))}</span><h3>${escapeHtml(item.title)}</h3><p>${escapeHtml(item.description)}</p><div class="card-footer"><span class="status ${item.verified ? "ELIGIBLE" : "POSSIBLY_ELIGIBLE"}">${item.verified ? "Verified" : "Verify first"}</span><button class="text-link detail-button" data-opportunity="${escapeHtml(item.id)}">View details →</button></div></article>`;
}

async function loadOpportunities() {
  const container = $("#opportunity-list");
  setLoading(container);
  const params = new URLSearchParams({ active: "true", limit: "100" });
  if ($("#opportunity-category").value) params.set("category", $("#opportunity-category").value);
  if ($("#opportunity-verified").value) params.set("verified", $("#opportunity-verified").value);
  try {
    const items = await request(`/opportunities?${params}`);
    container.dataset.loaded = "true";
    container.innerHTML = items.length ? items.map(opportunityMarkup).join("") : `<div class="empty">No opportunities match these filters.</div>`;
    container.querySelectorAll("[data-opportunity]").forEach((button) => button.addEventListener("click", () => showOpportunity(button.dataset.opportunity)));
  } catch (problem) { setError(container, problem); }
}

async function showOpportunity(id) {
  try {
    const item = await request(`/opportunities/${encodeURIComponent(id)}`);
    showModal(item.title, `<span class="card-tag">${escapeHtml(item.category.replaceAll("_", " "))}</span><p>${escapeHtml(item.description)}</p><h3>Documents</h3><ul>${item.documents.map((doc) => `<li>${escapeHtml(doc)}</li>`).join("") || "<li>Confirm on the official portal.</li>"}</ul>${item.official_url ? `<a class="button primary" href="${escapeHtml(item.official_url)}" target="_blank" rel="noreferrer">Open official source ↗</a>` : ""}`);
  } catch (problem) { showToast(problem.message); }
}

function topicMarkup(item) {
  return `<article class="topic-card"><span class="card-tag">Health awareness</span><h3>${escapeHtml(item.title)}</h3><p>${escapeHtml(item.summary)}</p><div class="card-footer"><span></span><button class="text-link detail-button" data-topic="${escapeHtml(item.id)}">Read topic →</button></div></article>`;
}

async function loadTopics(query = "") {
  const container = $("#topic-list");
  setLoading(container);
  try {
    const items = await request(query ? `/health-topics/search?q=${encodeURIComponent(query)}` : "/health-topics");
    container.dataset.loaded = "true";
    container.innerHTML = items.length ? items.map(topicMarkup).join("") : `<div class="empty">No topics matched your search.</div>`;
    container.querySelectorAll("[data-topic]").forEach((button) => button.addEventListener("click", () => showTopic(button.dataset.topic)));
    $("#health-disclaimer").hidden = !items.length;
    $("#health-disclaimer").textContent = items[0]?.disclaimer || "";
  } catch (problem) { setError(container, problem); }
}

async function showTopic(id) {
  try {
    const item = await request(`/health-topics/${encodeURIComponent(id)}`);
    showModal(item.title, `<p>${escapeHtml(item.summary)}</p><h3>Warning signs</h3><ul>${item.warning_signs.map((text) => `<li>${escapeHtml(text)}</li>`).join("") || "<li>See the source for more information.</li>"}</ul><h3>When to seek help</h3><ul>${item.when_to_seek_help.map((text) => `<li>${escapeHtml(text)}</li>`).join("")}</ul><div class="notice">${escapeHtml(item.disclaimer)}</div>`);
  } catch (problem) { showToast(problem.message); }
}

function showModal(title, body) {
  document.querySelector(".modal-backdrop")?.remove();
  const backdrop = document.createElement("div");
  backdrop.className = "modal-backdrop";
  backdrop.innerHTML = `<div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title"><button class="modal-close" aria-label="Close">×</button><h2 id="modal-title">${escapeHtml(title)}</h2><div>${body}</div></div>`;
  document.body.appendChild(backdrop);
  backdrop.addEventListener("click", (event) => { if (event.target === backdrop || event.target.closest(".modal-close")) backdrop.remove(); });
}

async function generatePlan() {
  const area = $("#plan-results");
  try {
    lastProfile ||= profileFromForm();
    area.hidden = false;
    setLoading(area, "Building your action plan…");
    const format = $("#plan-format").value;
    const result = await request(`/plan?format=${format}`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(lastProfile),
    });
    if (format === "markdown") {
      area.innerHTML = `<pre class="markdown-output">${escapeHtml(result)}</pre>`;
    } else {
      area.innerHTML = `<div class="result-card"><h2>Checklist</h2><ul class="checklist">${result.checklist.map((item) => `<li><input type="checkbox" aria-label="${escapeHtml(item.text)}"><span>${escapeHtml(item.text)}</span></li>`).join("")}</ul>${result.documents.length ? `<h3>Documents to gather</h3><p>${escapeHtml(result.documents.join(" • "))}</p>` : ""}${result.links.length ? `<h3>Official links</h3><div class="link-list">${result.links.map((link) => `<a href="${escapeHtml(link.url || "#")}" target="_blank" rel="noreferrer">${escapeHtml(link.title || link.url || "Open link")} ↗</a>`).join("")}</div>` : ""}${result.warnings.map((warning) => `<div class="notice">${escapeHtml(warning)}</div>`).join("")}</div>`;
    }

    function addChatMessage(role, text) {
      const messages = $("#chat-messages");
      const message = document.createElement("div");
      message.className = `chat-message ${role}`;
      message.textContent = text;
      messages.appendChild(message);
      messages.scrollTop = messages.scrollHeight;
    }

    async function sendChatMessage(text) {
      const message = text.trim();
      if (!message) return;
      addChatMessage("user", message);
      chatHistory.push({ role: "user", content: message });
      $("#chat-input").value = "";
      const pending = document.createElement("div");
      pending.className = "chat-message assistant pending";
      pending.textContent = "Thinking…";
      $("#chat-messages").appendChild(pending);
      try {
        const result = await request("/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message, history: chatHistory.slice(-8) }),
        });
        pending.remove();
        addChatMessage("assistant", result.reply);
        chatHistory.push({ role: "assistant", content: result.reply });
      } catch (problem) {
        pending.remove();
        addChatMessage("assistant", `I couldn't answer right now. ${problem.message}`);
      }
    }

    function initChatbot() {
      const launcher = $("#chat-launcher");
      const panel = $("#chat-panel");
      const open = () => {
        panel.hidden = false;
        launcher.setAttribute("aria-expanded", "true");
        $("#chat-input").focus();
      };
      const close = () => {
        panel.hidden = true;
        launcher.setAttribute("aria-expanded", "false");
      };
      launcher.addEventListener("click", () => (panel.hidden ? open() : close()));
      $("#chat-close").addEventListener("click", close);
      $("#chat-form").addEventListener("submit", (event) => {
        event.preventDefault();
        sendChatMessage($("#chat-input").value);
      });
      $$("#chat-suggestions button").forEach((button) => button.addEventListener("click", () => sendChatMessage(button.textContent)));
    }
    showToast("Your action plan is ready.");
  } catch (problem) {
    area.hidden = false;
    setError(area, problem);
  }
}

async function loadDashboard() {
  try {
    const [health, opportunities, topics] = await Promise.all([request("/health"), request("/opportunities?active=true&limit=100"), request("/health-topics")]);
    $("#stat-opportunities").textContent = opportunities.length;
    $("#stat-topics").textContent = topics.length;
    $("#stat-status").textContent = health.status === "ok" ? "Online" : "Degraded";
    $("#api-status").textContent = health.status === "ok"
      ? (health.ai_provider === "groq" && health.ai_configured ? "API + Groq online" : "API online")
      : "API degraded";
    $(".api-pill").classList.toggle("ok", health.status === "ok");
  } catch (_) {
    $("#api-status").textContent = "API unavailable";
  }
}

function init() {
  $$(".main-nav a").forEach((link) => link.addEventListener("click", () => navigate(link.dataset.view)));
  $$("[data-go]").forEach((button) => button.addEventListener("click", () => navigate(button.dataset.go)));
  $("#profile-form").addEventListener("submit", checkEligibility);
  $("#load-opportunities").addEventListener("click", loadOpportunities);
  $("#search-topics").addEventListener("click", () => loadTopics($("#topic-search").value.trim()));
  $("#load-topics").addEventListener("click", () => { $("#topic-search").value = ""; loadTopics(); });
  $("#generate-plan").addEventListener("click", generatePlan);
  initChatbot();
  window.addEventListener("hashchange", () => navigate(window.location.hash.slice(1)));
  navigate(window.location.hash.slice(1) || "dashboard");
  loadDashboard();
}

init();
