// habits.art: renders the cards from habits.json. Nothing in here needs to change when habits are swapped.
(async function () {
  const grid = document.getElementById('grid');
  const phone = window.matchMedia('(max-width: 620px)');
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
            <h2>${esc(h.name)}</h2>
            ${h.text.map(t => `<p>${esc(t)}</p>`).join('')}
          </div>
        </div>
      </button>`;
    const card = cell.querySelector('.card');
    const length = h.text.join(' ').length;
    card.style.setProperty('--fit', Math.min(1, Math.sqrt(190 / length)).toFixed(3));
    card.addEventListener('click', () => {
      if (phone.matches) return;             // phones show drawing and text together, nothing to turn
      const on = card.classList.toggle('flipped');
      card.setAttribute('aria-pressed', String(on));
    });
    grid.appendChild(cell);
  }

  // habits.art/#pen-pal opens with that card in view and turned over
  function openFromHash() {
    const cell = location.hash && document.getElementById(location.hash.slice(1));
    if (!cell) return;
    cell.scrollIntoView({ block: 'center' });
    const card = cell.querySelector('.card');
    card.classList.add('flipped');
    card.setAttribute('aria-pressed', 'true');
  }
  window.addEventListener('hashchange', openFromHash);
  openFromHash();

  document.addEventListener('keydown', e => {
    if (e.key !== 'Escape') return;
    document.querySelectorAll('.card.flipped').forEach(c => {
      c.classList.remove('flipped');
      c.setAttribute('aria-pressed', 'false');
    });
  });
})();
