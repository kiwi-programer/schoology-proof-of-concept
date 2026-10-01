const $ = id => document.getElementById(id);
const esc = value => String(value ?? "").replace(/[&<>"]/g, character => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[character]));
let catalog = {endpoints: [], categories: []};
let myId = null;

async function request(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`);
  return data;
}

const post = (url, body = {}) => request(url, {
  method: "POST",
  headers: {"Content-Type": "application/json"},
  body: JSON.stringify(body),
});

function setBusy(button, busy, label) {
  button.disabled = busy;
  if (busy) {
    button.dataset.label = button.textContent;
    button.textContent = label;
  } else if (button.dataset.label) {
    button.textContent = button.dataset.label;
  }
}

function showError(error, target = $("meta")) {
  target.textContent = `Error: ${error.message}`;
  target.classList.add("error-message");
}

function show(response) {
  const meta = $("meta");
  meta.classList.remove("error-message");
  if (response.detail) {
    showError(new Error(response.detail));
    $("out").textContent = "";
    return;
  }

  const emptyArrays = response.is_json && response.body && typeof response.body === "object"
    ? Object.keys(response.body).filter(key => Array.isArray(response.body[key]) && response.body[key].length === 0)
    : [];
  meta.innerHTML = `<strong>Status:</strong> ${esc(response.status ?? "-")} (${esc(response.classification)}) &nbsp; ` +
    `<strong>Time:</strong> ${esc(response.elapsed_ms)} ms &nbsp; <strong>Redirects:</strong> ${esc(response.redirect_count)}` +
    `<br><strong>Final URL:</strong> ${esc(response.final_url)}` +
    (response.error ? `<br><strong>Error:</strong> ${esc(response.error)}` : "") +
    emptyArrays.map(key => `<br>${esc(key)}: 0 returned (empty is a valid result)`).join("");
  const body = response.body;
  $("out").textContent = body == null ? "(empty response)" : response.is_json ? JSON.stringify(body, null, 2) : body;
  loadHistory();
}

async function get(path) {
  try {
    show(await post("/api/request", {path}));
  } catch (error) {
    showError(error);
  }
}

$("auth").onclick = async event => {
  const button = event.currentTarget;
  setBusy(button, true, "Testing...");
  try {
    const response = await post("/api/auth-test");
    show(response);
    $("authOut").textContent = response.user
      ? `Authentication: SUCCESS\nName: ${response.user.name}\nUser ID: ${response.user.id}\nSchool ID: ${response.user.school_id}\nRole ID: ${response.user.role_id}`
      : `Authentication: FAILED\nHTTP status: ${response.status}\nError: ${response.error || response.classification}\nFinal URL: ${response.final_url}`;
  } catch (error) {
    showError(error, $("authOut"));
  } finally {
    setBusy(button, false);
  }
};

function fillEndpoints() {
  const select = $("ep");
  select.replaceChildren(...catalog.endpoints
    .filter(endpoint => endpoint.category === $("cat").value)
    .map(endpoint => new Option(`${endpoint.path} - ${endpoint.name}`, endpoint.path)));
  checkIdField();
}

function checkIdField() {
  $("idBox").hidden = !$("ep").value.includes("{id}");
}

$("cat").onchange = fillEndpoints;
$("ep").onchange = checkIdField;
$("send").onclick = async event => {
  const button = event.currentTarget;
  let path = $("ep").value;
  if (path.includes("{id}")) {
    const id = $("idIn").value.trim();
    if (!id) {
      $("idIn").focus();
      return;
    }
    path = path.replace("{id}", encodeURIComponent(id));
  }
  setBusy(button, true, "Loading...");
  try { await get(path); } finally { setBusy(button, false); }
};

$("customGo").onclick = async event => {
  const path = $("custom").value.trim();
  if (!path) {
    $("custom").focus();
    return;
  }
  setBusy(event.currentTarget, true, "Loading...");
  try { await get(path); } finally { setBusy(event.currentTarget, false); }
};

$("copy").onclick = async event => {
  try {
    await navigator.clipboard.writeText($("out").textContent);
    setBusy(event.currentTarget, true, "Copied");
    setTimeout(() => setBusy(event.currentTarget, false), 900);
  } catch (error) {
    showError(error);
  }
};

$("disc").onclick = async event => {
  setBusy(event.currentTarget, true, "Loading users...");
  try {
    const response = await post("/api/request", {path: "/v1/users"});
    const users = (response.body && response.body.user) || [];
    $("discOut").innerHTML = users.length
      ? "<table><thead><tr><th>ID</th><th>Name</th></tr></thead><tbody>" + users.map(user =>
        `<tr class="row" data-id="${esc(user.id)}" data-name="${esc(user.name_display)}"><td>${esc(user.id)}</td><td>${esc(user.name_display)}</td></tr>`).join("") + "</tbody></table>"
      : `${esc(response.status)}: 0 users returned`;
    document.querySelectorAll("#discOut tr.row").forEach(row => row.onclick = () => showRelated(row.dataset.id, row.dataset.name));
  } catch (error) {
    showError(error, $("discOut"));
  } finally {
    setBusy(event.currentTarget, false);
  }
};

function showRelated(id, name) {
  const resources = ["", "sections", "groups", "grades", "events", "updates", "documents"];
  $("related").innerHTML = `<h3>${esc(name)} (User ID: ${esc(id)})</h3>` + resources
    .map(resource => `<button type="button" class="button button-secondary" data-path="/v1/users/${encodeURIComponent(id)}${resource ? "/" + resource : ""}">${resource || "Profile"}</button>`).join(" ");
  document.querySelectorAll("#related button").forEach(button => button.onclick = () => get(button.dataset.path));
}

$("scan").onclick = async event => {
  setBusy(event.currentTarget, true, "Starting...");
  try {
    await post("/api/scan");
    await poll();
  } catch (error) {
    showError(error, $("scanOut"));
  } finally {
    setBusy(event.currentTarget, false);
  }
};

async function poll() {
  const status = await request("/api/scan/status");
  const percent = status.total ? Math.round(100 * status.completed / status.total) : 0;
  $("fill").style.width = `${percent}%`;
  $("fill").parentElement.setAttribute("aria-valuenow", percent);
  $("scanOut").textContent = `${status.running ? "Scanning..." : "Done"} ${percent}%\nCurrent: ${status.current || "-"}\nCompleted: ${status.completed}\n` +
    Object.entries(status.counts).map(([key, value]) => `${key}: ${value}`).join("\n");
  if (status.running) {
    setTimeout(() => poll().catch(error => showError(error, $("scanOut"))), 500);
  } else {
    await loadHistory();
  }
}

async function loadHistory() {
  try {
    const history = await request("/api/history");
    $("hist").innerHTML = history.slice().reverse().map(item =>
      `<div class="row" data-index="${esc(item.index)}">${esc(item.status ?? "ERR")} ${esc(item.method)} ${esc(item.endpoint)} <small>${esc(item.timestamp)} ${esc(item.response_time)}ms</small></div>`).join("");
    document.querySelectorAll("#hist .row").forEach(row => row.onclick = async () => {
      try { show(await request(`/api/history/${encodeURIComponent(row.dataset.index)}`)); }
      catch (error) { showError(error); }
    });
  } catch (error) {
    showError(error, $("hist"));
  }
}

async function loadCatalog() {
  try {
    catalog = await request("/api/endpoints");
    $("cat").replaceChildren(...catalog.categories.map(category => new Option(category, category)));
    fillEndpoints();
  } catch (error) {
    showError(error, $("meta"));
  }
}

async function ensureMe() {
  if (myId) return myId;
  const response = await post("/api/request", {path: "/v1/users/me"});
  myId = response.body && response.body.id;
  return myId;
}

$("mySec").onclick = async event => {
  setBusy(event.currentTarget, true, "Loading sections...");
  try {
    const id = await ensureMe();
    if (!id) {
      $("secOut").textContent = "Could not get your user ID. Run Test authentication first.";
      return;
    }
    const response = await post("/api/request", {path: `/v1/users/${encodeURIComponent(id)}/sections`});
    const sections = (response.body && response.body.section) || [];
    $("secOut").innerHTML = sections.length
      ? "<table><thead><tr><th>Class</th><th>Section</th><th>ID</th><th></th></tr></thead><tbody>" + sections.map(section =>
        `<tr><td>${esc(section.course_title)}</td><td>${esc(section.section_title)}</td><td>${esc(section.id)}</td><td><button type="button" class="button button-quiet" data-section="${esc(section.id)}">Assignments</button></td></tr>`).join("") + "</tbody></table>"
      : `${esc(response.status)}: 0 sections returned`;
    document.querySelectorAll("#secOut button").forEach(button => button.onclick = () => showAssignments(button.dataset.section));
  } catch (error) {
    showError(error, $("secOut"));
  } finally {
    setBusy(event.currentTarget, false);
  }
};

async function showAssignments(sectionId) {
  try {
    const response = await post("/api/request", {path: `/v1/sections/${encodeURIComponent(sectionId)}/assignments`});
    show(response);
    const assignments = (response.body && response.body.assignment) || [];
    $("asgOut").innerHTML = assignments.length
      ? "<table><thead><tr><th>Title</th><th>Due</th></tr></thead><tbody>" + assignments.map(assignment =>
        `<tr><td>${esc(assignment.title)}</td><td>${esc(assignment.due || "none")}</td></tr>`).join("") + "</tbody></table>"
      : `${esc(response.status)}: 0 assignments returned`;
  } catch (error) {
    showError(error, $("asgOut"));
  }
}

loadCatalog();
loadHistory();