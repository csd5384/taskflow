# Part 4: Reuse & scale

| Lab | Course step | Concept |
|---|---|---|
| 4.1 | 16. Reusable workflows | One `checks.yml` called by CI, Nightly and Release |
| 4.2 | 17. Custom actions | Composite actions for setup and deploy (= the final pipeline) |
| 4.3 | 18. Self-hosted runners | Your PC as a runner: persistence, ephemeral mode |
| 4.4 | 19. Debugging, performance & cost | Diagnose, measure, a classic required-check trap |
| 4.5 | 20. Capstone | Release v1.0.0 and make the repo portfolio-ready |

---

## Lab 4.1: Reusable workflows (step 16)

**Problem you created:** `release.yml` deploys whatever lands on `main` without running
the checks, and the checks live only in `ci.yml`. Copy-pasting them would drift.
Fix: one reusable `checks.yml`, called from three places.

```powershell
git switch main; git pull; git switch -c lab-4-1
copy course\snippets\4-1-checks.yml .github\workflows\checks.yml
copy course\snippets\4-1-ci.yml .github\workflows\ci.yml
copy course\snippets\4-1-nightly.yml .github\workflows\nightly.yml
copy course\snippets\4-1-release.yml .github\workflows\release.yml
git add -A; git commit -m "Lab 4.1: reusable checks workflow"; git push -u origin HEAD
gh pr create --fill
```

⚠️ Called jobs get new names: the gate is now **`checks / ci-passed`**. Do the
[required-check swap](README.md#recipe-swapping-a-required-check) (`ci-passed` → `checks / ci-passed`), then merge.

🔍 **Observe:**
- `ci.yml` is now ~20 lines: triggers, concurrency, and one `uses:` with `full-matrix: false`.
- In the run, jobs appear nested: `checks / quick-checks`, `checks / test (…)`.
- After merging, **Release** runs `checks` with the **full matrix first**, and `build` waits
  for it (`needs: checks`). Nothing deploys unless every check passes.
- Actions → **Nightly** → **Run workflow**: the same checks, full matrix, no deploy.
  It also runs every night at 02:23 UTC on its own.
- `checks.yml` itself has no triggers except `workflow_call`: it never runs alone.

💥 **Break it: typed inputs.** On a branch, change `full-matrix: false` in `ci.yml` to
`full-matrix: "nope"` and push a PR. The run fails **before any job starts**, with an
input type error. Reusable workflows have typed interfaces. Close the PR.

✅ **Checkpoint:** inside `checks.yml`, which repository's code does `actions/checkout` fetch, and which event does `github.event_name` show?
<details><summary>Answer</summary>The caller's: same repo, and the caller's event (pull_request, schedule, push…). A called workflow runs in the caller's context.</details>

---

## Lab 4.2: Composite actions (step 17) → the final pipeline

**Problem:** every job repeats setup-python + install, and the two deploy jobs repeat
~25 lines of deploy and smoke-test script. Composite actions turn each into one step.

This lab installs the finished pipeline from `course/final/` and removes the lab-only workflows:

```powershell
git switch main; git pull; git switch -c lab-4-2
Copy-Item -Recurse -Force course\final\.github\* .github\
del .github\workflows\secrets-lab.yml, .github\workflows\oidc-lab.yml
gh secret delete DEMO_SECRET 2>$null
dir -Recurse .github
git add -A; git commit -m "Lab 4.2: composite actions, final pipeline"; git push -u origin HEAD
gh pr create --fill
```

`dir -Recurse .github` should list `actions\setup-python-project\action.yml`,
`actions\deploy-render\action.yml`, `dependabot.yml` and the workflows
`checks.yml`, `ci.yml`, `nightly.yml`, `release.yml`, `coverage-comment.yml`.

🔍 **Observe:**
- Open both `action.yml` files: inputs, outputs, `runs: using: composite`, and a
  `shell:` on every `run` step (required in composites).
- In a run's log, the step **Run ./.github/actions/setup-python-project** expands into its inner steps.
- In `release.yml`, each deploy job is now: checkout → `uses: ./.github/actions/deploy-render`.
  The deploy logic exists in one place.

Merge, approve production, and confirm both URLs report the new SHA.

💥 **Break it: local action before checkout.** On a branch, in `checks.yml`'s `quick-checks`
job, move the `setup-python-project` step **above** `actions/checkout`. Push a PR. The job
fails: "Can't find 'action.yml'". Local actions live in the repo, and a fresh runner has
no repo until checkout. Close the PR.

✅ **Checkpoint:** when would you choose a composite action, and when a reusable workflow?
<details><summary>Answer</summary>Composite action: reuse steps inside a job (setup, deploy procedure). Reusable workflow: reuse whole jobs with their own runners, matrices, environments (the checks pipeline).</details>

---

## Lab 4.3: Self-hosted runners (step 18)

> ⚠️ Do this in a **separate private repo**. Never attach a runner on your PC to the public
> `taskflow` repo: anyone could open a PR and run code on your machine.

**1. Create the scratch repo:**

```powershell
mkdir $HOME\runner-lab; cd $HOME\runner-lab
git init -b main
mkdir .github\workflows
copy $HOME\taskflow\course\snippets\4-3-runner-lab.yml .github\workflows\runner-lab.yml
git add -A; git commit -m "Runner lab"
gh repo create runner-lab --private --source=. --push
```

**2. Register your PC as a runner (persistent mode):** in `runner-lab` on GitHub:
**Settings → Actions → Runners → New self-hosted runner → Windows, x64**. Run the
**Download** commands it shows (into `C:\actions-runner`), then the **Configure** command,
accepting the defaults. Finally start it:

```powershell
cd C:\actions-runner
.\run.cmd
```

It prints "Listening for Jobs". It connects **out** to GitHub; no ports are opened.

**3. Run the lab twice:** in another PowerShell window:

```powershell
cd $HOME\runner-lab
gh workflow run runner-lab.yml; Start-Sleep 20; gh workflow run runner-lab.yml
```

🔍 **Observe** (Actions tab of `runner-lab`):
- Run 1: your PC's name, "No leftovers".
- Run 2: **"LEFTOVER FROM AN EARLIER JOB"**. The same machine runs job after job, so
  whatever one job leaves behind (a file, a process, a backdoor) is there for the next.
  Hosted runners never have this problem.

**4. Switch to ephemeral mode:** stop the runner (`Ctrl+C`). Copy the remove command from
**Settings → Actions → Runners → (your runner) → Remove** and run it in `C:\actions-runner`.
Then re-run the **Configure** command from step 2 with ` --ephemeral` added at the end, and `.\run.cmd`.
Trigger the workflow twice again.

🔍 **Observe:**
- The first job runs, and then the runner **exits and deregisters itself**.
- The second run stays **Queued**: no runner left. That's why real setups pair
  `--ephemeral` with an autoscaler (e.g. Actions Runner Controller on Kubernetes) that
  creates a **brand-new machine or container** for every job.
- The first job still found the leftover marker: `--ephemeral` removes the *registration*,
  not the files. Cleanliness comes from destroying and recreating the machine.

**5. Clean up:** cancel the queued run (`gh run cancel`), delete
`$env:TEMP\runner-lab-marker.txt`, and remove the runner from Settings if it's still listed.
Delete `C:\actions-runner` if you're done with it.

✅ **Checkpoint:** name two reasons to self-host and the main risk.
<details><summary>Answer</summary>Reasons: special hardware (GPU), private network access, local data, cost at scale. Risk: persistence. One compromised job can affect every later job, so use ephemeral, autoscaled runners separated by trust level, never on public repos.</details>

---

## Lab 4.4: Debugging, performance & cost (step 19)

Back in `taskflow`: `cd $HOME\taskflow`.

### A. Diagnose from the terminal only

Make any test fail on a branch, open a PR, then **without opening the browser**:

```powershell
gh pr checks                     # which checks failed
gh run list --limit 5            # find the run
gh run view --log-failed         # only the failing step's log
```

Re-run that run in the UI with **Re-run jobs → Enable debug logging** and compare the
log detail. Then close the PR.

### B. Measure the cache

1. Actions → **Caches** (left sidebar, under Management) shows each cache, its key, and its size.
   Or `gh cache list`.
2. Open a PR with an empty commit and note `checks / quick-checks` duration.
3. Delete all caches: `gh cache delete --all`. Push another empty commit.
4. Compare: the run without caches re-downloads everything (Set up Python and Type check
   take longer). That's the cache's whole value. It's a speed-up, never a requirement.

### C. The required-check trap (a real-world classic)

On a branch, add to `ci.yml` under `pull_request:`

```yaml
  pull_request:
    paths-ignore: ["**.md"]
```

Merge it, then open a PR that **only edits `README.md`**. CI doesn't run (filtered out), so
`checks / ci-passed` never reports, and the PR is **stuck** waiting forever. Lesson:
never put path filters on a workflow that provides a *required* check. (`release.yml`
uses `paths-ignore` safely, because it isn't a required check.) Revert the change.

### D. Cost

Public repo on standard runners means **free**. But imagine it were private:
1. Open a full Release run → **Summary**: note the job durations, including the 3 Windows
   test jobs from the full matrix.
2. Windows minutes cost more than Linux, macOS much more, and each job is rounded up to a
   whole minute. Which costs more per release: the Linux jobs or the Windows jobs?
3. Your actual usage: profile picture → **Settings → Billing and licensing → Usage**.

### E. Lint before you push

```powershell
pip install actionlint-py zizmor
actionlint
zizmor --min-severity medium .github
```

The same checks as the `workflow-lint` job, in seconds, before CI even starts.

---

## Lab 4.5: Capstone: release it and make it portfolio-ready (step 20)

**1. Finish the README.** Replace the `OWNER` placeholders with your username:

```powershell
git switch main; git pull; git switch -c lab-4-5
(Get-Content README.md) -replace 'OWNER', '<your-username>' | Set-Content README.md
```

Also fill in the two Render URLs in the "Live" section. Commit, PR, merge.

**2. Cut a release and polish the repo page:**

```powershell
gh release create v1.0.0 --generate-notes --title "Taskflow v1.0.0"
gh repo edit --description "To-do API with a production-grade GitHub Actions CI/CD pipeline" --homepage "https://<your-production-url>"
gh repo edit --add-topic github-actions --add-topic ci-cd --add-topic fastapi --add-topic devops --add-topic python
```

Then on your GitHub profile: **Customize your pins** → pin `taskflow`.

**3. Explain it like an interview.** Answer these aloud, without notes. They're the
questions a reviewer will ask about this repo:

1. Walk me through what happens from opening a PR to code running in production.
2. Why is there one required check instead of one per matrix job?
3. How do fork PRs get a coverage comment without exposing a write token to untrusted code?
4. Why does production deploy a digest and not `:latest`?
5. What stops a compromised third-party action from stealing your deploy hook?
6. If you moved to AWS, what would change in the deploy jobs, and what would the trust policy say?

**4. CV bullets** (adapt freely):

- Built a CI/CD pipeline in GitHub Actions for a FastAPI service: PR checks (ruff, strict
  mypy, pytest with coverage), a nightly cross-platform matrix (Linux/Windows, Python 3.12–3.14),
  and a single stable required status check gating merges.
- Implemented build-once deployments: immutable container images published to GHCR, auto-deployed
  to staging and promoted to production behind a manual approval gate, with automated smoke tests
  verifying the live version.
- Hardened the pipeline's supply chain: least-privilege `GITHUB_TOKEN` permissions, SHA-pinned
  actions kept current by Dependabot with a cooldown, workflow linting and security scanning
  (actionlint, zizmor), and a privilege-separated `workflow_run` design for safe fork-PR comments.
- Reduced duplication with a reusable workflow and composite actions; tuned cost and speed with
  caching, concurrency cancellation, and event-dependent matrices.

### Where each course step lives in your repo

| Step | Where to point a reviewer |
|---|---|
| 1–3 | `ci.yml` + `checks.yml`: triggers, jobs, steps |
| 4 | `runs-on: ubuntu-24.04` / `windows-2025` pins; `runner-lab` repo |
| 5, 17 | `.github/actions/*` composites; pinned `uses:` |
| 7 | `vars.PYTHON_VERSION`, `$GITHUB_OUTPUT`, job summaries |
| 8, 12 | Environment secrets `RENDER_DEPLOY_HOOK`; staging/production environments |
| 9 | `needs`, job outputs, `ci-passed` gate, concurrency groups |
| 10 | `test` matrix with `fromJSON(inputs.full-matrix …)` |
| 11 | Test-result artifacts; pip + mypy caches |
| 13 | `permissions:` on every workflow and job |
| 14 | OIDC lab (Lab 3.4) and the trust policy you wrote |
| 15 | SHA pins, `dependabot.yml`, `workflow-lint`, `coverage-comment.yml` |
| 16 | `checks.yml` called by `ci.yml`, `nightly.yml`, `release.yml` |
| 18 | `runner-lab` (private repo) |
| 19 | Timeouts, caching, concurrency, the paths-filter lesson |

## Where to go next

- **Real cloud + OIDC:** swap Render for AWS App Runner or Google Cloud Run, authenticating with
  OIDC instead of a deploy hook. The Lab 3.4 trust policy is your starting point.
- **Preview environments:** deploy each PR to its own temporary URL.
- **CodeQL:** GitHub's code scanning for the Python code *and* the workflows.
- **Automated releases:** release-please or semantic versioning from commit messages.
- **Self-repository syntax:** zizmor suggests GitHub's newer `$/…` form for local actions
  instead of `./…`. Read the changelog and decide if you want to adopt it.

**Course complete.** 🎉
