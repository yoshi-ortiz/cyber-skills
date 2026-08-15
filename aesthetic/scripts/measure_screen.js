// Paste-and-run probe for the browser pane. Measures what the user can SEE,
// because counting markup is how invisible controls kept passing review.
// Returns {rows, visibleShots, deadShots:[...], tinyText, worst}
(() => {
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
    .filter(n => n.children.length === 0 && n.textContent.trim())
    .map(n => parseFloat(getComputedStyle(n).fontSize));
  const tiny = sizes.filter(s => s < 9).length;
  return JSON.stringify({
    rows: rows.length, visibleShots: visible, deadShots: dead.slice(0, 6),
    tinyTextNodes: tiny, smallestFontPx: sizes.length ? Math.min(...sizes) : null,
  }, null, 1);
})()
