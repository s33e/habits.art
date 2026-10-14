// habits.art/all: every habit, newest first. Cards are added in batches as you scroll.
(async function () {
  const grid = document.getElementById('grid');
  const phone = window.matchMedia('(max-width: 620px)');
  const BATCH = 12;                       // cards added at a time (a multiple of 3 keeps desktop rows full)
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

  function makeCell(h) {
    const cell = document.createElement('div');
    cell.className = 'cell';
    cell.id = h.slug;
    cell.innerHTML = `
      <button class="card" type="button" aria-pressed="false" aria-label="${esc(h.name)}, turn card">
        <div class="card-inner">
          <div class="face front"><img src="${esc(h.image)}" alt="${esc(h.name)}" width="600" height="600" loading="lazy" decoding="async"></div>
          <div class="face back">
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
      e.stopPropagation();
      if (phone.matches) return;             // phones show drawing and text together
      const wasOpen = card.classList.contains('flipped');
      closeAll();
      if (!wasOpen) setFlipped(card, true);
    });
    return cell;
  }

  // add cards up to index `upTo` (exclusive)
  let shown = 0;
  function showUpTo(upTo) {
    const frag = document.createDocumentFragment();
    while (shown < Math.min(upTo, habits.length)) frag.appendChild(makeCell(habits[shown++]));
    grid.insertBefore(frag, sentinel);
    if (shown >= habits.length) observer.disconnect(), sentinel.remove();
  }

  // an invisible marker at the end of the grid; when it nears the screen, the next batch is added
  const sentinel = document.createElement('div');
  sentinel.style.cssText = 'grid-column:1/-1;height:1px';
  grid.appendChild(sentinel);
  const observer = new IntersectionObserver(entries => {
    if (entries.some(e => e.isIntersecting)) showUpTo(shown + BATCH);
  }, { rootMargin: '1500px 0px' });   // start well before the end, so scrolling never waits
  showUpTo(BATCH);
  observer.observe(sentinel);

  // habits.art/all/#pen-pal opens with that card in view (and turned over on desktop)
  function openFromHash() {
    const slug = location.hash && decodeURIComponent(location.hash.slice(1));
    const i = slug ? habits.findIndex(h => h.slug === slug) : -1;
    if (i < 0) return;
    if (i >= shown) showUpTo(Math.ceil((i + 1) / BATCH) * BATCH);
    const cell = document.getElementById(slug);
    cell.scrollIntoView({ block: phone.matches ? 'start' : 'center' });
    closeAll();
    if (!phone.matches) setFlipped(cell.querySelector('.card'), true);
  }
  window.addEventListener('hashchange', openFromHash);
  openFromHash();

  document.addEventListener('click', closeAll);
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeAll(); });
})();
