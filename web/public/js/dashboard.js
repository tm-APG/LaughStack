/* Session dashboard: stat tiles, laugh timeline, QC panel, per-bit table. */

import { laughTimeline, inlineBar } from "./charts.js";

const esc = s => String(s ?? "").replace(/[&<>"']/g,
  c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function fmt(v, digits = 1) {
  return v == null ? "—" : Number(v).toFixed(digits);
}

export function renderDashboard(root, session) {
  if (session._pending) {
    const d = session._pending;
    root.innerHTML = `<div class="card"><h2>Analysis ${esc(d.status)}</h2>
      <div class="sub">${d.status === "error"
        ? esc(d.error || "unknown error")
        : "This page will show the full dashboard once the analyzer finishes. Refresh in a minute."}</div></div>`;
    return;
  }

  const m = session.metrics || {};
  const a = session.audio || {};
  const jokes = session.jokes || [];
  const silent = jokes.filter(j => !(j.events || []).length).length;

  root.innerHTML = `
    <div style="display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:14px">
      <h1 style="margin:0;font-size:22px">${esc(session.performer || session.session_id)}</h1>
      <span style="color:var(--text-muted);font-size:13.5px">
        ${esc(session.venue || "")} ${session.venue && session.date ? "·" : ""} ${esc(session.date || "")}
        · source: ${esc(a.source_type || "?")}</span>
    </div>

    <div class="grid-tiles">
      ${tile("Laughs / min", fmt(m.laughs_per_minute, 2))}
      ${tile("Laugh sec / min", fmt(m.laugh_s_per_minute, 1),
             "18+ = headliner benchmark")}
      ${tile("PAR score", fmt(m.par_score, 1), "% of stage time laughing · 30 = headliner")}
      ${tile("Laugh events", m.n_events ?? "—")}
      ${tile("Longest silence", fmt(m.longest_silence_s, 0), "seconds")}
      ${tile("Applause breaks", m.applause_breaks ?? 0)}
    </div>

    <div class="card">
      <h2>Laugh map</h2>
      <div class="sub">every audience response across the set — hover for detail</div>
      <div id="timeline"></div>
    </div>

    <div class="card">
      <h2>Recording QC</h2>
      <div id="qc"></div>
    </div>

    <div class="card">
      <h2>Per-bit results</h2>
      <div class="sub">${jokes.length
        ? `${jokes.length} bits · ${silent} silent (silence is data — dead bits stay in the table)`
        : "No transcript attached — per-bit scores need transcription (enable in the analyzer or attach a set list)."}</div>
      <div id="bits" style="overflow-x:auto"></div>
    </div>`;

  laughTimeline(root.querySelector("#timeline"), session);
  renderQC(root.querySelector("#qc"), a);
  if (jokes.length) renderBits(root.querySelector("#bits"), jokes);
}

function tile(label, value, context = "") {
  return `<div class="tile"><div class="label">${label}</div>
    <div class="value">${value}</div>
    ${context ? `<div class="context">${context}</div>` : ""}</div>`;
}

function renderQC(el, audio) {
  const items = [];
  const ok = (t) => items.push(`<div class="qc-item ok"><span class="icon">✓</span><span>${t}</span></div>`);
  const warn = (t) => items.push(`<div class="qc-item warn"><span class="icon">▲</span><span>${t}</span></div>`);
  const fail = (t) => items.push(`<div class="qc-item fail"><span class="icon">✕</span><span>${t}</span></div>`);

  if (audio.qc_passed) ok("QC gates passed"); else fail("QC gates failed — treat numbers with care");
  if (audio.cal_tone_offset_s != null)
    ok(`Cal tone found at ${audio.cal_tone_offset_s.toFixed(1)}s (level ${fmt(audio.cal_tone_level_dbfs)} dBFS) — levels calibrated`);
  else
    warn("No cal tone — numbers are uncalibrated; within-session comparisons only");
  if (audio.rt60_s != null) ok(`RT60 ${audio.rt60_s.toFixed(2)}s — decay times room-corrected`);
  else warn("No room measurement — decay times include the venue's reverb");
  if (audio.noise_floor_dbfs != null) {
    (audio.noise_floor_dbfs <= -45 ? ok : warn)(
      `Noise floor ${audio.noise_floor_dbfs.toFixed(1)} dBFS`);
  }
  for (const n of audio.qc_notes || []) warn(esc(n));
  el.innerHTML = items.join("");
}

function renderBits(el, jokes) {
  const maxLaugh = Math.max(...jokes.map(j =>
    (j.events || []).reduce((s, e) => s + (e.end_s - e.start_s), 0)), 0.001);
  const rows = jokes.map((j, i) => {
    const laughS = (j.events || []).reduce((s, e) => s + (e.end_s - e.start_s), 0);
    const z = bestZ(j);
    const silent = !(j.events || []).length;
    return `<tr>
      <td class="num">${i + 1}</td>
      <td class="punch" title="${esc(j.punchline_text)}">${esc(j.punchline_text || "(unaligned response)")}</td>
      <td class="num">${silent
        ? '<span class="badge silent">silent</span>'
        : `${laughS.toFixed(1)}s ${inlineBar(laughS, maxLaugh)}`}</td>
      <td class="num">${z == null ? "—" : (z >= 0 ? "+" : "") + z.toFixed(2)}</td>
      <td class="num">${j.latency_s == null ? "—" : j.latency_s.toFixed(2) + "s"}</td>
      <td class="num">${j.position_in_set == null ? "—" : Math.round(j.position_in_set * 100) + "%"}</td>
    </tr>`;
  }).join("");
  el.innerHTML = `<table class="data">
    <thead><tr><th class="num">#</th><th>Punchline</th>
      <th class="num">Laugh time</th><th class="num">Energy (z)</th>
      <th class="num">Latency</th><th class="num">Position</th></tr></thead>
    <tbody>${rows}</tbody></table>
    <div class="note">Energy z is measured against this room's own median laugh
    (median/MAD) — comparable across venues. Stacked tags are credited only
    with energy above the previous laugh's decay.</div>`;
}

function bestZ(j) {
  const zs = (j.events || []).map(e => e.rel_energy).filter(v => v != null);
  return zs.length ? Math.max(...zs) : null;
}
