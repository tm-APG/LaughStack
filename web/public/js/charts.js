/* SVG chart layer: laugh timeline + shared tooltip.
   Marks follow the dataviz spec: thin bars with rounded data-ends anchored
   to the baseline, recessive hairline grid, hover tooltips, text in ink
   tokens (identity carried by the mark, never by colored text). */

const KIND_COLOR = {
  laugh: "var(--series-laugh)",
  applause: "var(--series-applause)",
  mixed: "var(--series-mixed)",
};
const KIND_LABEL = { laugh: "Laugh", applause: "Applause", mixed: "Laugh → applause" };

const SVG_NS = "http://www.w3.org/2000/svg";
function el(name, attrs = {}) {
  const n = document.createElementNS(SVG_NS, name);
  for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
  return n;
}

function fmtTime(s) {
  const m = Math.floor(s / 60);
  const sec = Math.round(s % 60);
  return `${m}:${String(sec).padStart(2, "0")}`;
}

/** Laugh timeline: x = set time, bar height = within-room intensity. */
export function laughTimeline(container, session) {
  const events = session.events || [];
  const dur = session.metrics?.duration_s || Math.max(60, ...events.map(e => e.end_s));
  const W = 960, H = 220, padL = 8, padR = 8, padT = 14, padB = 26;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const x = s => padL + (s / dur) * plotW;

  // intensity: rel_energy z clamped to [-1.5, 3] -> [0.18, 1] of plot height
  const zs = events.map(e => e.rel_energy ?? 0);
  const hFor = z => {
    const c = Math.max(-1.5, Math.min(3, z ?? 0));
    return (0.18 + 0.82 * ((c + 1.5) / 4.5)) * plotH;
  };

  const wrap = document.createElement("div");
  wrap.className = "chart-wrap";
  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img",
                          "aria-label": "Laugh timeline across the set" });

  // hairline grid: one line per 25/50/75% intensity
  for (const f of [0.25, 0.5, 0.75]) {
    svg.appendChild(el("line", {
      x1: padL, x2: W - padR, y1: padT + plotH * (1 - f), y2: padT + plotH * (1 - f),
      stroke: "var(--grid)", "stroke-width": 1,
    }));
  }
  // baseline
  svg.appendChild(el("line", {
    x1: padL, x2: W - padR, y1: padT + plotH, y2: padT + plotH,
    stroke: "var(--baseline)", "stroke-width": 1,
  }));
  // time ticks every 5 min (or 1 min for short sets)
  const tickStep = dur > 900 ? 300 : dur > 240 ? 60 : 30;
  for (let t = 0; t <= dur; t += tickStep) {
    const anchor = t === 0 ? "start" : (dur - t < tickStep ? "end" : "middle");
    const tx = el("text", {
      x: x(t), y: H - 8, "text-anchor": anchor,
      "font-size": 11, fill: "var(--text-muted)",
    });
    tx.textContent = fmtTime(t);
    svg.appendChild(tx);
  }

  const tooltip = document.createElement("div");
  tooltip.className = "viz-tooltip";

  events.forEach((e, i) => {
    const bw = Math.max(3, x(e.end_s) - x(e.start_s));
    const bh = hFor(zs[i]);
    const rect = el("rect", {
      x: x(e.start_s), y: padT + plotH - bh,
      width: bw, height: bh, rx: 3, ry: 3,
      fill: KIND_COLOR[e.kind] || KIND_COLOR.laugh,
    });
    // hover target bigger than the mark
    const hit = el("rect", {
      x: x(e.start_s) - 4, y: padT, width: bw + 8, height: plotH,
      fill: "transparent",
    });
    hit.addEventListener("mouseenter", () => {
      rect.setAttribute("opacity", "0.82");
      tooltip.innerHTML = `
        <div class="t">${fmtTime(e.start_s)} · ${KIND_LABEL[e.kind] || e.kind}</div>
        <div class="row"><span>Duration</span><span class="v">${(e.end_s - e.start_s).toFixed(1)} s</span></div>
        <div class="row"><span>Peak</span><span class="v">${e.peak_dbfs?.toFixed(1)} dBFS</span></div>
        <div class="row"><span>Room-relative</span><span class="v">${e.rel_energy != null ? (e.rel_energy >= 0 ? "+" : "") + e.rel_energy.toFixed(2) + " z" : "—"}</span></div>
        ${e.parent_index != null ? '<div class="t">stacked tag — excess-energy credited</div>' : ""}`;
      tooltip.style.display = "block";
    });
    hit.addEventListener("mousemove", ev => {
      const r = wrap.getBoundingClientRect();
      const left = Math.min(ev.clientX - r.left + 12, r.width - 170);
      tooltip.style.left = `${left}px`;
      tooltip.style.top = `${ev.clientY - r.top - 10}px`;
    });
    hit.addEventListener("mouseleave", () => {
      rect.removeAttribute("opacity");
      tooltip.style.display = "none";
    });
    svg.appendChild(rect);
    svg.appendChild(hit);
  });

  wrap.appendChild(svg);
  wrap.appendChild(tooltip);

  // legend: identity never color-alone (labels beside swatches)
  const kinds = [...new Set(events.map(e => e.kind))];
  if (kinds.length >= 1) {
    const legend = document.createElement("div");
    legend.className = "legend";
    for (const k of ["laugh", "mixed", "applause"]) {
      if (!kinds.includes(k)) continue;
      const item = document.createElement("span");
      item.className = "key";
      item.innerHTML = `<span class="swatch" style="background:${KIND_COLOR[k]}"></span>${KIND_LABEL[k]}`;
      legend.appendChild(item);
    }
    const hint = document.createElement("span");
    hint.className = "key";
    hint.style.marginLeft = "auto";
    hint.textContent = "bar height = intensity vs this room's median";
    legend.appendChild(hint);
    wrap.appendChild(legend);
  }
  container.replaceChildren(wrap);
}

/** Inline horizontal bar scaled against a max (sequential, one hue). */
export function inlineBar(value, max, width = 90) {
  const w = max > 0 ? Math.max(2, (value / max) * width) : 0;
  return `<span class="inline-bar" style="width:${w}px"></span>`;
}

/** Diverging delta bar centered at zero (blue = positive, red = negative). */
export function deltaBar(z, scale = 2.5) {
  if (z == null) return '<span class="delta-track"><span class="zero"></span></span>';
  const frac = Math.max(-1, Math.min(1, z / scale)) / 2; // -0.5..0.5
  const left = frac >= 0 ? 50 : 50 + frac * 100;
  const width = Math.abs(frac) * 100;
  const color = frac >= 0 ? "var(--div-pos)" : "var(--div-neg)";
  return `<span class="delta-track">
    <span class="fill" style="left:${left}%;width:${width}%;background:${color}"></span>
    <span class="zero"></span></span>`;
}
