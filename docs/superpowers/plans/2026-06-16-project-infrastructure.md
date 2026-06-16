# Project Infrastructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the public-ready Python-only monorepo infrastructure for the Warhammer 40k LOS analysis tool.

**Architecture:** FastAPI serves both backend APIs and the local browser GUI. The GUI uses Jinja2 templates, CSS, and small vanilla JavaScript modules for SVG/Canvas interaction, with no Node/npm build chain.

**Tech Stack:** Python 3.12, uv, FastAPI, Jinja2, Pydantic, pytest, pytest-cov, pytest-playwright, Ruff, mypy, PyMuPDF, OpenCV, Shapely, GitHub Actions.

---

## File Structure

- `.gitignore`, `.editorconfig`, `.gitattributes`, `README.md`, `LICENSE`, `NOTICE.md`, and `.env.example` define public repository metadata.
- `pyproject.toml`, `uv.lock`, `backend/fortyk_los_backend/`, and `backend/tests/` define the Python app and tests.
- `backend/fortyk_los_backend/templates/` contains server-rendered GUI pages.
- `backend/fortyk_los_backend/static/` contains CSS and vanilla JavaScript assets.
- `schemas/` and `fixtures/` document generated schemas and safe fixtures.
- `scripts/` contains setup, dev, and verification commands.
- `.github/workflows/ci.yml` runs public-safe Python-only CI.

## Task 0: Toolchain Bootstrap

**Files:**
- Modify: local user Python environment for `uv`.

- [ ] **Step 1: Install uv if missing**

Run:

```powershell
if (-not (python -m uv --version 2>$null)) {
  python -m pip install --user uv
}
python -m uv --version
```

Expected: `python -m uv --version` prints an installed version.

## Task 1: Branch And Repository Metadata

**Files:**
- Create: `.gitignore`
- Create: `.editorconfig`
- Create: `.gitattributes`
- Create: `README.md`
- Create: `LICENSE`
- Create: `NOTICE.md`
- Create: `.env.example`

- [ ] **Step 1: Move work onto an implementation branch**

Run:

```powershell
git branch -m main
git switch -c codex/project-infrastructure
```

Expected: current branch is `codex/project-infrastructure`; base branch is `main`.

- [ ] **Step 2: Create repository metadata files**

Create `.gitignore`:

```gitignore
# Python
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
.venv/
dist/
build/
*.egg-info/

# Local source assets and generated outputs
.cache/
data/cache/
data/pdfs/
data/renders/
data/outputs/
*.pdf
*.png
*.jpg
*.jpeg
*.webp
*.tiff

# Vision verifier and local env
.env
.env.*
!.env.example
vision-cache/

# Superpowers local worktrees / mockups
.worktrees/
.superpowers/
```

Create `.editorconfig`:

```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
indent_style = space
indent_size = 2
trim_trailing_whitespace = true

[*.py]
indent_size = 4

[*.md]
trim_trailing_whitespace = false
```

Create `.gitattributes`:

```gitattributes
* text=auto eol=lf
*.bat text eol=crlf
*.ps1 text eol=crlf
```

Create `README.md`:

```markdown
# Warhammer 40k LOS Analyzer

Local Python tooling for deterministic visual analysis of Warhammer 40k table layouts, terrain footprints, deployment zones, and base-aware 2D line of sight.

## Status

This repository is in infrastructure setup. The next implementation milestone is the deterministic data spine: source manifests, canonical geometry schemas, synthetic fixtures, validation records, and stable exports.

## Source Policy

Official Warhammer PDFs and rules text are third-party source material and are not redistributed by this repository. The app stores source URLs and hashes in manifests, while downloaded PDFs and rendered pages stay in a local gitignored cache.

## Planned Stack

- Python 3.12 local web app with FastAPI, Jinja2, Pydantic, PyMuPDF, OpenCV, Shapely, pytest, Ruff, mypy, and Python Playwright.
- Browser GUI served by FastAPI using templates, CSS, vanilla JavaScript, SVG, and Canvas.
- Public-safe GitHub Actions for linting, typing, unit tests, and synthetic fixtures.

## Development Commands

```powershell
.\scripts\verify.cmd
.\scripts\dev.cmd
```

Additional gates are split so public CI stays copyright-safe:

```powershell
.\scripts\verify-public.cmd
.\scripts\verify-gui.cmd
.\scripts\verify-full-local.cmd
```

The full official-PDF regression gate requires a local pinned PDF cache and is intentionally separate from public-safe CI. Use `verify-full-local.cmd -RequireOfficialPdfRegression` once the official-cache regression harness exists.
```

Create `LICENSE`:

```text
MIT License

Copyright (c) 2026 Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

Create `NOTICE.md`:

```markdown
# Notices

This project is an independent analysis tool.

Warhammer, Warhammer 40,000, and related rules, PDFs, artwork, names, and marks are third-party material owned by their respective rights holders. This repository does not redistribute official PDF binaries or rules text.

Project source code is licensed under the repository license. Third-party source documents remain governed by their original terms.
```

Create `.env.example`:

```dotenv
# Optional vision verifier settings. Production extraction must remain deterministic.
VISION_VERIFIER_PROVIDER=
VISION_VERIFIER_MODEL=
VISION_VERIFIER_API_KEY=

# Local cache paths. These are gitignored.
FORTYK_LOS_CACHE_DIR=data/cache
FORTYK_LOS_PDF_DIR=data/pdfs
```

- [ ] **Step 3: Verify metadata files**

Run:

```powershell
git diff --check
```

Expected: no whitespace errors.

- [ ] **Step 4: Commit metadata**

Run:

```powershell
git add .gitignore .editorconfig .gitattributes README.md LICENSE NOTICE.md .env.example
git commit -m "chore: add repository metadata"
```

Expected: commit succeeds.

## Task 2: Python Backend Tooling Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `uv.lock`
- Create: `backend/fortyk_los_backend/__init__.py`
- Create: `backend/fortyk_los_backend/app.py`
- Create: `backend/tests/test_app.py`

- [ ] **Step 1: Write the backend health test first**

Create `backend/tests/test_app.py`:

```python
from fastapi.testclient import TestClient

from fortyk_los_backend.app import app


def test_health_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Create Python project config**

Create `pyproject.toml` with FastAPI, Jinja2, PyMuPDF, OpenCV, Shapely, Pydantic, pytest, pytest-cov, pytest-playwright, Ruff, and mypy dependencies.

- [ ] **Step 3: Run the test and verify it fails**

Run:

```powershell
python -m uv run pytest backend/tests/test_app.py -q
```

Expected: fails because `fortyk_los_backend.app` does not exist.

- [ ] **Step 4: Create minimal backend app**

Create `backend/fortyk_los_backend/__init__.py`:

```python
"""Backend package for the Warhammer 40k LOS analyzer."""
```

Create `backend/fortyk_los_backend/app.py`:

```python
from fastapi import FastAPI

app = FastAPI(title="Warhammer 40k LOS Analyzer")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 5: Verify backend test passes**

Run:

```powershell
python -m uv run pytest backend/tests/test_app.py -q
```

Expected: one passing test and no warnings.

- [ ] **Step 6: Commit backend skeleton**

Run:

```powershell
git add pyproject.toml uv.lock backend
git commit -m "chore: add backend tooling skeleton"
```

Expected: commit succeeds.

## Task 3: Python-Served GUI Skeleton

**Files:**
- Create: `backend/fortyk_los_backend/templates/index.html`
- Create: `backend/fortyk_los_backend/static/styles.css`
- Create: `backend/fortyk_los_backend/static/app.js`
- Modify: `backend/fortyk_los_backend/app.py`
- Create: `backend/tests/test_gui.py`

- [ ] **Step 1: Write the GUI route test first**

Create `backend/tests/test_gui.py`:

```python
from fastapi.testclient import TestClient

from fortyk_los_backend.app import app


def test_index_serves_local_gui_shell() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "Warhammer 40k LOS Analyzer" in response.text
    assert "Infrastructure ready" in response.text
    assert "/static/app.js" in response.text
```

- [ ] **Step 2: Run the GUI test and verify it fails**

Run:

```powershell
python -m uv run pytest backend/tests/test_gui.py -q
```

Expected: fails because `/` is not implemented.

- [ ] **Step 3: Add templates and static assets**

Create `backend/fortyk_los_backend/templates/index.html`:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Warhammer 40k LOS Analyzer</title>
    <link rel="stylesheet" href="/static/styles.css" />
  </head>
  <body>
    <main class="app-shell">
      <h1>Warhammer 40k LOS Analyzer</h1>
      <p id="status">Infrastructure ready</p>
      <section class="board-frame" aria-label="Board analysis canvas">
        <canvas id="board-canvas" width="880" height="1200"></canvas>
      </section>
    </main>
    <script type="module" src="/static/app.js"></script>
  </body>
</html>
```

Create `backend/fortyk_los_backend/static/styles.css`:

```css
:root {
  color: #202124;
  background: #f7f5ef;
  font-family: Arial, sans-serif;
}

body {
  margin: 0;
}

.app-shell {
  max-width: 1120px;
  margin: 0 auto;
  padding: 24px;
}

.board-frame {
  border: 1px solid #79756d;
  background: #fffdf7;
  max-width: 440px;
}

#board-canvas {
  display: block;
  width: 100%;
  height: auto;
}
```

Create `backend/fortyk_los_backend/static/app.js`:

```javascript
const canvas = document.querySelector("#board-canvas");
const context = canvas.getContext("2d");

context.fillStyle = "#fffaf0";
context.fillRect(0, 0, canvas.width, canvas.height);
context.strokeStyle = "#2f2f2f";
context.lineWidth = 8;
context.strokeRect(4, 4, canvas.width - 8, canvas.height - 8);
```

- [ ] **Step 4: Serve the GUI from FastAPI**

Modify `backend/fortyk_los_backend/app.py`:

```python
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

PACKAGE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Warhammer 40k LOS Analyzer")
app.mount("/static", StaticFiles(directory=PACKAGE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=PACKAGE_DIR / "templates")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html")
```

- [ ] **Step 5: Verify GUI and backend tests pass**

Run:

```powershell
python -m uv run pytest backend/tests -q
```

Expected: two passing tests and no warnings.

- [ ] **Step 6: Commit Python GUI skeleton**

Run:

```powershell
git add backend
git commit -m "chore: add python-served GUI skeleton"
```

Expected: commit succeeds.

## Task 4: Shared Schemas, Fixtures, Scripts, And CI

**Files:**
- Create: `schemas/README.md`
- Create: `fixtures/README.md`
- Create: `scripts/verify.ps1`
- Create: `scripts/dev.ps1`
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create schema and fixture notes**

Create `schemas/README.md`:

```markdown
# Schemas

Generated JSON Schema files will live here after backend Pydantic models are implemented.

Canonical schema output must be deterministic: sorted keys, fixed float precision, explicit units, and stable enum values.
```

Create `fixtures/README.md`:

```markdown
# Fixtures

This directory is for synthetic fixtures and copyright-safe golden outputs.

Official PDFs are not committed here. They belong in the local gitignored cache documented by `pdf_manifest.json`.
```

- [ ] **Step 2: Create scripts**

Create `scripts/verify.ps1`:

```powershell
$ErrorActionPreference = "Stop"
python -m uv run ruff check .
python -m uv run mypy backend
python -m uv run pytest backend/tests -q
```

Create `scripts/dev.ps1`:

```powershell
$ErrorActionPreference = "Stop"
python -m uv run uvicorn fortyk_los_backend.app:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

- [ ] **Step 3: Create public-safe CI**

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
  pull_request:

jobs:
  python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: uv sync --group dev
      - run: uv run ruff check .
      - run: uv run mypy backend
      - run: uv run pytest backend/tests -q
```

- [ ] **Step 4: Verify scripts**

Run:

```powershell
.\scripts\verify.cmd
```

Expected: Ruff, mypy, and pytest pass.

- [ ] **Step 5: Commit scripts and CI**

Run:

```powershell
git add schemas fixtures scripts .github
git commit -m "chore: add verification scripts and CI"
```

Expected: commit succeeds.

## Task 5: GitHub Publication Prep

**Files:**
- Modify: local git configuration and remote only.

- [ ] **Step 1: Check GitHub CLI authentication**

Run:

```powershell
gh auth status
```

Expected: authenticated account. If the token is invalid, stop GitHub publication and report:

```powershell
gh auth login -h github.com
```

- [ ] **Step 2: Create the public repository after auth works**

Use these defaults unless the user overrides them before this task runs:

- Owner: authenticated GitHub user.
- Repository name: `wh40k-los-analyzer`.
- Visibility: public.
- License: MIT for project code.

Run:

```powershell
gh repo create wh40k-los-analyzer --public --source . --remote origin --description "Python local Warhammer 40k LOS and terrain-layout analysis tool"
git push -u origin main
git push -u origin codex/project-infrastructure
```

Expected: remote `origin` exists, `main` and `codex/project-infrastructure` are pushed.
