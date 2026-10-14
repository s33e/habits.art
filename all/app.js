// all.habits.art: every habit, newest first. Filters by category and year, plus search.
(async function () {
  const grid = document.getElementById('grid');
  const chipsEl = document.getElementById('chips');
  const countEl = document.getElementById('count');
  const q = document.getElementById('q');
  const phone = window.matchMedia('(max-width: 620px)');
  const setFlipped = (card, on) => { card.classList.toggle('flipped', on); card.setAttribute('aria-pressed', String(on)); };
  const closeAll = () => document.querySelectorAll('.card.flipped').forEach(c => setFlipped(c, false));

  let habits = [];
  try {
    const v = document.querySelector('meta[name="data-version"]')?.content || '';
    habits = await fetch('habits.json?v=' + v, { cache: 'no-cache' }).then(r => r.json());
  } catch (e) {
    grid.textContent = 'The habits could not be loaded. Please reload the page.';
    return;
  }

  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const LABEL = { mindset: 'Mindset', relationships: 'Relationships', communication: 'Communication', decisions: 'Decisions',
                  productivity: 'Productivity', growth: 'Growth', health: 'Health', joy: 'Joy' };
  const fmt = d => new Date(d + 'T00:00:00').toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });

  // build every card once; filtering only shows or hides them
  for (const h of habits) {
    const cell = document.createElement('div');
    cell.className = 'cell';
    cell.id = h.slug;
    cell.innerHTML = `
      <button class="card" type="button" aria-pressed="false" aria-label="${esc(h.name)}, turn card">
        <div class="card-inner">
          <div class="face front"><img src="${esc(h.image)}" alt="${esc(h.name)}" width="600" height="600" loading="lazy" decoding="async"></div>
          <div class="face back">
            <p class="meta">#${h.number} · ${fmt(h.date)} · ${esc(LABEL[h.category] || '')}</p>
            <p class="lead">${esc(h.lead)}</p>
            ${h.text.map(t => `<p>${esc(t)}</p>`).join('')}
            <img class="mark" src="../assets/mark-grey.png" alt="" width="256" height="150">
          </div>
        </div>
      </button>`;
    const card = cell.querySelector('.card');
    const length = [h.lead, ...h.text].join(' ').length;
    card.style.setProperty('--fit', Math.min(1, Math.sqrt(175 / length)).toFixed(3));
    card.addEventListener('click', e => {
      if (phone.matches) return;
      e.stopPropagation();
      const wasOpen = card.classList.contains('flipped');
      closeAll();
      if (!wasOpen) setFlipped(card, true);
    });
    h.el = cell;
    h.hay = [h.name, h.lead, ...h.text].join(' ').toLowerCase();
    grid.appendChild(cell);
  }
  const empty = document.createElement('p');
  empty.className = 'empty'; empty.textContent = 'No habit matches. Try another word.';
  grid.appendChild(empty);

  // filter chips: All, the categories present, then the years
  const cats = Object.keys(LABEL).filter(c => habits.some(h => h.category === c));
  const years = [...new Set(habits.map(h => h.date.slice(0, 4)))];
  const filters = [{ key: 'all', label: 'All' }, ...cats.map(c => ({ key: 'c:' + c, label: LABEL[c] })), ...years.map(y => ({ key: 'y:' + y, label: y }))];
  let active = 'all';
  for (const f of filters) {
    const b = document.createElement('button');
    b.className = 'chip'; b.type = 'button'; b.textContent = f.label;
    b.setAttribute('aria-pressed', String(f.key === active));
    b.addEventListener('click', () => {
      active = f.key;
      chipsEl.querySelectorAll('.chip').forEach(c => c.setAttribute('aria-pressed', String(c === b)));
      apply();
    });
    chipsEl.appendChild(b);
  }

  function apply() {
    const words = q.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
    let shown = 0;
    for (const h of habits) {
      const okFilter = active === 'all'
        || (active.startsWith('c:') && h.category === active.slice(2))
        || (active.startsWith('y:') && h.date.startsWith(active.slice(2)));
      const ok = okFilter && words.every(w => h.hay.includes(w));
      h.el.hidden = !ok;
      if (ok) shown++;
    }
    empty.hidden = shown > 0;
    const word = n => n === 1 ? 'habit' : 'habits';
    countEl.textContent = shown === habits.length ? `${shown} ${word(shown)}` : `${shown} of ${habits.length} ${word(habits.length)}`;
  }
  q.addEventListener('input', apply);
  apply();

  // all.habits.art/#pen-pal opens with that card in view and turned over
  function openFromHash() {
    const cell = location.hash && document.getElementById(decodeURIComponent(location.hash.slice(1)));
    if (!cell) return;
    if (cell.hidden) { active = 'all'; q.value = ''; chipsEl.firstChild.click(); }
    cell.scrollIntoView({ block: 'center' });
    closeAll();
    if (!phone.matches) setFlipped(cell.querySelector('.card'), true);
  }
  window.addEventListener('hashchange', openFromHash);
  openFromHash();

  document.addEventListener('click', closeAll);
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeAll(); });
})();
