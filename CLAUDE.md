# PyStudio — notes for Claude

A browser Python editor with a step-through debugger, built for the teacher (Abid Khan, ICS Amman,
a.khan@ics.edu.jo) and their Computer Science classes. Students use it in lessons.

## How it fits together
| Part | Where | Notes |
|---|---|---|
| Editor (everything the user sees) | `index.html`, one file, served by **GitHub Pages** at https://abidbkk.github.io/pystudio/ (repo `abidbkk/pystudio`, public) | `git push` to `main` publishes in ~1 min. Check with `gh api repos/abidbkk/pystudio/pages/builds/latest`. |
| Sign-in "door" + server | `apps-script/` (`Code.gs`, `index.html`, `loadtest.html`) in the teacher's Google Apps Script project https://script.google.com/d/1eZDTMFnKGrqdUYjrClxuT99YsE3McGJBxcOqPAk6w6jEwGzhJum9ogsL/edit | **Not deployed automatically.** The teacher pastes the files in (raw links: `https://raw.githubusercontent.com/abidbkk/pystudio/main/apps-script/<file>`) and does Deploy → Manage deployments → ✏️ → New version → Deploy. Executes as the teacher, access "Anyone within ics.edu.jo". Students open the `/exec` link; the door frames the GitHub page and relays `google.script.run` calls via postMessage (allow-list `ALLOWED` in `apps-script/index.html`). |
| Files and class lists | Teacher's Google Drive | *PyStudio files* folder: `<Class>/<Name (email)>/…` per student, `<Class>/_Class files (students can see these)/`, `Teachers/<email>/`. Class list = *PyStudio – Classes* spreadsheet (tabs Courses, Students, Teachers). Folder ids are in Script Properties (`f:<email>`, `f:class:<name>`). |

Python runs in the browser with Pyodide 0.26 in a Web Worker. The debugger records every step with
`sys.settrace` and replays it (so you can step backwards). `input()` re-runs the program with the
answers so far. Turtle is a recording module (`dev/turtle.py`) drawn on a canvas.

## Editing
- `index.html` is the source of truth for the page. The Python translator (`dev/pseudo.py`) and turtle
  module (`dev/turtle.py`) are embedded in it: **edit the file in `dev/`, then run `python dev/embed.py`.**
- Keep the existing style: small vanilla JS, CSS variables for colours (light default, `data-theme="dark"`).
- After changing `apps-script/*`, tell the teacher exactly which files to paste and to redeploy.
  Changes that only touch `index.html` need no Apps Script step (but the teacher may need Ctrl+Shift+R).

## Testing (no access to the real Google server from here)
- Local server: `python -m http.server 8765` in the project folder, then open http://localhost:8765 in the browser pane.
- `dev/gas-mock.js` fakes DriveApp/PropertiesService/CacheService/SpreadsheetApp/Session. In the page:
  load it and `apps-script/Code.gs` with `(0,eval)(await (await fetch(url)).text())`, then replace
  `bridge.call` with a function that calls the Code.gs functions, and set `GAS.as` to act as a user.
- `dev/opcount.js` counts Drive operations per request for a given Code.gs (performance comparisons).
- Pseudocode: `cd dev/pseudo_tests && PYTHONIOENCODING=utf-8 python show.py <file.py>`.
- Real-server load test: the teacher opens `<exec link>?page=loadtest` (teachers only).

## Decisions the teacher has made (keep them)
- **Pseudocode (Cambridge IGCSE 0984):** 0-based arrays `ARRAY[0:n]`; `DECLARE` lines added; PascalCase
  names (i, j, k kept); `IF … THEN` on one line, `ELSEIF … THEN` for Python `elif`, `ELSE`, `ENDIF`
  (an `else:` containing an `if` stays nested); `CASE OF` only from Python `match`; written-out lists on
  one line (`Numbers ← [1, 2, 3]`); `random.randint(a, b)` → `ROUND(RANDOM() * (b - a), 0) + a` with a
  `// a whole number from a to b` comment.
- **Model solutions for classes:** no functions (`def`), every `for` loop uses `range(start, stop)`
  with an explicit start, no `in` membership tests, no `max/min/sum/break`, no lists where the task can
  be done with comparisons. Year 11 solutions are in the teacher's PyStudio files, folder `Y11`
  (local copies in `.scratch/y11/`, deliberately **not** committed: the repo is public).
- **Saving:** the newest save wins; no clash copies are ever made.
- **Class files are read-only for students** (they can run, debug and copy; no personal copy is made).
  Sharing a file to a class does not copy the teacher's folder name.
- New students start with one file `hello.py` containing `# Start typing your code here`.
- Look: light by default; 🌙 switches the whole page dark (per browser). ☰ hides the file sidebar
  (open on every start). Folders start closed. File buttons: two rows of small text buttons under the list.
- Student folders are created in advance (`prepareFolders`, also run by `importFromClassroom`).
- Don't rename a class's "Name in PyStudio" once in use: class files are linked by name.

## Working with the teacher
- Plain explanations; they are a teacher, not a developer. Ask before changing or deleting student work.
- Year 11 class in Classroom/Drive is the folder `10/CSciC 2025-2026` (owned by co-teacher N.Karamh).
- Syllabus reference: Cambridge IGCSE (9–1) Computer Science 0984, 2026–2028 (pseudocode guide pp. 35–48).
