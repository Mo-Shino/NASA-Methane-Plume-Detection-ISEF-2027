from pathlib import Path

server_path = Path("server.py")
content = server_path.read_text(encoding="utf-8")

target = 'app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")'
replacement = '''app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

PRESENTATION_DIR = PROJECT_ROOT / "docs" / "presentation"
PRESENTATION_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/presentation", StaticFiles(directory=str(PRESENTATION_DIR), html=True), name="presentation")

@app.get("/presentation", response_class=HTMLResponse)
def serve_presentation():
    pres_file = PRESENTATION_DIR / "index.html"
    if not pres_file.exists():
        return HTMLResponse("<h1>Presentation Loading...</h1>", status_code=200)
    return HTMLResponse(
        content=pres_file.read_text(encoding="utf-8"),
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
    )
'''

if target in content:
    new_content = content.replace(target, replacement, 1)
    server_path.write_text(new_content, encoding="utf-8")
    print("SUCCESS: server.py updated with /presentation mount")
else:
    print("ERROR: Target line not found")
