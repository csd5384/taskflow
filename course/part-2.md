# Part 2: Data & control flow

| Lab | Course step | Concept |
|---|---|---|
| 2.1 | 7. Contexts, expressions & variables | `${{ }}`, `vars`, `$GITHUB_OUTPUT`/`$GITHUB_ENV`, summaries |
| 2.2 | 8. Secrets | Storage, masking and its limits, skipping when missing |
| 2.3 | 9. Job orchestration | Job outputs, `if:`, `failure()`, concurrency |
| 2.4 | 10. Matrix builds | Matrix, `fromJSON`, `fail-fast`, the gate job |
| 2.5 | 11. Artifacts vs caching | Test reports you can download; cache hits and misses |

Every lab uses the [PR loop](README.md#recipe-the-pr-loop-from-lab-16-on).

---

## Lab 2.1: Contexts, expressions & variables (step 7)

```powershell
git switch main; git pull; git switch -c lab-2-1
copy course\snippets\2-1-ci.yml .github\workflows\ci.yml
git add -A; git commit -m "Lab 2.1: contexts and variables"; git push -u origin HEAD
gh pr create --fill
```

Read the new `ci.yml`: every new line has a comment.

🔍 **Observe** (open the run from the PR):
- **Dump contexts**: expand the `github context` group. That's everything GitHub knows
  about this run: event, ref, SHA, and the whole PR payload under `event`.
- The **Summary** page of the run shows your Markdown table: event, short SHA, build
  date (set in one step via `$GITHUB_ENV`, read in a later one), Python version.
- Lint failing no longer skips Type check and Test (`if: success() || failure()`).

**Change config without a commit:**

```powershell
gh variable set PYTHON_VERSION --body 3.13
```

Then on the PR: **Checks** tab → **Re-run all jobs**. The new run's summary says
Python 3.13, with no file changed. Merge the PR.

✅ **Checkpoint:** why does the dump step pass `toJSON(github)` through `env:` instead of writing `${{ toJSON(github) }}` directly in `run:`?
<details><summary>Answer</summary>`${{ }}` is pasted into the script before the shell runs. The github context contains attacker-controllable text (PR titles, branch names), so splicing it into a script is script injection. Through env it's just data.</details>

---

## Lab 2.2: Secrets (step 8)

**1. Create a FAKE secret** (this lab shows how masking can be bypassed, so never use a real one):

```powershell
gh secret set DEMO_SECRET
```

When prompted, paste `not-a-real-secret-123` and press Enter.
#### stopped here
**2. Add the lab workflow** (it needs to be on `main` for the Run button):

```powershell
git switch main; git pull; git switch -c lab-2-2
copy course\snippets\2-2-secrets-lab.yml .github\workflows\secrets-lab.yml
git add -A; git commit -m "Lab 2.2: secrets lab"; git push -u origin HEAD
gh pr create --fill; gh pr checks --watch; gh pr merge --squash --delete-branch
git switch main; git pull
```

Actions → **Secrets lab** → **Run workflow**.

🔍 **Observe:**
- `Direct value: ***`: the exact string is masked.
- `Base64:` and `Reversed:` print readable transformations: **masking only matches
  the exact string.** Decode the base64 yourself if you like.
- The last step prints `<not set>`: a secret only exists where you map it in.
- Go to **Settings → Secrets and variables → Actions** and click the secret: you can
  update or remove it, but never view it. Secrets are write-only.

💥 **Break it:** delete the secret and run the lab again:

```powershell
gh secret delete DEMO_SECRET
```

The workflow doesn't fail: it shows a warning annotation and skips the secret steps.
That's the pattern for jobs that must survive fork PRs, where secrets are always empty.

✅ **Checkpoint:** why are secrets withheld from PRs opened from forks?
<details><summary>Answer</summary>For PR events, the workflow file comes from the PR's own commit, so a stranger could edit it to print or send your secrets just by opening a PR.</details>

Leave `secrets-lab.yml` for now; you'll clean up the labs in Lab 4.2.

---

## Lab 2.3: Job orchestration (step 9)

```powershell
git switch main; git pull; git switch -c lab-2-3
copy course\snippets\2-3-ci.yml .github\workflows\ci.yml
git add -A; git commit -m "Lab 2.3: job orchestration"; git push -u origin HEAD
gh pr create --fill
```

⚠️ The PR will wait forever on the required check `checks`, because that job no
longer exists. Do the [required-check swap](README.md#recipe-swapping-a-required-check):
replace `checks` with **`quick-checks`** and **`test`**.

🔍 **Observe:**
- The graph: `quick-checks` → `test` → `report`. `notify-failure` shows as **skipped**:
  its `if: failure()` was false.
- The **Summary** table was written by `report`, using `quick-checks`'s **job output**
  (the short SHA) and the `needs.<job>.result` values.

💥 **Break it: concurrency.** Push two commits quickly:

```powershell
git commit --allow-empty -m "first"; git push
git commit --allow-empty -m "second"; git push
```

In the Actions tab, the run for "first" shows **Cancelled**: same concurrency group
(`ci-refs/pull/<n>/merge`), and `cancel-in-progress: true`.

💥 **Break it: failure handling.** Add `import os` at the top of `app/store.py`, commit, push.
`quick-checks` fails → `test` is **skipped** (needs failed) → `notify-failure` **runs**
→ `report` still runs (`always()`) and shows the results table. Remove the import, push again, merge.

✅ **Checkpoint:** `deploy` is skipped on PRs, and `report` has `needs: [deploy]` with no `if:`. What happens to `report`?
<details><summary>Answer</summary>It's skipped too: by default a job needs all its dependencies to succeed, and skipped isn't success. Fix with `if: ${{ !cancelled() && ... }}`.</details>

---

## Lab 2.4: Matrix builds (step 10)

```powershell
git switch main; git pull; git switch -c lab-2-4
copy course\snippets\2-4-ci.yml .github\workflows\ci.yml
git add -A; git commit -m "Lab 2.4: matrix and gate"; git push -u origin HEAD
gh pr create --fill
```

Swap the required checks again: replace `quick-checks` and `test` with **`ci-passed`**.
From now on, that one name stays stable however the matrix changes.

🔍 **Observe:**
- On the PR: **3** test jobs (Linux × Python 3.12/3.13/3.14). The `fromJSON(...)`
  expression picked the small matrix because `event_name == 'pull_request'`.
- Merge, then open the **push** run on `main`: **6** test jobs (Linux + Windows).
- `ci-passed` runs last, even on failure (`always()`), and fails unless everything succeeded.

💥 **Break it: platform-specific failure.** On a new branch, edit `tests/test_store.py`:
add `import sys` as the **first line** followed by an empty line, and this test at the **bottom**:

```python
def test_only_on_linux() -> None:
    assert sys.platform == "linux"
```

Commit, push, open a PR.

The PR is green (Linux only). Now run the workflow on that branch with the full matrix:
Actions → **CI** → **Run workflow** → pick your branch. Windows jobs fail, and because
`fail-fast: false`, the Linux jobs still finish, so you see exactly which combinations break.
Delete the test and close the PR (`gh pr close --delete-branch`).

✅ **Checkpoint:** why does `ci-passed` use `if: always()` rather than `if: !cancelled()`?
<details><summary>Answer</summary>A skipped required check counts as passing. If the gate could be skipped, unverified code could merge. With always() it runs and fails explicitly.</details>

---

## Lab 2.5: Artifacts vs caching (step 11)

```powershell
git switch main; git pull; git switch -c lab-2-5
copy course\snippets\2-5-ci.yml .github\workflows\ci.yml
git add -A; git commit -m "Lab 2.5: artifacts and caching"; git push -u origin HEAD
gh pr create --fill; gh pr checks --watch
```

🔍 **Observe (cache):**
- In `quick-checks` → **Restore mypy cache**: the first run says no cache was found.
  The **Post Restore mypy cache** step at the end saves it.
- Push an empty commit (`git commit --allow-empty -m "cache test"; git push`).
  Now it says the cache was **restored**, and **Type check** is faster.
- **Set up Python** shows the same for pip downloads.

🔍 **Observe (artifacts):** the run's **Summary** page lists `test-results-…` artifacts,
one per matrix combination. Download one and open the coverage report:

```powershell
gh run download --name test-results-ubuntu-24.04-py3.13 --dir $env:TEMP\coverage
start $env:TEMP\coverage\htmlcov\index.html
```

(`gh run download` asks which run to use: pick the latest CI run. Or click the artifact on the Summary page.)

💥 **Break it:** the test upload step has `if: always()`. Make a test fail, push, and
download the artifact from the failed run: `junit.xml` records exactly which test failed.
That's why reports are uploaded even (especially) when tests fail. Revert, then merge.

✅ **Checkpoint:** why is the coverage report an artifact and the mypy data a cache?
<details><summary>Answer</summary>If the coverage report vanished you'd lose a result: wrong. If the mypy cache vanished, mypy just runs slower. Wrong means artifact, slower means cache.</details>

**Part 2 done.** Your CI has stages, a matrix, one stable gate check, downloadable reports, and caching.

Next: [Part 3: Delivery & security](part-3.md)
