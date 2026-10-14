# Part 1: The core machine

| Lab | Course step | Concept |
|---|---|---|
| 1.1 | 1. Why CI/CD exists | The problem, felt locally |
| 1.2 | 2. Events → workflows | What starts a run |
| 1.3 | 3. Workflow → jobs → steps | Machines vs commands |
| 1.4 | 4. Runners | What machine you get |
| 1.5 | 5. Actions vs `run` | Reusable building blocks |
| 1.6 | 6. First real CI | Lint + types + tests gating every PR |

Labs 1.2–1.5 push straight to `main` (simple); from 1.6 on you use the
[PR loop](README.md#recipe-the-pr-loop-from-lab-16-on).

---

## Lab 1.1: Why CI/CD exists (step 1)

**Goal:** feel the "works on my machine" problem before automating it away.

1. Run the checks locally (venv active, see Lab 0.3): `ruff check .`, `mypy`, `pytest -v`.
2. Ask yourself: what in your environment could make these pass *here* but fail
   elsewhere? (Your Python version, packages installed globally, the `.venv` folder, …)
3. Open `requirements-dev.txt`: every tool version is pinned. That's the first
   defense; a clean machine running the same pinned versions is the second.

✅ **Checkpoint:** why does CI run on a fresh machine instead of a developer's laptop?
<details><summary>Answer</summary>
Laptops carry hidden state (tool versions, env vars, uncommitted files) that can make
tests pass for the wrong reasons. A fresh machine has only the repo plus what the
pipeline installs, so a pass is reproducible.
</details>

---

## Lab 1.2: Events → workflows (step 2)

**Goal:** see exactly what starts a workflow, and how filters change that.

```powershell
copy course\snippets\1-2-hello.yml .github\workflows\hello.yml
git add -A; git commit -m "Lab 1.2: hello workflow"; git push
```

🔍 **Observe:**
- **Actions** tab → **Hello** → the run → job **hello** → step **Who triggered me?**
  shows `Event: push`, `Branch: main`, your commit SHA and username.
- Now click **Run workflow** (it exists because of `workflow_dispatch`) → run it.
  The new run says `Event: workflow_dispatch`.

💥 **Break it: filters.** Push to a different branch:

```powershell
git switch -c experiment
git commit --allow-empty -m "push to a branch"
git push -u origin experiment
```

A **Hello** run starts for `experiment`, because `on: push` with no filter matches every branch.
Now edit `.github/workflows/hello.yml` on this branch so the trigger reads:

```yaml
on:
  push:
    branches: [main]
  workflow_dispatch:
```

```powershell
git add -A; git commit -m "only main"; git push
```

No new run appears. Why? GitHub reads the workflow **from the commit you pushed**,
and that commit now says "only main". Clean up:

```powershell
git switch main
git push origin --delete experiment
git branch -D experiment
```

✅ **Checkpoint:** you change a workflow on a feature branch. Which version runs for pushes to that branch?
<details><summary>Answer</summary>The version in the pushed commit, so you can test workflow changes on a branch before merging.</details>

---

## Lab 1.3: Workflow → jobs → steps (step 3)

**Goal:** see with your own eyes that jobs are separate machines and steps are separate shells.

```powershell
copy course\snippets\1-3-jobs.yml .github\workflows\jobs-lab.yml
git add -A; git commit -m "Lab 1.3: jobs lab"; git push
```

Actions → **Jobs lab** → **Run workflow**.

🔍 **Observe:**
- The run graph: `build` and `lint` start together; `deploy` waits for `build`.
- Each job prints a different machine name (`hostname`).
- In `build`: the `cd` and `export` from one step are gone in the next step,
  but the file from the first step is still there.
- In `deploy`: `dist/app.txt NOT found`. `needs:` gave the order, not the files.

✅ **Checkpoint:** how would `deploy` get `build`'s files? *(You'll do it in Lab 2.5 and Part 3.)*
<details><summary>Answer</summary>Upload them as an artifact in build, download it in deploy.</details>

---

## Lab 1.4: Runners (step 4)

```powershell
copy course\snippets\1-4-runners.yml .github\workflows\runners-lab.yml
git add -A; git commit -m "Lab 1.4: runners lab"; git push
```

Actions → **Runners lab** → **Run workflow**.

🔍 **Observe:**
- Three jobs, three operating systems, each chosen only by its `runs-on:` label.
- Compare CPUs and the pre-installed Python and Node versions: they differ per image.
  That's why real pipelines install exact versions instead of trusting what's there.
- Open the first step of any job, **Set up job**: it shows the runner image name and version.

✅ **Checkpoint:** why does the snippet use `ubuntu-24.04` instead of `ubuntu-latest`?
<details><summary>Answer</summary>`-latest` moves to newer images over time, which can break a pipeline with zero changes in your repo. Pinning makes the environment come from your YAML.</details>

---

## Lab 1.5: Actions vs `run` steps (step 5)

```powershell
copy course\snippets\1-5-actions.yml .github\workflows\actions-lab.yml
git add -A; git commit -m "Lab 1.5: actions lab"; git push
```

Actions → **Actions lab** → **Run workflow**.

🔍 **Observe:**
- `without-actions`: the workspace is **empty** and pytest fails. A fresh runner has no code.
- `with-actions`: `actions/checkout` brought the code, `actions/setup-python` installed
  exactly 3.12, then your own `run:` commands did the rest. 12 tests pass.
- **Set up job** lists "Download action repository 'actions/checkout@v7'": actions
  are other people's repos, fetched before your job starts.

✅ **Checkpoint:** what can an action access inside your job?
<details><summary>Answer</summary>Everything your own steps can: files, environment variables, the token, any secrets passed to the job. Actions aren't sandboxed, which is why you'll pin them in Lab 3.5.</details>

---

## Lab 1.6: Your first real CI workflow (step 6)

**Goal:** a CI workflow that checks every PR, and a `main` branch that won't accept red code.

**1. Replace the lab workflows with real CI:**

```powershell
git switch -c lab-1-6
del .github\workflows\hello.yml, .github\workflows\jobs-lab.yml, .github\workflows\runners-lab.yml, .github\workflows\actions-lab.yml
copy course\snippets\1-6-ci.yml .github\workflows\ci.yml
git add -A; git commit -m "Lab 1.6: first real CI"
git push -u origin HEAD
gh pr create --fill
gh pr checks --watch
```

🔍 **Observe:** the PR shows **CI / checks (pull_request)** running, then green.
Open it: Lint → Type check → Test, in order, on one machine. Merge it:

```powershell
gh pr merge --squash --delete-branch
git switch main; git pull
```

The merge itself triggers another CI run, this time a **push** to `main`.

**2. Protect `main`:** **Settings → Rules → Rulesets → New ruleset → New branch ruleset**

- Name: `protect-main` · Enforcement status: **Active**
- Target branches → **Add target → Include default branch**
- Tick **Require a pull request before merging** (required approvals: 0, since you work alone)
- Tick **Require status checks to pass** → **Add checks** → type `checks` → select it
- Tick **Block force pushes** → **Create**

💥 **Break it: a failing test.**

```powershell
git switch -c break-test
```

In `app/store.py`, in `create()`, change `title=data.title.strip()` to `title=data.title`.

```powershell
git add -A; git commit -m "Break title trimming"; git push -u origin HEAD
gh pr create --fill
gh pr checks --watch
```

🔍 **Observe:**
- CI fails. Click through to the log: `test_title_is_trimmed` failed, with expected vs actual shown.
- **Lint and Type check passed**: they can't catch logic bugs, only tests can.
- The merge button is **blocked** by your ruleset. That's CI as a real gate.

Fix it (undo the change), commit, push. The same PR re-runs automatically and turns green.
Merge with `gh pr merge --squash --delete-branch`.

💥 **Break it: lint.** On a new branch, add `import os` at the top of `app/store.py`
and open a PR. Lint fails with `F401`, and **Type check and Test are skipped**: a
failed step skips the rest of the job. In Lab 2.1 you'll make them run anyway.
Close that PR without merging: `gh pr close --delete-branch`.

✅ **Checkpoint:** why does pushing to a PR branch create **one** CI run, not two,
even though the workflow has both `push` and `pull_request` triggers?
<details><summary>Answer</summary>`push` is filtered to `branches: [main]`, so pushes to feature branches only fire `pull_request`.</details>

**Part 1 done.** Your repo now has real CI and a protected main branch.

Next: [Part 2: Data & control flow](part-2.md)
