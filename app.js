// habits.art: renders the cards from habits.json. Nothing in here needs to change when habits are swapped.
(async function () {
  const grid = document.getElementById('grid');
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

  for (const h of habits) {
    const cell = document.createElement('div');
    cell.className = 'cell';
    cell.id = h.slug;
    cell.innerHTML = `
      <button class="card" type="button" aria-pressed="false" aria-label="${esc(h.name)}, turn card">
        <div class="card-inner">
          <div class="face front"><img src="${esc(h.image)}" alt="${esc(h.name)}" width="1200" height="1200" loading="lazy"></div>
          <div class="face back">
            <p class="lead"><img class="mark" src="assets/mark.png" alt="" width="256" height="150">${esc(h.lead)}</p>
            ${h.text.map(t => `<p>${esc(t)}</p>`).join('')}
          </div>
        </div>
      </button>`;
    const card = cell.querySelector('.card');
    const length = [h.lead, ...h.text].join(' ').length;
    card.style.setProperty('--fit', Math.min(1, Math.sqrt(190 / length)).toFixed(3));
    card.addEventListener('click', e => {
      if (phone.matches) return;             // phones show drawing and text together, nothing to turn
      e.stopPropagation();
      const wasOpen = card.classList.contains('flipped');
      closeAll();
      if (!wasOpen) setFlipped(card, true);  // only one card shows its text at a time
    });
    grid.appendChild(cell);
  }

  // phones: a quiet arrow under the first card says there is more below
  const hint = document.createElement('img');
  hint.className = 'scroll-hint'; hint.src = 'assets/scroll-down.png'; hint.alt = ''; hint.width = 150; hint.height = 256;
  grid.firstElementChild?.appendChild(hint);

  // habits.art/#pen-pal opens with that card in view and turned over
  function openFromHash() {
    const cell = location.hash && document.getElementById(location.hash.slice(1));
    if (!cell) return;
    cell.scrollIntoView({ block: 'center' });
    closeAll();
    setFlipped(cell.querySelector('.card'), true);
  }
  window.addEventListener('hashchange', openFromHash);
  openFromHash();

  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeAll(); });
  document.addEventListener('click', () => closeAll());   // a click on the background turns the open card back
})();
