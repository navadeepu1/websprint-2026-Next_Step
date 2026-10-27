const API = "/api/v1";
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;",
}[char]));

let lastProfile = null;
let toastTimer;
const chatHistory = [];
let authMode = "login";
let accessToken = localStorage.getItem("nextstep_access_token");
const demoProfile = {
  age: 21,
  education_level: "undergraduate",
  occupation: "student",
  annual_income: 0,
  state: "PB",
  need: ["study", "work"],
};

function showToast(message) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 3200);
}

async function request(path, options = {}) {
  const authHeaders = accessToken ? { Authorization: "Bearer " + accessToken } : {};
  const response = await fetch(`${API}${path}`, {
    headers: { "Accept": "application/json", ...authHeaders, ...(options.headers || {}) },
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

function updateAuthButton(user) {
  const button = $("#auth-button");
  button.textContent = user ? `Sign out (${user.display_name})` : "Sign in";
}

function openAuth(mode = "login") {
  authMode = mode;
  $("#auth-dialog").hidden = false;
  $("#auth-title").textContent = mode === "login" ? "Welcome back" : "Create your account";
  $("#auth-subtitle").textContent = mode === "login"
    ? "Sign in to your NextStep session."
    : "Create a local account for testing.";
  $("#auth-name-label").hidden = mode === "login";
  $("#auth-submit").textContent = mode === "login" ? "Sign in" : "Create account";
  $("#auth-switch").textContent = mode === "login" ? "Create a new account" : "I already have an account";
  $("#auth-password").minLength = mode === "login" ? 1 : 8;
  $("#auth-error").hidden = true;
  $("#auth-email").focus();
}

function closeAuth() {
  $("#auth-dialog").hidden = true;
}

async function submitAuth(event) {
  event.preventDefault();
  const error = $("#auth-error");
  error.hidden = true;
  const payload = { email: $("#auth-email").value, password: $("#auth-password").value };
  if (authMode === "register") payload.display_name = $("#auth-name").value;
  try {
    const result = await request(`/auth/${authMode}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    accessToken = result.access_token;
    localStorage.setItem("nextstep_access_token", accessToken);
    updateAuthButton(result.user);
    await loadSavedProfileIntoForm();
    closeAuth();
    showToast(`Signed in as ${result.user.display_name}.`);
  } catch (problem) {
    error.textContent = problem.message;
    error.hidden = false;
  }
}

async function loadSavedProfileIntoForm() {
  if (!accessToken) return;
  try {
    const profile = await request("/profile");
    const form = $("#profile-form");
    for (const [field, value] of Object.entries(profile)) {
      const input = form.elements.namedItem(field);
      if (!input || value === null || value === undefined) continue;
      if (field === "need") {
        form.querySelectorAll('input[name="need"]').forEach((checkbox) => { checkbox.checked = value.includes(checkbox.value); });
      } else if (input.type === "checkbox") {
        input.checked = value;
      } else if (input.type !== "submit") {
        input.value = value;
      }
    }
  } catch (problem) {
    if (!problem.message.includes("No saved profile")) showToast(problem.message);
  }
}

async function initializeAuth() {
  if (!accessToken) return;
  try {
    updateAuthButton(await request("/auth/me"));
    await loadSavedProfileIntoForm();
  } catch (_) {
    accessToken = null;
    localStorage.removeItem("nextstep_access_token");
  }
}

function setLoading(container, message = "Loadingâ€¦") {
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
  if (target === "workspace") loadWorkspace();
  if (target === "discover") loadDiscover();
  if (target === "plan" && !$("#plan-results").innerHTML) renderDemoPlan();
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
  const summary = `<div class="result-summary"><span class="count-chip good">âœ“ ${counts.ELIGIBLE} eligible</span><span class="count-chip warn">â— ${counts.POSSIBLY_ELIGIBLE} possibly eligible</span><span class="count-chip">Ã— ${counts.NOT_ELIGIBLE} not eligible</span></div>`;
  const cards = payload.results.length ? payload.results.map((item) => `<article class="result-card"><div class="result-top"><div><span class="card-tag">${escapeHtml(item.category.replaceAll("_", " "))}</span><h3>${escapeHtml(item.title)}</h3></div><span class="status ${escapeHtml(item.status)}">${escapeHtml(item.status.replaceAll("_", " "))}</span></div>${item.reasons.map(reasonMarkup).join("")}${item.near_miss ? `<p><strong>Near miss:</strong> ${escapeHtml(item.near_miss)}</p>` : ""}<p><strong>Documents:</strong> ${escapeHtml(item.documents.join(", ") || "Check the official portal")}</p>${item.official_url ? `<a class="text-link" href="${escapeHtml(item.official_url)}" target="_blank" rel="noreferrer">Open official source â†—</a>` : ""}</article>`).join("") : `<div class="empty">No matching opportunities were found for this profile.</div>`;
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
    setLoading(area, "Evaluating opportunities against your profileâ€¦");
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
  return `<article class="opportunity-card"><span class="card-tag">${escapeHtml(item.category.replaceAll("_", " "))}</span><h3>${escapeHtml(item.title)}</h3><p>${escapeHtml(item.description)}</p><div class="card-footer"><span class="status ${item.verified ? "ELIGIBLE" : "POSSIBLY_ELIGIBLE"}">${item.verified ? "Verified" : "Verify first"}</span><button class="text-link detail-button" data-opportunity="${escapeHtml(item.id)}">View details â†’</button></div><div class="card-actions"><button class="button ghost small" data-save-opportunity="${escapeHtml(item.id)}">Save</button><button class="button secondary small" data-track-opportunity="${escapeHtml(item.id)}">Track</button></div></article>`;
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
    container.querySelectorAll("[data-save-opportunity]").forEach((button) => button.addEventListener("click", () => saveOpportunity(button.dataset.saveOpportunity)));
    container.querySelectorAll("[data-track-opportunity]").forEach((button) => button.addEventListener("click", () => trackOpportunity(button.dataset.trackOpportunity)));
  } catch (problem) { setError(container, problem); }
}

async function saveProfile() {
  try {
    const profile = profileFromForm();
    await request("/profile", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(profile) });
    showToast("Profile saved to your workspace.");
  } catch (problem) {
    showToast(accessToken ? problem.message : "Sign in before saving your profile.");
  }
}

async function saveOpportunity(id) {
  try {
    await request(`/saved-opportunities/${encodeURIComponent(id)}`, { method: "POST" });
    showToast("Opportunity saved.");
  } catch (problem) { showToast(problem.message); }
}

async function trackOpportunity(id) {
  try {
    await request("/applications", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ opportunity_id: id }) });
    showToast("Opportunity added to your tracker.");
  } catch (problem) { showToast(problem.message); }
}

function workspaceProfileMarkup(profile) {
  return `<div class="profile-summary"><strong>${escapeHtml(profile.occupation.replaceAll("_", " "))}</strong><span>${escapeHtml(profile.state)} · age ${profile.age}</span><span>${escapeHtml(profile.need.join(", "))}</span></div>`;
}

function applicationMarkup(item) {
  return `<article class="tracker-row"><div><strong>${escapeHtml(item.opportunity.title)}</strong><small>${escapeHtml(item.next_step || "Add a next step")}</small></div><select data-application-status="${item.id}">${["interested", "preparing", "submitted", "in_review", "completed", "closed"].map((status) => `<option value="${status}" ${status === item.status ? "selected" : ""}>${status.replaceAll("_", " ")}</option>`).join("")}</select></article>`;
}

async function loadWorkspace() {
  const loginNotice = $("#workspace-login");
  if (!accessToken) {
    loginNotice.hidden = false;
    renderDemoWorkspace();
    return;
  }
  loginNotice.hidden = true;
  try {
    const [profile, saved, applications] = await Promise.all([
      request("/profile").catch(() => null),
      request("/saved-opportunities"),
      request("/applications"),
    ]);
    $("#saved-profile").innerHTML = profile ? workspaceProfileMarkup(profile) : `<div class="empty">Save your profile from the eligibility page.</div>`;
    $("#saved-opportunities").innerHTML = saved.length ? saved.map((item) => `<div class="workspace-item"><strong>${escapeHtml(item.opportunity.title)}</strong><button class="text-link" data-track-opportunity="${escapeHtml(item.opportunity.id)}">Track</button></div>`).join("") : `<div class="empty">Nothing saved yet.</div>`;
    $("#application-list").innerHTML = applications.length ? applications.map(applicationMarkup).join("") : `<div class="empty">No applications tracked yet.</div>`;
    $("#saved-opportunities").querySelectorAll("[data-track-opportunity]").forEach((button) => button.addEventListener("click", () => trackOpportunity(button.dataset.trackOpportunity)));
    $("#application-list").querySelectorAll("[data-application-status]").forEach((select) => select.addEventListener("change", async () => {
      await request(`/applications/${select.dataset.applicationStatus}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status: select.value }) });
      showToast("Application status updated.");
    }));
  } catch (problem) {
    setError($("#application-list"), problem);
  }
}

function demoOpportunity(title, category, status, description) {
  return { id: `demo-${category}-${title.toLowerCase().replaceAll(" ", "-")}`, title, category, status, description };
}

function renderDemoWorkspace() {
  $("#saved-profile").innerHTML = `<div class="demo-label">Preview data</div>${workspaceProfileMarkup(demoProfile)}<p class="demo-copy">Sign in to save this profile and keep it across devices.</p>`;
  $("#saved-opportunities").innerHTML = [
    demoOpportunity("National Apprenticeship Training Scheme", "internship", "ELIGIBLE", "Student placement and workplace learning"),
    demoOpportunity("Post-Matric Scholarship", "scholarship", "POSSIBLY_ELIGIBLE", "Confirm current income and document rules"),
  ].map((item) => `<div class="workspace-item"><div><strong>${escapeHtml(item.title)}</strong><small>${escapeHtml(item.description)}</small></div><span class="status ${item.status}">${item.status.replaceAll("_", " ")}</span></div>`).join("");
  $("#application-list").innerHTML = [
    ["National Career Service registration", "preparing", "Create your job seeker profile"],
    ["Student Internship Discovery", "interested", "Review the employer and stipend"],
  ].map(([title, status, next]) => `<article class="tracker-row"><div><strong>${title}</strong><small>${next}</small></div><span class="status ${status === "preparing" ? "POSSIBLY_ELIGIBLE" : "ELIGIBLE"}">${status.replaceAll("_", " ")}</span></article>`).join("");
}

async function loadDiscover() {
  const login = $("#discover-login");
  const sections = $("#discover-sections");
  if (!accessToken) {
    login.hidden = false;
    await renderDemoDiscover();
    return;
  }
  login.hidden = true;
  setLoading(sections, "Finding opportunities that fit your profile…");
  try {
    const result = await request("/discover");
    $("#discover-summary").hidden = false;
    $("#discover-summary").innerHTML = `<span class="count-chip good">${result.total_matches} possible matches</span><span>Based on your saved profile · ${escapeHtml(result.profile.state)}</span>`;
    sections.innerHTML = result.sections.length ? result.sections.map((section) => `<section class="discover-section"><div class="section-heading"><div><p class="eyebrow">${section.count} matches</p><h2>${escapeHtml(section.title)}</h2></div></div><div class="card-grid">${section.opportunities.map((item) => `<article class="result-card"><div class="result-top"><div><span class="card-tag">${escapeHtml(item.status.replaceAll("_", " "))}</span><h3>${escapeHtml(item.title)}</h3></div><span class="status ${escapeHtml(item.status)}">${escapeHtml(item.status.replaceAll("_", " "))}</span></div><p>${escapeHtml(item.reasons[0]?.message || "Review the opportunity details and official source.")}</p><div class="card-actions"><button class="button ghost small" data-save-opportunity="${escapeHtml(item.id)}">Save</button><button class="button secondary small" data-track-opportunity="${escapeHtml(item.id)}">Track</button>${item.official_url ? `<a class="button primary small" href="${escapeHtml(item.official_url)}" target="_blank" rel="noreferrer">Official source</a>` : ""}</div></article>`).join("")}</div></section>`).join("") : `<div class="empty">No possible matches yet. Update your profile with more details to broaden discovery.</div>`;
    sections.querySelectorAll("[data-save-opportunity]").forEach((button) => button.addEventListener("click", () => saveOpportunity(button.dataset.saveOpportunity)));
    sections.querySelectorAll("[data-track-opportunity]").forEach((button) => button.addEventListener("click", () => trackOpportunity(button.dataset.trackOpportunity)));
  } catch (problem) {
    setError(sections, problem);
  }
}

async function renderDemoDiscover() {
  const sections = $("#discover-sections");
  setLoading(sections, "Loading the sample opportunity hub…");
  try {
    const items = await request("/opportunities?active=true&limit=100");
    const grouped = items.reduce((all, item) => {
      (all[item.category] ||= []).push(item);
      return all;
    }, {});
    const titles = { scholarship: "Scholarships", internship: "Internships", job: "Jobs and placements", training: "Training and skill building", farmer_scheme: "Farmer schemes", senior_support: "Senior support" };
    sections.innerHTML = Object.entries(grouped).map(([category, records]) => `<section class="discover-section"><div class="section-heading"><div><p class="eyebrow">${records.length} sample matches</p><h2>${titles[category] || category}</h2></div></div><div class="card-grid">${records.slice(0, 3).map((item) => `<article class="result-card"><div class="result-top"><div><span class="card-tag">Preview match</span><h3>${escapeHtml(item.title)}</h3></div><span class="status POSSIBLY_ELIGIBLE">Review fit</span></div><p>${escapeHtml(item.description)}</p><div class="card-actions">${item.official_url ? `<a class="button primary small" href="${escapeHtml(item.official_url)}" target="_blank" rel="noreferrer">Official source</a>` : ""}<button class="button ghost small" data-demo-signin>Save after sign in</button></div></article>`).join("")}</div></section>`).join("");
    $("#discover-summary").hidden = false;
    $("#discover-summary").innerHTML = `<span class="count-chip good">${items.length} catalogue opportunities</span><span>Preview mode · sign in for profile-specific matches</span>`;
    sections.querySelectorAll("[data-demo-signin]").forEach((button) => button.addEventListener("click", () => openAuth()));
  } catch (problem) {
    setError(sections, problem);
  }
}

function renderDemoPlan() {
  const area = $("#plan-results");
  area.hidden = false;
  area.innerHTML = `<div class="demo-label">Sample action plan</div><div class="result-card"><h2>Student opportunity starter plan</h2><ul class="checklist"><li><input type="checkbox" aria-label="Create a student profile"><span>Create a student profile on the official opportunity portal</span></li><li><input type="checkbox" aria-label="Prepare resume"><span>Prepare a one-page resume and education certificate</span></li><li><input type="checkbox" aria-label="Check deadlines"><span>Check the application deadline and eligibility rules</span></li><li><input type="checkbox" aria-label="Track application"><span>Save the opportunity and track your next step</span></li></ul><h3>Documents to gather</h3><p>Education certificate · Identity document · Bank account details · Resume</p><div class="notice">This is preview data. Generate a personal plan after completing your profile.</div></div>`;
}

async function showOpportunity(id) {
  try {
    const item = await request(`/opportunities/${encodeURIComponent(id)}`);
    showModal(item.title, `<span class="card-tag">${escapeHtml(item.category.replaceAll("_", " "))}</span><p>${escapeHtml(item.description)}</p><h3>Documents</h3><ul>${item.documents.map((doc) => `<li>${escapeHtml(doc)}</li>`).join("") || "<li>Confirm on the official portal.</li>"}</ul>${item.official_url ? `<a class="button primary" href="${escapeHtml(item.official_url)}" target="_blank" rel="noreferrer">Open official source â†—</a>` : ""}`);
  } catch (problem) { showToast(problem.message); }
}

function topicMarkup(item) {
  return `<article class="topic-card"><span class="card-tag">Health awareness</span><h3>${escapeHtml(item.title)}</h3><p>${escapeHtml(item.summary)}</p><div class="card-footer"><span></span><button class="text-link detail-button" data-topic="${escapeHtml(item.id)}">Read topic â†’</button></div></article>`;
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
  backdrop.innerHTML = `<div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title"><button class="modal-close" aria-label="Close">Ã—</button><h2 id="modal-title">${escapeHtml(title)}</h2><div>${body}</div></div>`;
  document.body.appendChild(backdrop);
  backdrop.addEventListener("click", (event) => { if (event.target === backdrop || event.target.closest(".modal-close")) backdrop.remove(); });
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
  pending.textContent = "Thinkingâ€¦";
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
  let returnFocus = launcher;
  const open = () => {
    returnFocus = document.activeElement instanceof HTMLElement ? document.activeElement : launcher;
    panel.hidden = false;
    launcher.setAttribute("aria-expanded", "true");
    refreshChatStatus();
    $("#chat-input").focus();
  };
  const close = () => {
    panel.hidden = true;
    launcher.setAttribute("aria-expanded", "false");
    returnFocus.focus();
  };
  launcher.addEventListener("click", () => (panel.hidden ? open() : close()));
  $("#chat-close").addEventListener("click", close);
  panel.addEventListener("keydown", (event) => {
    if (event.key === "Escape") close();
  });
  $("#chat-form").addEventListener("submit", (event) => {
    event.preventDefault();
    sendChatMessage($("#chat-input").value);
  });
  $$("#chat-suggestions button").forEach((button) => button.addEventListener("click", () => sendChatMessage(button.textContent)));
}

async function refreshChatStatus() {
  const header = document.querySelector("#chat-title")?.parentElement?.querySelector("small");
  if (!header) return;
  try {
    const health = await request("/health");
    header.textContent = health.ai_configured && health.ai_provider === "groq"
      ? "AI online — ask anything"
      : "Offline help mode — configure Groq for general questions";
  } catch (_) {
    header.textContent = "Ask anything — website help or general questions";
  }
}

async function generatePlan() {
  const area = $("#plan-results");
  try {
    lastProfile ||= profileFromForm();
    area.hidden = false;
    setLoading(area, "Building your action planâ€¦");
    const format = $("#plan-format").value;
    const result = await request(`/plan?format=${format}`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(lastProfile),
    });
    if (format === "markdown") {
      area.innerHTML = `<pre class="markdown-output">${escapeHtml(result)}</pre>`;
    } else {
      area.innerHTML = `<div class="result-card"><h2>Checklist</h2><ul class="checklist">${result.checklist.map((item) => `<li><input type="checkbox" aria-label="${escapeHtml(item.text)}"><span>${escapeHtml(item.text)}</span></li>`).join("")}</ul>${result.documents.length ? `<h3>Documents to gather</h3><p>${escapeHtml(result.documents.join(" â€¢ "))}</p>` : ""}${result.links.length ? `<h3>Official links</h3><div class="link-list">${result.links.map((link) => `<a href="${escapeHtml(link.url || "#")}" target="_blank" rel="noreferrer">${escapeHtml(link.title || link.url || "Open link")} â†—</a>`).join("")}</div>` : ""}${result.warnings.map((warning) => `<div class="notice">${escapeHtml(warning)}</div>`).join("")}</div>`;
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
  $("#auth-button").addEventListener("click", async () => {
    if (!accessToken) return openAuth();
    await request("/auth/logout", { method: "POST" });
    accessToken = null;
    localStorage.removeItem("nextstep_access_token");
    updateAuthButton(null);
    showToast("You have been signed out.");
  });
  $("#auth-close").addEventListener("click", closeAuth);
  $("#auth-switch").addEventListener("click", () => openAuth(authMode === "login" ? "register" : "login"));
  $("#auth-form").addEventListener("submit", submitAuth);
  initializeAuth();
  $$(".main-nav a").forEach((link) => link.addEventListener("click", () => navigate(link.dataset.view)));
  $$("[data-go]").forEach((button) => button.addEventListener("click", () => navigate(button.dataset.go)));
  $("#profile-form").addEventListener("submit", checkEligibility);
  $("#save-profile").addEventListener("click", saveProfile);
  $("#load-opportunities").addEventListener("click", loadOpportunities);
  $("#topic-search-form").addEventListener("submit", (event) => {
    event.preventDefault();
    loadTopics($("#topic-search").value.trim());
  });
  $("#load-topics").addEventListener("click", () => { $("#topic-search").value = ""; loadTopics(); });
  $("#generate-plan").addEventListener("click", generatePlan);
  initChatbot();
  window.addEventListener("hashchange", () => navigate(window.location.hash.slice(1)));
  navigate(window.location.hash.slice(1) || "dashboard");
  loadDashboard();
}

init();
