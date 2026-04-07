/**
 * SuspensionSim — Matrix-Based Force Distribution
 * Frontend: Auth + Theme Toggle + Simulation + AI Chat + PDF
 */

const API = window.location.hostname === "localhost" || window.location.protocol === "file:"
  ? "http://localhost:5000/api"
  : "https://python-deploy-5twl.onrender.com/api";
let linkCount = 2;
let lastResult = null;
let forceChart = null;
let authToken = localStorage.getItem("ss_token") || null;
let currentUser = localStorage.getItem("ss_user") || null;

// ===== BOOT =====
document.addEventListener("DOMContentLoaded", () => {
  applyTheme(localStorage.getItem("ss_theme") || "dark");
  if (authToken && currentUser) {
    enterApp();
  }
  // Allow Enter key on auth forms
  document.getElementById("login-password").addEventListener("keydown", e => {
    if (e.key === "Enter") doLogin(e);
  });
});

// ===== THEME TOGGLE =====
function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme");
  const next = current === "dark" ? "light" : "dark";
  applyTheme(next);
  localStorage.setItem("ss_theme", next);
}

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  document.getElementById("theme-btn").textContent = theme === "dark" ? "☀️" : "🌙";
}

// ===== AUTH TAB SWITCH =====
function switchAuthTab(tab) {
  document.getElementById("login-form").classList.toggle("hidden", tab !== "login");
  document.getElementById("signup-form").classList.toggle("hidden", tab !== "signup");
  document.getElementById("tab-login-btn").classList.toggle("active", tab === "login");
  document.getElementById("tab-signup-btn").classList.toggle("active", tab === "signup");
  document.getElementById("login-error").classList.add("hidden");
  document.getElementById("signup-error").classList.add("hidden");
}

// ===== LOGIN =====
async function doLogin(e) {
  e.preventDefault();
  const btn = document.getElementById("login-btn");
  const errEl = document.getElementById("login-error");
  errEl.classList.add("hidden");
  btn.disabled = true;
  btn.textContent = "Signing in...";

  const username = document.getElementById("login-username").value.trim();
  const password = document.getElementById("login-password").value.trim();

  try {
    const res = await fetch(`${API}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Login failed");
    saveAuth(data.token, data.username);
    enterApp();
  } catch (err) {
    errEl.textContent = err.message;
    errEl.classList.remove("hidden");
  } finally {
    btn.disabled = false;
    btn.textContent = "Sign In";
  }
}

// ===== SIGNUP =====
async function doSignup(e) {
  e.preventDefault();
  const btn = document.getElementById("signup-btn");
  const errEl = document.getElementById("signup-error");
  errEl.classList.add("hidden");
  btn.disabled = true;
  btn.textContent = "Creating account...";

  const username = document.getElementById("signup-username").value.trim();
  const email = document.getElementById("signup-email").value.trim();
  const password = document.getElementById("signup-password").value.trim();

  try {
    const res = await fetch(`${API}/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Registration failed");
    saveAuth(data.token, data.username);
    enterApp();
  } catch (err) {
    errEl.textContent = err.message;
    errEl.classList.remove("hidden");
  } finally {
    btn.disabled = false;
    btn.textContent = "Create Account";
  }
}

function saveAuth(token, username) {
  authToken = token;
  currentUser = username;
  localStorage.setItem("ss_token", token);
  localStorage.setItem("ss_user", username);
}

function enterApp() {
  document.getElementById("auth-overlay").classList.add("hidden");
  document.getElementById("app").classList.remove("hidden");
  document.getElementById("chatbot-bubble").classList.remove("hidden");
  document.getElementById("user-name-display").textContent = currentUser;
  document.getElementById("user-avatar").textContent = currentUser[0].toUpperCase();
  document.getElementById("history-subtitle").textContent =
    `${currentUser}'s simulations stored in MongoDB`;
  renderLinks();
  drawSuspensionDiagram();
  loadHistory();
}

function logout() {
  authToken = null;
  currentUser = null;
  localStorage.removeItem("ss_token");
  localStorage.removeItem("ss_user");
  document.getElementById("auth-overlay").classList.remove("hidden");
  document.getElementById("app").classList.add("hidden");
  document.getElementById("chatbot-bubble").classList.add("hidden");
  document.getElementById("chatbot-panel").classList.add("hidden");
  // Reset forms
  document.getElementById("login-username").value = "";
  document.getElementById("login-password").value = "";
  switchAuthTab("login");
}

// ===== TAB NAVIGATION =====
function showTab(name) {
  document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
  document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
  document.getElementById(`tab-${name}`).classList.add("active");
  document.querySelectorAll(".nav-btn").forEach(b => {
    if (b.textContent.toLowerCase().includes(name)) b.classList.add("active");
  });
  if (name === "history") loadHistory();
}

// ===== LINK MANAGEMENT =====
function changeLinks(delta) {
  linkCount = Math.max(1, Math.min(8, linkCount + delta));
  document.getElementById("link-count").textContent = linkCount;
  renderLinks();
  drawSuspensionDiagram();
}

function renderLinks() {
  const container = document.getElementById("links-container");
  const currentCount = container.querySelectorAll(".link-item").length;
  for (let i = currentCount; i < linkCount; i++) {
    const div = document.createElement("div");
    div.className = "link-item";
    div.innerHTML = `
      <span class="link-badge">L${i + 1}</span>
      <div class="link-field">
        <label>Angle θ (°)</label>
        <input type="number" class="link-angle" value="${30 + i * 30}" min="-180" max="180" oninput="drawSuspensionDiagram()" />
      </div>
      <div class="link-field">
        <label>Length (mm)</label>
        <input type="number" class="link-length" value="${200 + i * 20}" min="1" max="1000" />
      </div>`;
    container.appendChild(div);
  }
  const items = container.querySelectorAll(".link-item");
  for (let i = linkCount; i < items.length; i++) items[i].remove();
}

function getLinks() {
  return Array.from(document.querySelectorAll(".link-item")).map(item => ({
    angle: parseFloat(item.querySelector(".link-angle").value) || 0,
    length: parseFloat(item.querySelector(".link-length").value) || 100,
  }));
}

// ===== PRESETS =====
const PRESETS = {
  double_wishbone: [{ angle: 30, length: 250 }, { angle: 150, length: 250 }],
  macpherson: [{ angle: 45, length: 300 }, { angle: 90, length: 200 }, { angle: 135, length: 280 }],
  multilink: [
    { angle: 20, length: 220 }, { angle: 60, length: 200 },
    { angle: 100, length: 240 }, { angle: 140, length: 210 }, { angle: 160, length: 230 }
  ],
};

function loadPreset(name) {
  const preset = PRESETS[name];
  if (!preset) return;
  linkCount = preset.length;
  document.getElementById("link-count").textContent = linkCount;
  const container = document.getElementById("links-container");
  container.innerHTML = "";
  preset.forEach((lnk, i) => {
    const div = document.createElement("div");
    div.className = "link-item";
    div.innerHTML = `
      <span class="link-badge">L${i + 1}</span>
      <div class="link-field">
        <label>Angle θ (°)</label>
        <input type="number" class="link-angle" value="${lnk.angle}" min="-180" max="180" oninput="drawSuspensionDiagram()" />
      </div>
      <div class="link-field">
        <label>Length (mm)</label>
        <input type="number" class="link-length" value="${lnk.length}" min="1" max="1000" />
      </div>`;
    container.appendChild(div);
  });
  drawSuspensionDiagram();
}

function selectForceType(radio) {
  document.querySelectorAll(".force-card").forEach(c => c.classList.remove("active"));
  radio.closest(".force-card").classList.add("active");
}

// ===== 2D DIAGRAM =====
function drawSuspensionDiagram(highlightIndex = -1) {
  const canvas = document.getElementById("suspension-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const W = canvas.offsetWidth || 800;
  const H = 280;
  canvas.width = W; canvas.height = H;
  ctx.clearRect(0, 0, W, H);

  const isDark = document.documentElement.getAttribute("data-theme") !== "light";
  const gridColor = isDark ? "rgba(31,41,55,0.6)" : "rgba(203,213,225,0.5)";

  ctx.strokeStyle = gridColor; ctx.lineWidth = 1;
  for (let x = 0; x < W; x += 40) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
  for (let y = 0; y < H; y += 40) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }

  const links = getLinks();
  if (!links.length) return;
  const cx = W / 2, cy = H / 2;
  const maxLen = Math.max(...links.map(l => l.length));
  const scale = (Math.min(W, H) * 0.38) / maxLen;

  // Hub
  ctx.beginPath(); ctx.arc(cx, cy, 9, 0, Math.PI * 2);
  ctx.fillStyle = "#f59e0b"; ctx.fill();
  ctx.strokeStyle = "#fbbf24"; ctx.lineWidth = 2; ctx.stroke();

  links.forEach((lnk, i) => {
    const rad = (lnk.angle * Math.PI) / 180;
    const len = lnk.length * scale;
    const ex = cx + len * Math.cos(rad);
    const ey = cy - len * Math.sin(rad);
    const isHigh = i === highlightIndex;
    const color = isHigh ? "#ef4444" : `hsl(${210 + i * 35}, 75%, 60%)`;

    ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(ex, ey);
    ctx.strokeStyle = color; ctx.lineWidth = isHigh ? 3 : 2;
    ctx.setLineDash(isHigh ? [6, 3] : []);
    ctx.stroke(); ctx.setLineDash([]);

    ctx.beginPath(); ctx.arc(ex, ey, 5, 0, Math.PI * 2);
    ctx.fillStyle = color; ctx.fill();

    ctx.fillStyle = color;
    ctx.font = "bold 11px 'JetBrains Mono', monospace";
    ctx.fillText(`L${i + 1} (${lnk.angle}°)`, ex + 8, ey + 4);
  });

  const axisColor = isDark ? "rgba(148,163,184,0.35)" : "rgba(100,116,139,0.4)";
  ctx.strokeStyle = axisColor; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(cx - 60, cy); ctx.lineTo(cx + 60, cy); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(cx, cy - 60); ctx.lineTo(cx, cy + 60); ctx.stroke();
  ctx.fillStyle = axisColor; ctx.font = "10px Inter";
  ctx.fillText("Fx →", cx + 62, cy + 4);
  ctx.fillText("↑ Fy", cx + 4, cy - 62);
}

// ===== SIMULATION =====
async function runSimulation() {
  const btn = document.getElementById("sim-btn-text");
  const errEl = document.getElementById("sim-error");
  errEl.classList.add("hidden");

  const links = getLinks();
  const magnitude = parseFloat(document.getElementById("force-magnitude").value);
  const forceType = document.querySelector('input[name="force_type"]:checked').value;

  if (!magnitude || magnitude <= 0) { showSimError("Enter a valid force magnitude."); return; }

  btn.textContent = "⏳ Computing...";
  document.querySelector(".btn-primary").disabled = true;

  try {
    const res = await fetch(`${API}/simulate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(authToken ? { "Authorization": `Bearer ${authToken}` } : {}),
      },
      body: JSON.stringify({ links, external_force: magnitude, force_type: forceType }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Simulation failed");
    lastResult = data;
    renderResults(data);
    showTab("results");
  } catch (e) {
    showSimError(e.message);
  } finally {
    btn.textContent = "▶ Run Simulation";
    document.querySelector(".btn-primary").disabled = false;
  }
}

function showSimError(msg) {
  const el = document.getElementById("sim-error");
  el.textContent = msg; el.classList.remove("hidden");
}

// ===== RENDER RESULTS =====
function renderResults(data) {
  document.getElementById("no-results").classList.add("hidden");
  document.getElementById("results-content").classList.remove("hidden");

  const { links, results, external_force, force_type, method, residual, max_stress_link, direction_cosine_matrix, external_force_vector } = data;

  document.getElementById("result-subtitle").textContent =
    `${force_type.toUpperCase()} · ${external_force} N · ${links.length} links · ${method.replace(/_/g, " ")}`;

  const maxF = Math.max(...results.map(Math.abs));
  const minF = Math.min(...results.map(Math.abs));

  document.getElementById("summary-cards").innerHTML = `
    <div class="summary-card"><div class="s-label">Links</div><div class="s-value">${links.length}</div><div class="s-sub">suspension links</div></div>
    <div class="summary-card"><div class="s-label">Applied Force</div><div class="s-value">${external_force}</div><div class="s-sub">Newtons (${force_type})</div></div>
    <div class="summary-card danger"><div class="s-label">Max Link Force</div><div class="s-value">${maxF.toFixed(1)}</div><div class="s-sub">Link ${max_stress_link + 1} — overstressed</div></div>
    <div class="summary-card success"><div class="s-label">Min Link Force</div><div class="s-value">${minF.toFixed(1)}</div><div class="s-sub">Newtons</div></div>
    <div class="summary-card"><div class="s-label">Residual</div><div class="s-value" style="font-size:15px">${residual.toFixed(4)}</div><div class="s-sub">equilibrium error</div></div>
    <div class="summary-card"><div class="s-label">Fx / Fy</div><div class="s-value" style="font-size:14px">${external_force_vector[0].toFixed(0)} / ${external_force_vector[1].toFixed(0)}</div><div class="s-sub">force components (N)</div></div>`;

  // Direction Cosine Matrix
  if (direction_cosine_matrix?.length) {
    const headers = ["", ...links.map((_, i) => `L${i + 1}`)];
    const rowLabels = ["cos θ (Fx)", "sin θ (Fy)"];
    let html = `<table class="matrix-table"><thead><tr>${headers.map(h => `<th>${h}</th>`).join("")}</tr></thead><tbody>`;
    direction_cosine_matrix.forEach((row, ri) => {
      html += `<tr><td class="matrix-label">${rowLabels[ri]}</td>${row.map(v => `<td>${v.toFixed(4)}</td>`).join("")}</tr>`;
    });
    html += `</tbody></table>`;
    document.getElementById("matrix-display").innerHTML = html;
  }

  // Table
  document.getElementById("results-tbody").innerHTML = links.map((lnk, i) => `
    <tr>
      <td><strong>L${i + 1}</strong></td>
      <td>${lnk.angle}°</td>
      <td>${lnk.length} mm</td>
      <td style="font-family:'JetBrains Mono',monospace;color:${i === max_stress_link ? 'var(--danger)' : 'var(--text)'}">${results[i].toFixed(4)}</td>
      <td>${i === max_stress_link ? '<span class="badge-max">⚠ MAX STRESS</span>' : '<span class="badge-ok">OK</span>'}</td>
    </tr>`).join("");

  renderChart(links, results, max_stress_link);
  drawSuspensionDiagram(max_stress_link);
}

function renderChart(links, results, maxIdx) {
  const ctx = document.getElementById("force-chart").getContext("2d");
  if (forceChart) forceChart.destroy();
  const isDark = document.documentElement.getAttribute("data-theme") !== "light";
  const tickColor = isDark ? "#9ca3af" : "#475569";
  const gridColor = isDark ? "rgba(31,41,55,0.8)" : "rgba(203,213,225,0.6)";

  forceChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: links.map((_, i) => `Link ${i + 1}`),
      datasets: [{
        label: "Force T (N)",
        data: results.map(Math.abs),
        backgroundColor: results.map((_, i) => i === maxIdx ? "rgba(255,82,82,0.85)" : "rgba(224,64,251,0.75)"),
        borderColor: results.map((_, i) => i === maxIdx ? "#ff5252" : "#e040fb"),
        borderWidth: 2, borderRadius: 6,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => ` ${c.parsed.y.toFixed(4)} N` } } },
      scales: {
        x: { ticks: { color: tickColor }, grid: { color: gridColor } },
        y: { ticks: { color: tickColor }, grid: { color: gridColor }, title: { display: true, text: "Force (N)", color: tickColor } },
      },
    },
  });
}

// ===== PDF =====
async function downloadPDF() {
  if (!lastResult) return;
  try {
    const res = await fetch(`${API}/pdf`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(lastResult),
    });
    if (!res.ok) throw new Error("PDF generation failed");
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "suspension_simulation_report.pdf"; a.click();
    URL.revokeObjectURL(url);
  } catch (e) { alert("PDF error: " + e.message); }
}

// ===== HISTORY =====
async function loadHistory() {
  const container = document.getElementById("history-list");
  container.innerHTML = `<div style="color:var(--text3);text-align:center;padding:40px">Loading...</div>`;
  try {
    const res = await fetch(`${API}/history`, {
      headers: authToken ? { "Authorization": `Bearer ${authToken}` } : {},
    });
    const data = await res.json();
    if (!data.length) {
      container.innerHTML = `<div style="color:var(--text3);text-align:center;padding:40px">No simulations yet. Run one from the Builder!</div>`;
      return;
    }
    container.innerHTML = data.map(sim => `
      <div class="history-card">
        <div>
          <div class="history-title">${sim.links.length}-Link Suspension — ${(sim.force_type || "bump").toUpperCase()} Load</div>
          <div class="history-time">${new Date(sim.timestamp).toLocaleString()}</div>
          <div class="history-meta">
            <span class="history-tag accent">${sim.external_force} N</span>
            <span class="history-tag">${sim.links.length} links</span>
            <span class="history-tag">Max: ${Math.max(...sim.results.map(Math.abs)).toFixed(1)} N</span>
            <span class="history-tag">${(sim.method || "solver").replace(/_/g, " ")}</span>
          </div>
        </div>
        <div class="history-actions">
          <button class="btn-load" onclick='loadFromHistory(${JSON.stringify(sim).replace(/'/g, "&#39;")})'>Load</button>
          <button class="btn-del" onclick="deleteHistory('${sim._id}')">Delete</button>
        </div>
      </div>`).join("");
  } catch (e) {
    container.innerHTML = `<div style="color:var(--danger);text-align:center;padding:40px">Error: ${e.message}</div>`;
  }
}

function loadFromHistory(sim) {
  lastResult = sim;
  renderResults(sim);
  showTab("results");
}

async function deleteHistory(id) {
  if (!confirm("Delete this simulation?")) return;
  await fetch(`${API}/history/${id}`, { method: "DELETE" });
  loadHistory();
}

// ===== CHATBOT =====
function toggleChat() {
  document.getElementById("chatbot-panel").classList.toggle("hidden");
}

async function sendChat() {
  const input = document.getElementById("chat-input");
  const msg = input.value.trim();
  if (!msg) return;
  appendChatMsg(msg, "user");
  input.value = "";
  const typingEl = appendChatMsg("Thinking...", "bot", true);

  let context = "";
  if (lastResult) {
    context = `Simulation: ${lastResult.links.length} links, ${lastResult.external_force}N ${lastResult.force_type} load. ` +
      `Link forces: [${lastResult.results.map(v => v.toFixed(2)).join(", ")}] N. ` +
      `Max stress on Link ${lastResult.max_stress_link + 1}. Method: ${lastResult.method}.`;
  }

  try {
    const res = await fetch(`${API}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg, context }),
    });
    const data = await res.json();
    typingEl.remove();
    appendChatMsg(data.reply || data.error, "bot");
  } catch (e) {
    typingEl.remove();
    appendChatMsg("Connection error. Is the backend running?", "bot");
  }
}

function appendChatMsg(text, role, isTyping = false) {
  const container = document.getElementById("chat-messages");
  const div = document.createElement("div");
  div.className = `chat-msg ${role}`;
  div.innerHTML = `<div class="msg-bubble${isTyping ? " msg-typing" : ""}">${text}</div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return div;
}
