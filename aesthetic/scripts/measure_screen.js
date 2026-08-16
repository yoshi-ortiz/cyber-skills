// Paste-and-run probe for the browser pane. Measures what the user can SEE,
// because counting markup is how invisible controls kept passing review.
// Returns {rows, visibleShots, deadShots, tinyText, unreadable, worstContrast}
//
// The contrast pass exists because the two worst screens this harness ever
// served both LOOKED correct in markup. A block painted `background:#fff` and
// left its colour to inherit, so it drew the companion frame's near-white on
// white at 1.09:1 and read as an empty box; and prose written for paper was
// served inside that dark frame at 1.33:1. Neither is visible to any check
// that reads HTML, and both are one number away from obvious.
(() => {
  const parse = (c) => {
    const m = (c || '').match(/[\d.]+/g);
    if (!m) return null;
    return { r: +m[0], g: +m[1], b: +m[2], a: m.length > 3 ? +m[3] : 1 };
  };
  const over = (f, b) => ({
    r: f.r * f.a + b.r * (1 - f.a), g: f.g * f.a + b.g * (1 - f.a),
    b: f.b * f.a + b.b * (1 - f.a), a: 1,
  });
  const lum = (c) => {
    const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
    return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b);
  };
  // Composite every translucent layer up the tree. Stopping at the first
  // non-transparent background reads `rgba(0,0,0,.05)` as solid black and
  // reports a false failure against perfectly legible text.
  const ground = (el) => {
    const stack = [];
    let n = el;
    while (n && n !== document.documentElement) {
      const c = parse(getComputedStyle(n).backgroundColor);
      if (c && c.a > 0) { stack.push(c); if (c.a === 1) break; }
      n = n.parentElement;
    }
    let acc = parse(getComputedStyle(document.documentElement).backgroundColor)
      || { r: 255, g: 255, b: 255, a: 1 };
    if (acc.a !== 1) acc = over(acc, { r: 255, g: 255, b: 255, a: 1 });
    for (let i = stack.length - 1; i >= 0; i--) acc = over(stack[i], acc);
    return acc;
  };

  const rows = [...document.querySelectorAll('[data-element]')];
  const dead = [];
  let visible = 0;
  for (const row of rows) {
    const shot = row.querySelector('.dh-shot');
    if (!shot) { dead.push({ el: row.dataset.element, why: 'no .dh-shot' }); continue; }
    const r = shot.getBoundingClientRect();
    const cs = getComputedStyle(shot);
    if (r.width < 24 || r.height < 24 || cs.display === 'none' || cs.visibility === 'hidden') {
      dead.push({ el: row.dataset.element, w: Math.round(r.width), h: Math.round(r.height),
                  display: cs.display });
    } else visible++;
  }

  const sizes = [...document.querySelectorAll('*')]
    .filter((n) => n.children.length === 0 && n.textContent.trim())
    .map((n) => parseFloat(getComputedStyle(n).fontSize));
  const tiny = sizes.filter((s) => s < 9).length;

  // One entry per offending RULE, not per instance: the fix is a rule, and a
  // per-instance list buries that under thirty copies of the same class.
  const failures = {};
  let worst = 21;
  for (const el of document.querySelectorAll('body *')) {
    const own = [...el.childNodes].filter((n) => n.nodeType === 3)
      .map((n) => n.textContent.trim()).join(' ').trim();
    if (own.length < 8) continue;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) < 0.1) continue;
    const fg = parse(cs.color);
    if (!fg) continue;
    const bg = ground(el);
    const a = lum(over(fg, bg)), b = lum(bg);
    const ratio = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
    const px = parseFloat(cs.fontSize), bold = +cs.fontWeight >= 700;
    const floor = (px >= 24 || (px >= 18.66 && bold)) ? 3 : 4.5;  // WCAG large-text allowance
    if (ratio < worst) worst = ratio;
    if (ratio < floor) {
      const key = el.className || el.tagName;
      if (!failures[key] || failures[key].ratio > ratio) {
        failures[key] = { ratio: +ratio.toFixed(2), needs: floor,
                          px: cs.fontSize, sample: own.slice(0, 40) };
      }
    }
  }

  return JSON.stringify({
    rows: rows.length, visibleShots: visible, deadShots: dead.slice(0, 6),
    tinyTextNodes: tiny, smallestFontPx: sizes.length ? Math.min(...sizes) : null,
    worstContrast: +worst.toFixed(2),
    unreadable: Object.keys(failures).length, failingRules: failures,
  }, null, 1);
})()
