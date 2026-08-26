/* App shell: hash router, sessions list, upload flow. */

import { demoMode, signIn, signOut, onUser, listSessions,
         getSession, createUpload } from "./api.js";
import { renderDashboard } from "./dashboard.js";
import { renderCompare } from "./compare.js";

const esc = s => String(s ?? "").replace(/[&<>"']/g,
  c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const main = document.querySelector("main");
let currentUser = null;

// ---- auth chrome ----------------------------------------------------------
onUser(u => {
  currentUser = u;
  const area = document.getElementById("auth-area");
  if (demoMode) {
    area.innerHTML = `<span>demo mode</span>`;
  } else if (u) {
    area.innerHTML = `<span>${esc(u.displayName || u.email || "signed in")}</span>
      <button class="ghost" id="signout">Sign out</button>`;
    area.querySelector("#signout").onclick = () => signOut();
  } else {
    area.innerHTML = `<button class="primary" id="signin">Sign in with Google</button>`;
    area.querySelector("#signin").onclick = () => signIn();
  }
  route();
});

// ---- router ----------------------------------------------------------------
window.addEventListener("hashchange", route);

function nav() {
  const h = location.hash || "#/sessions";
  document.querySelectorAll("header nav a").forEach(a => {
    a.classList.toggle("active", h.startsWith(a.getAttribute("href")));
  });
}

async function route() {
  nav();
  const h = location.hash || "#/sessions";
  if (demoMode) {
    const b = document.createElement("div");
    b.className = "demo-banner";
    b.innerHTML = `<b>Demo mode.</b> Showing bundled sample data. To go live:
      paste your Firebase config into <code>js/firebase-init.js</code> and deploy
      (see web/README.md).`;
    main.replaceChildren(b);
  } else {
    main.replaceChildren();
  }
  const view = document.createElement("div");
  main.appendChild(view);

  try {
    if (h.startsWith("#/session/")) {
      const id = decodeURIComponent(h.split("/")[2]);
      view.innerHTML = `<div class="empty">Loading session…</div>`;
      const session = await getSession(id);
      renderDashboard(view, session);
    } else if (h.startsWith("#/upload")) {
      renderUpload(view);
    } else if (h.startsWith("#/compare")) {
      await renderCompare(view);
    } else {
      await renderSessions(view);
    }
  } catch (e) {
    view.innerHTML = `<div class="empty">${esc(e.message)}</div>`;
  }
}

// ---- sessions list ----------------------------------------------------------
async function renderSessions(root) {
  if (!demoMode && !currentUser) {
    root.innerHTML = `<div class="empty">Sign in to see your sessions.</div>`;
    return;
  }
  root.innerHTML = `<div class="empty">Loading sessions…</div>`;
  const sessions = await listSessions();
  if (!sessions.length) {
    root.innerHTML = `<div class="empty">No sessions yet —
      <a href="#/upload">upload a set recording</a> to get started.</div>`;
    return;
  }
  root.innerHTML = sessions.map(s => {
    const m = s.metrics || {};
    return `<div class="session-row" data-id="${esc(s.id)}">
      <div class="who">
        <div class="name">${esc(s.performer || s.id)}</div>
        <div class="meta">${esc(s.venue || "")} ${s.venue && s.date ? "·" : ""} ${esc(s.date || "")}
          · ${esc(s.sourceType || "upload")}</div>
      </div>
      <span class="badge ${esc(s.status)}">${esc(s.status)}</span>
      ${s.status === "complete" ? `
        <div class="stat"><div class="v">${(m.lpm ?? 0).toFixed(1)}</div><div class="k">laughs/min</div></div>
        <div class="stat"><div class="v">${(m.parScore ?? 0).toFixed(1)}</div><div class="k">PAR</div></div>
        <div class="stat"><div class="v">${(m.nEvents ?? 0)}</div><div class="k">events</div></div>` : ""}
    </div>`;
  }).join("");
  root.querySelectorAll(".session-row").forEach(el => {
    el.addEventListener("click", () => {
      location.hash = `#/session/${encodeURIComponent(el.dataset.id)}`;
    });
  });
}

// ---- upload -----------------------------------------------------------------
function renderUpload(root) {
  root.innerHTML = `<div class="card">
    <h2>Analyze a set</h2>
    <div class="sub">upload a recording — WAV straight from the kit, or any
    common audio/video format (converted server-side)</div>
    <form class="stack" id="upform">
      <div class="dropzone" id="drop">Drop audio here or click to choose
        <input type="file" id="file" accept="audio/*,video/*,.wav,.mp3,.m4a,.flac,.mp4" hidden>
        <div class="note" id="fname"></div>
      </div>
      <label>Performer <input type="text" name="performer" placeholder="Jane Doe"></label>
      <label>Venue <input type="text" name="venue" placeholder="The Cellar"></label>
      <label>Date <input type="date" name="date"></label>
      <label>Source
        <select name="sourceType">
          <option value="upload">Phone / customer recording</option>
          <option value="kit">LaughStack kit (has cal tone)</option>
          <option value="youtube">Published video pull</option>
        </select></label>
      <progress id="prog" max="1" value="0" style="display:none"></progress>
      <button class="primary" type="submit" ${demoMode ? "disabled" : ""}>
        ${demoMode ? "Uploads disabled in demo mode" : "Upload & analyze"}</button>
      <div class="note">Recordings stay in your private bucket, are never used
        for training, and are deleted on the retention schedule in your
        agreement. Numbers from non-kit sources are labeled uncalibrated.</div>
    </form></div>`;

  const drop = root.querySelector("#drop");
  const fileInput = root.querySelector("#file");
  const fname = root.querySelector("#fname");
  let file = null;

  drop.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", () => {
    file = fileInput.files[0] || null;
    fname.textContent = file ? `${file.name} (${(file.size / 1e6).toFixed(1)} MB)` : "";
  });
  for (const ev of ["dragover", "dragleave", "drop"]) {
    drop.addEventListener(ev, e => {
      e.preventDefault();
      drop.classList.toggle("drag", ev === "dragover");
      if (ev === "drop" && e.dataTransfer.files.length) {
        file = e.dataTransfer.files[0];
        fname.textContent = `${file.name} (${(file.size / 1e6).toFixed(1)} MB)`;
      }
    });
  }

  root.querySelector("#upform").addEventListener("submit", async e => {
    e.preventDefault();
    if (!file) { alert("Choose an audio file first."); return; }
    const fd = new FormData(e.target);
    const meta = Object.fromEntries(fd.entries());
    const prog = root.querySelector("#prog");
    prog.style.display = "block";
    const btn = e.target.querySelector("button");
    btn.disabled = true;
    try {
      const id = await createUpload(file, meta, p => { prog.value = p; });
      location.hash = `#/session/${id}`;
    } catch (err) {
      alert(err.message);
      btn.disabled = false;
    }
  });
}
