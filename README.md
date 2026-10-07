# habits.art

A 3×3 gallery of Happy Habits. Each card shows the drawing; tap it and it turns over to the habit's text.

## Swap a habit

1. Edit `habits.txt`: one slug per line, top to bottom = left to right, row by row.
2. Run `python3 build.py`. It pulls drawings and texts from
   [s33e/happyhabits-site](https://github.com/s33e/happyhabits-site), writes `habits.json`
   and the web images, and removes images that are no longer used.
3. Commit and push. GitHub Pages publishes within a minute or two.

The build stops with a clear message if a slug is unknown, has no drawing or has no text.

## Files

| File | Role |
|---|---|
| `habits.txt` | The selection. The only file you edit. |
| `build.py` | Turns the selection into `habits.json` and `images/`. |
| `habits.json`, `images/` | Generated. Don't edit by hand. |
| `index.html`, `style.css`, `app.js` | The site. Renders whatever is in `habits.json`. |

Texts are cleaned automatically: the leading emoji is dropped, and if an entry holds a
second version after ` // `, only the first is used.

The page is `noindex` for now; remove that line from `index.html` when it should be findable.
