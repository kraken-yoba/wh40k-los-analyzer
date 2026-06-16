# Project Infrastructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the public-ready monorepo infrastructure for the Warhammer 40k LOS analysis tool.

**Architecture:** This plan creates the repository shell, documentation, Python backend scaffolding, frontend scaffolding, shared schemas, scripts, and CI definitions without implementing the PDF extraction or LOS algorithms. The resulting repo should be ready for future TDD feature slices and safe for public publication without redistributing official PDF binaries.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, pytest, Ruff, mypy, TypeScript, React, Vite, Vitest, Playwright, GitHub Actions, npm, uv.

---

## File Structure

- Bootstrap local development tools: `uv` for Python and Node/npm for frontend lockfile generation.
- Create `.gitignore` for generated outputs, official PDF caches, local tool caches, Python artifacts, and frontend artifacts.
- Create `.editorconfig` and `.gitattributes` for consistent formatting and line endings.
- Create `README.md`, `LICENSE`, `NOTICE.md`, and `.env.example` for public repository readiness.
- Create `pyproject.toml`, `backend/fortyk_los_backend/`, and `backend/tests/` for Python scaffolding.
- Create `frontend/package.json`, `frontend/tsconfig*.json`, `frontend/vite.config.ts`, `frontend/src/`, and `frontend/tests/` for frontend scaffolding.
- Create `schemas/README.md`, `fixtures/README.md`, and `scripts/` entry points.
- Create `.github/workflows/ci.yml` for public-safe CI.

## Task 0: Toolchain Bootstrap

**Files:**
- Modify: local user Python environment for `uv`.
- Modify: `C:\tmp\fortyk-los-tools\` for portable Node if system Node/npm is unavailable.

- [ ] **Step 1: Install uv if missing**

Run:

```powershell
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
  python -m pip install --user uv
}
uv --version
```

Expected: `uv --version` prints an installed version.

- [ ] **Step 2: Install portable Node/npm if missing**

Run:

```powershell
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
  New-Item -ItemType Directory -Force C:\tmp\fortyk-los-tools | Out-Null
  Invoke-WebRequest `
    -Uri https://nodejs.org/dist/v22.22.1/node-v22.22.1-win-x64.zip `
    -OutFile C:\tmp\fortyk-los-tools\node-v22.22.1-win-x64.zip
  Expand-Archive `
    -Path C:\tmp\fortyk-los-tools\node-v22.22.1-win-x64.zip `
    -DestinationPath C:\tmp\fortyk-los-tools `
    -Force
  $env:PATH = "C:\tmp\fortyk-los-tools\node-v22.22.1-win-x64;$env:PATH"
}
npm --version
```

Expected: `npm --version` prints an installed version.

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

# Node / frontend
node_modules/
frontend/dist/
frontend/coverage/
frontend/playwright-report/
frontend/test-results/

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

Local tooling for deterministic visual analysis of Warhammer 40k table layouts, terrain footprints, deployment zones, and base-aware 2D line of sight.

## Status

This repository is in infrastructure setup. The extraction and LOS engines are planned but not implemented yet.

## Source Policy

Official Warhammer PDFs and rules text are third-party source material and are not redistributed by this repository. The app stores source URLs and hashes in manifests, while downloaded PDFs and rendered pages stay in a local gitignored cache.

## Planned Stack

- Python 3.12 backend with FastAPI, Pydantic, PyMuPDF, OpenCV, Shapely, pytest, Ruff, and mypy.
- TypeScript frontend with React, Vite, Zod, Vitest, and Playwright.
- Public-safe GitHub Actions for linting, typing, unit tests, and synthetic fixtures.

## Development Commands

```powershell
.\scripts\verify.ps1
```

The full official-PDF regression gate requires a local pinned PDF cache and is intentionally separate from public-safe CI.
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

Create `pyproject.toml`:

```toml
[project]
name = "fortyk-los-analyzer"
version = "0.1.0"
description = "Local deterministic Warhammer 40k LOS analysis tooling"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.115.0",
  "httpx>=0.27.0",
  "opencv-python-headless>=4.10.0.84",
  "pydantic>=2.8.0",
  "pymupdf>=1.24.0",
  "shapely>=2.0.0",
  "uvicorn>=0.30.0",
]

[dependency-groups]
dev = [
  "mypy>=1.10.0",
  "pytest>=8.2.0",
  "pytest-cov>=5.0.0",
  "ruff>=0.5.0",
]

[tool.uv]
package = false

[tool.pytest.ini_options]
testpaths = ["backend/tests"]
pythonpath = ["backend"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP"]

[tool.mypy]
python_version = "3.12"
strict = true
mypy_path = "backend"
```

- [ ] **Step 3: Run the test and verify it fails**

Run:

```powershell
python -m pytest backend/tests/test_app.py -q
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
python -m pytest backend/tests/test_app.py -q
```

Expected: one passing test.

- [ ] **Step 6: Commit backend skeleton**

Run:

```powershell
git add pyproject.toml backend
git commit -m "chore: add backend tooling skeleton"
```

Expected: commit succeeds.

## Task 3: Frontend Tooling Skeleton

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/index.html`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/App.test.tsx`
- Create: `frontend/src/test/setup.ts`

- [ ] **Step 1: Create frontend package metadata**

Create `frontend/package.json`:

```json
{
  "name": "fortyk-los-frontend",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite --host 127.0.0.1",
    "build": "tsc -b && vite build",
    "lint": "eslint .",
    "format:check": "prettier --check .",
    "test": "vitest run",
    "test:e2e": "playwright test"
  },
  "dependencies": {
    "@vitejs/plugin-react": "^4.3.0",
    "vite": "^5.4.0",
    "typescript": "^5.5.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "zod": "^3.23.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.4.0",
    "@testing-library/react": "^16.0.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "eslint": "^9.8.0",
    "prettier": "^3.3.0",
    "vitest": "^2.0.0",
    "jsdom": "^24.1.0",
    "@playwright/test": "^1.45.0"
  }
}
```

- [ ] **Step 2: Write the frontend smoke test first**

Create `frontend/src/App.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { App } from "./App";

describe("App", () => {
  it("renders the infrastructure-ready shell", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "Warhammer 40k LOS Analyzer" })).toBeInTheDocument();
    expect(screen.getByText("Infrastructure ready")).toBeInTheDocument();
  });
});
```

- [ ] **Step 3: Create minimal frontend source**

Create `frontend/src/App.tsx`:

```tsx
export function App() {
  return (
    <main>
      <h1>Warhammer 40k LOS Analyzer</h1>
      <p>Infrastructure ready</p>
    </main>
  );
}
```

Create `frontend/src/main.tsx`:

```tsx
import React from "react";
import ReactDOM from "react-dom/client";

import { App } from "./App";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

Create `frontend/src/test/setup.ts`:

```ts
import "@testing-library/jest-dom/vitest";
```

Create `frontend/index.html`:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Warhammer 40k LOS Analyzer</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

Create `frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["DOM", "DOM.Iterable", "ES2020"],
    "allowJs": false,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "module": "ESNext",
    "moduleResolution": "Node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "types": ["vitest/globals", "@testing-library/jest-dom"]
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

Create `frontend/tsconfig.node.json`:

```json
{
  "compilerOptions": {
    "composite": true,
    "module": "ESNext",
    "moduleResolution": "Node",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

Create `frontend/vite.config.ts`:

```ts
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
  },
});
```

- [ ] **Step 4: Verify frontend dependency blocker or tests**

Run:

```powershell
npm --version
```

Expected: `npm --version` prints a version. Then run:

```powershell
npm install --package-lock-only --prefix frontend
npm test --prefix frontend
```

Expected: `frontend/package-lock.json` exists and the smoke test passes.

- [ ] **Step 5: Commit frontend skeleton**

Run:

```powershell
git add frontend
git commit -m "chore: add frontend tooling skeleton"
```

Expected: commit succeeds.

## Task 4: Shared Schemas, Fixtures, Scripts, And CI

**Files:**
- Create: `schemas/README.md`
- Create: `fixtures/README.md`
- Create: `scripts/verify.ps1`
- Create: `scripts/verify_backend.ps1`
- Create: `scripts/verify_frontend.ps1`
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

- [ ] **Step 2: Create verification scripts**

Create `scripts/verify_backend.ps1`:

```powershell
$ErrorActionPreference = "Stop"
python -m pytest backend/tests -q
```

Create `scripts/verify_frontend.ps1`:

```powershell
$ErrorActionPreference = "Stop"
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
  Write-Host "npm is not installed; skipping frontend verification."
  exit 0
}
npm test --prefix frontend
```

Create `scripts/verify.ps1`:

```powershell
$ErrorActionPreference = "Stop"
& "$PSScriptRoot\verify_backend.ps1"
& "$PSScriptRoot\verify_frontend.ps1"
```

- [ ] **Step 3: Create public-safe CI**

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
  pull_request:

jobs:
  backend:
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

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - run: npm ci
        working-directory: frontend
      - run: npm run build
        working-directory: frontend
      - run: npm test
        working-directory: frontend
```

- [ ] **Step 4: Verify scripts**

Run:

```powershell
.\scripts\verify.ps1
```

Expected: backend tests pass; frontend verification runs with npm and the frontend smoke test passes.

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

Expected: authenticated account. If the token is invalid, stop GitHub publication and report the exact re-authentication command.

- [ ] **Step 2: Create the public repository after auth works**

Use these defaults unless the user overrides them before this task runs:

- Owner: authenticated GitHub user.
- Repository name: `wh40k-los-analyzer`.
- Visibility: public.
- License: MIT for project code.

Run:

```powershell
gh repo create wh40k-los-analyzer --public --source . --remote origin --description "Deterministic local Warhammer 40k LOS and terrain-layout analysis tool"
git push -u origin main
git push -u origin codex/project-infrastructure
```

Expected: remote `origin` exists, `main` and `codex/project-infrastructure` are pushed.

- [ ] **Step 3: Verify remote**

Run:

```powershell
git remote -v
gh repo view --web
```

Expected: repository exists and opens in browser if GUI access is available.
