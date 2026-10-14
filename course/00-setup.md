# Part 0: Setup

About 20 minutes. You need a GitHub account. Everything else is free.

## Lab 0.1: Install the tools (once)

Open **PowerShell** and run:

```powershell
winget install --id Git.Git -e
winget install --id GitHub.cli -e
winget install --id Python.Python.3.13 -e
```

Close and reopen PowerShell so the new commands are found, then check:

```powershell
git --version
gh --version
python --version
```

Log the GitHub CLI in (choose **GitHub.com → HTTPS → Login with a web browser**):

```powershell
gh auth login
```

If Git has never been used on this PC, set your identity once:

```powershell
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

## Lab 0.2: Put the project in the right place

This is the step that tripped us up earlier, so do it carefully.

1. Right-click `taskflow.zip` → **Extract All…** → extract to `C:\Users\<you>\`
   (your user folder). You'll get the folder `C:\Users\<you>\taskflow`.
2. In PowerShell:

```powershell
cd $HOME\taskflow
dir -Force
```

✅ **You must see** `.github`, `app`, `course`, `tests`, `Dockerfile`, `pyproject.toml`,
`requirements.txt`, `requirements-dev.txt` and `README.md`.
If you see a single `taskflow` folder instead, run `cd taskflow` and check again.
If `dir` shows nothing, the zip went somewhere else: find it and extract again.

## Lab 0.3: Run it locally, then publish the repo

**Run the app on your machine** (optional but recommended, since it's what CI will do on a fresh machine):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
ruff check .
mypy
pytest -v
uvicorn app.main:app --reload
```

Open <http://localhost:8000>, add a few to-dos, then open
<http://localhost:8000/health>. It says `"version": "dev"`. Later, the deployed app
will show the commit SHA here, which is how you'll prove which version is live.
Press `Ctrl+C` to stop the server.

> If `Activate.ps1` is blocked: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then retry.

**Create the GitHub repo and push:**

```powershell
git init -b main
git add -A
git commit -m "Initial commit: Taskflow app and course"
gh repo create taskflow --public --source=. --push
```

Make it **public**: hosted runners (including Windows and macOS), environment
protection rules, and required checks are free for public repos. It's also what
lets you show the project on your CV.

🔍 **Observe:** open `https://github.com/<owner>/taskflow`. The **Actions** tab offers
templates because there are no workflows yet. `.github/workflows/` holds only an empty
`.gitkeep` placeholder: GitHub runs nothing until a workflow file lands there.

Next: [Part 1: The core machine](part-1.md)
