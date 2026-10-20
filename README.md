# PyStudio

A browser-based Python editor for students, with a visual debugger and class management.

**Editor:** https://abidbkk.github.io/pystudio/ (students use the school's Apps Script link so their files save online)

## Features
- Python 3.12 running entirely in the browser (via [Pyodide](https://pyodide.org))
- Breakpoints, step over / into / out, continue, and **step backwards** through a recorded run
- Variables & call-stack panel that highlights changed values, plus watch expressions
- Interactive `input()` in the output console
- School Google sign-in; each student's files are saved to their own folder in the teacher's Google Drive
- Teacher view: browse classes and students, open, run, debug and edit their files, with near-live refresh

## How it fits together
- `index.html` is the whole editor, served by GitHub Pages.
- `apps-script/` is a tiny Google Apps Script web app. It signs people in with their school account,
  shows the editor in a frame, and saves and loads files in Google Drive. The class list is a Google Sheet.

Setup steps are in [SETUP.md](SETUP.md).

## Run locally
```
python -m http.server 8765
```
then open http://localhost:8765. Opened directly like this, files are saved in the browser only.
