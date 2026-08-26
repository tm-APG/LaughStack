/* A/B compare view: pick two completed sessions, render the matched-joke
   table with diverging delta bars. */

import { compare, listSessions } from "./api.js";
import { deltaBar } from "./charts.js";

const esc = s => String(s ?? "").replace(/[&<>"']/g,
  c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

export async function renderCompare(root) {
  root.innerHTML = `<div class="card"><h2>A/B comparison</h2>
    <div class="sub">match the same jokes across two analyzed sets — scores are
    within-room z, so a hot Friday crowd doesn't automatically beat a Tuesday mic</div>
    <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:end">
      <label style="font-size:13px;color:var(--text-secondary)">Session A<br>
        <select id="sel-a"></select></label>
      <label style="font-size:13px;color:var(--text-secondary)">Session B<br>
        <select id="sel-b"></select></label>
      <button class="primary" id="run">Compare</button>
    </div>
    <div id="cmp-out" style="margin-top:18px"></div></div>`;

  const sessions = (await listSessions()).filter(s => s.status === "complete");
  const opts = sessions.map(s =>
    `<option value="${esc(s.id)}">${esc(s.performer || s.id)} — ${esc(s.venue || "")} ${esc(s.date || "")}</option>`).join("");
  const selA = root.querySelector("#sel-a");
  const selB = root.querySelector("#sel-b");
  selA.innerHTML = opts; selB.innerHTML = opts;
  if (sessions.length > 1) selB.selectedIndex = 1;

  const out = root.querySelector("#cmp-out");
  if (sessions.length < 2) {
    out.innerHTML = `<div class="empty">Need at least two completed sessions to compare.</div>`;
    return;
  }

  root.querySelector("#run").addEventListener("click", async () => {
    out.innerHTML = `<div class="empty">Matching jokes…</div>`;
    try {
      const res = await compare(selA.value, selB.value);
      renderResult(out, res, selA.value, selB.value);
    } catch (e) {
      out.innerHTML = `<div class="empty">Comparison failed: ${esc(e.message)}</div>`;
    }
  });
  // auto-run once
  root.querySelector("#run").click();
}

function renderResult(out, res, aId, bId) {
  if (!res.rows?.length) {
    out.innerHTML = `<div class="empty">No jokes matched across both sessions —
      material may differ, or per-bit alignment (transcription) is missing.</div>`;
    return;
  }
  const rows = res.rows.map(r => `<tr>
    <td class="punch" title="${esc(r.joke)}">${esc(r.joke)}</td>
    <td class="num">${r.deltaTotalLaughS >= 0 ? "+" : ""}${r.deltaTotalLaughS.toFixed(1)}s</td>
    <td><div class="delta-cell">
      <span style="font-variant-numeric:tabular-nums">${r.deltaEnergyRel == null ? "—" :
        (r.deltaEnergyRel >= 0 ? "+" : "") + r.deltaEnergyRel.toFixed(2)}</span>
      ${deltaBar(r.deltaEnergyRel)}</div></td>
    <td class="num">${r.deltaLatencyS == null ? "—" :
        (r.deltaLatencyS >= 0 ? "+" : "") + r.deltaLatencyS.toFixed(2) + "s"}</td>
    <td>${esc(r.verdict)}${r.positionConfound != null && r.positionConfound > 0.25
        ? "" : ""}</td>
  </tr>`).join("");
  out.innerHTML = `
    <div class="legend" style="margin-bottom:8px">
      <span class="key"><span class="swatch" style="background:var(--div-pos)"></span>B stronger</span>
      <span class="key"><span class="swatch" style="background:var(--div-neg)"></span>A stronger</span>
      <span class="key" style="margin-left:auto">${res.matched} joke(s) matched · A=${esc(aId)} · B=${esc(bId)}</span>
    </div>
    <div style="overflow-x:auto"><table class="data">
      <thead><tr><th>Joke</th><th class="num">Δ laugh</th>
        <th class="num">Δ energy z (A → B)</th><th class="num">Δ latency</th>
        <th>Verdict</th></tr></thead>
      <tbody>${rows}</tbody></table></div>`;
}
