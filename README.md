# PyStudio

A browser-based Python editor for students, with a visual debugger.

**Use it:** https://abidbkk.github.io/pystudio/

## Features
- Python 3.12 running entirely in the browser (via [Pyodide](https://pyodide.org)) — no server needed
- Breakpoints, step over / into / out, continue, and **step backwards** through a recorded run
- Variables & call-stack panel that highlights changed values, plus watch expressions
- Interactive `input()` in the output console
- Multiple files, saved automatically; upload / download `.py` files
- Optional sign-in with a school Google account so files are saved online and follow the student to any computer (Firebase — see [SETUP.md](SETUP.md))

## Notes
- Until Firebase is configured, or when a student chooses "Use without signing in", files are stored only in that browser. Use **Download** to keep a copy.
- Debug recording stops after 5,000 steps to catch infinite loops.

## Run locally
```
python -m http.server 8765
```
then open http://localhost:8765
