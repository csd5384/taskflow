# Taskflow CI/CD course

Build a professional GitHub Actions pipeline for a real app, one lab per concept.
Every lab tells you **exactly what to do**, **what to look for**, and gives you
something to **break on purpose**, because seeing a failure is how the model sticks.

You end with a public repo you can put on your CV: a tested, linted, type-checked
FastAPI app with PR checks, a nightly cross-platform matrix, security scanning,
SHA-pinned dependencies, and staged deployments (staging → approved production)
to a live URL.

## The four parts

| Part | Labs | Course steps | You'll have at the end |
|---|---|---|---|
| [0. Setup](00-setup.md) | 0.1–0.3 | — | Repo on GitHub, app running locally |
| [1. The core machine](part-1.md) | 1.1–1.6 | 1–6 | A real CI workflow gating every PR |
| [2. Data & control flow](part-2.md) | 2.1–2.5 | 7–11 | Multi-job CI: matrix, gate check, artifacts, caching |
| [3. Delivery & security](part-3.md) | 3.1–3.5 | 12–15 | Image builds, staging/prod deploys with approval, OIDC, hardened workflows |
| [4. Reuse & scale](part-4.md) | 4.1–4.5 | 16–20 | Reusable workflows, composite actions, runner lab, tuning, portfolio-ready repo |

Every course step 1–20 is covered by at least one lab; the table at the top of
each part shows which.

## How the files work

- `course/snippets/` holds every workflow version, named by lab (`2-4-ci.yml` = Lab 2.4).
  Labs tell you which snippet to copy where. **Read the file after copying it**:
  the comments explain each new line, and that's where the learning is.
- `course/final/.github/` is the finished pipeline. You copy it in Lab 4.2, and you
  can compare against it any time you're stuck.
- Files in `course/` never run: GitHub only runs workflows inside `.github/workflows/`.

## Conventions

- **Terminal: PowerShell** (the default in Windows Terminal and VS Code on Windows).
  Commands are written for it. `<owner>` means your GitHub username.
- **Copying a snippet:** `copy course\snippets\1-2-hello.yml .github\workflows\hello.yml`
- 🔍 **Observe** = what to look at in the GitHub UI.
- 💥 **Break it** = a deliberate failure to experiment with.
- ✅ **Checkpoint** = a question to answer before moving on (answers are folded).

## Recipe: the PR loop (from Lab 1.6 on)

Once `main` is protected, every change goes through a pull request, just like at work:

```powershell
git switch main; git pull                    # start from the latest main
git switch -c lab-2-1                        # one branch per lab
# ...copy/edit files...
git add -A
git commit -m "Lab 2.1: contexts and variables"
git push -u origin HEAD
gh pr create --fill                          # opens the PR
gh pr checks --watch                         # watch CI live in the terminal
gh pr merge --squash --delete-branch         # when green
git switch main; git pull
```

## Recipe: swapping a required check

When a lab renames or replaces the check that `main` requires, the PR gets
stuck on "Expected — waiting for status to be reported", because the old check
will never run again. This happens in real teams too. Fix:

1. Open the PR and wait until the **new** checks have run once.
2. **Settings → Rules → Rulesets → protect-main → Require status checks to pass:**
   remove the old check, click **Add checks**, and add the new one (it now
   appears in the search because it has run). Save.
3. Back on the PR, the merge button unlocks. Merge.

## If something goes wrong

1. Read the red step's log from the bottom up (Lab 4.4 teaches the full toolkit).
2. Compare your file with the snippet or `course/final/`.
3. `gh run view --log-failed` shows only the failing logs in your terminal.
