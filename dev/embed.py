"""Copy dev/pseudo.py and dev/turtle.py into index.html (they run inside the page's Python).

Run from the project folder after editing either file:   python dev/embed.py
"""
import pathlib

root = pathlib.Path(__file__).resolve().parent.parent
page = root / "index.html"
html = page.read_text(encoding="utf-8")
for block_id, source in [("pseudo-src", "pseudo.py"), ("turtle-src", "turtle.py")]:
    code = (root / "dev" / source).read_text(encoding="utf-8")
    assert "</script" not in code, f"{source} must not contain </script"
    start_tag = f'<script type="text/python" id="{block_id}">\n'
    a = html.index(start_tag) + len(start_tag)
    b = html.index("</script>", a)
    html = html[:a] + code + html[b:]
page.write_text(html, encoding="utf-8")
print("Embedded pseudo.py and turtle.py into index.html")
