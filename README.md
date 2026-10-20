# PyStudio

A browser-based Python editor for students, with a visual debugger.

**Use it:** https://abidbkk.github.io/pystudio/

## Features
- Python 3.12 running entirely in the browser (via [Pyodide](https://pyodide.org)) — no server needed
- Breakpoints, step over / into / out, continue, and **step backwards** through a recorded run
- Variables & call-stack panel that highlights changed values, plus watch expressions
- Interactive `input()` in the output console
- Multiple files, saved automatically in the browser; upload / download `.py` files

## Notes
- Files are stored in the student's browser (localStorage) on that device. Use **Download** to keep a copy.
- Debug recording stops after 5,000 steps to catch infinite loops.

## Run locally
```
python -m http.server 8765
```
then open http://localhost:8765
