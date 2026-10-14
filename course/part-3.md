# Part 3: Delivery & security

| Lab | Course step | Concept |
|---|---|---|
| 3.1 | 11 → 12 bridge | Build once: an immutable image in GHCR |
| 3.2 | 12. Environments & deployments | Staging auto-deploy, production with approval, smoke tests |
| 3.3 | 13. `GITHUB_TOKEN` & permissions | Least privilege, seeing a denied permission |
| 3.4 | 14. OIDC | Mint a real ID token and read its claims |
| 3.5 | 15. Supply-chain & injection security | SHA pinning, Dependabot, scanners, safe PR comments, a live injection |

You'll need a free [Render](https://render.com) account in Lab 3.2 (sign in with GitHub, no card).

---

## Lab 3.1: Build once, publish an image

**Goal:** every merge to `main` produces one immutable Docker image, identified by its digest.

```powershell
git switch main; git pull; git switch -c lab-3-1
copy course\snippets\3-1-release.yml .github\workflows\release.yml
git add -A; git commit -m "Lab 3.1: build and publish image"; git push -u origin HEAD
gh pr create --fill; gh pr checks --watch; gh pr merge --squash --delete-branch
git switch main; git pull
```

The merge is a push to `main`, so **Release** starts. Watch it: `gh run watch`.

🔍 **Observe:**
- Read `release.yml`: `permissions: {}` at the top, and only `build` gets `packages: write`.
- The run's **Summary** shows the image reference: `ghcr.io/<owner>/taskflow@sha256:…`.
  A tag like `:latest` can be moved; that digest can't. Deploys will use the digest.
- Your repo page now shows **Packages → taskflow** on the right.

**Make the image public** so Render can pull it without credentials:
`https://github.com/<owner>?tab=packages` → **taskflow** → **Package settings** →
**Change visibility** → **Public**.

(Optional, with Docker Desktop: `docker run -p 8000:8000 ghcr.io/<owner>/taskflow:latest`,
then <http://localhost:8000/health> shows the commit SHA as the version.)

---

## Lab 3.2: Environments & deployments (step 12)

**Goal:** merge → staging deploys automatically → you approve → production gets the
**same** image → smoke tests prove the right version is live.

**1. Create two Render services** (repeat for `taskflow-staging` and `taskflow-production`):
1. Render dashboard → **New → Web Service** → **Existing Image**.
2. Image URL: `ghcr.io/<owner>/taskflow:latest`, with `<owner>` in **lowercase** (GHCR names are lowercase) → **Connect**.
3. Name: `taskflow-staging` (then `taskflow-production`) · Region: Frankfurt (closest to Greece) · Instance type: **Free** → **Deploy**.
4. When it's live, open its URL (`https://taskflow-staging-xxxx.onrender.com`) and check `/health`.
5. **Settings → Deploy Hook** → copy the URL. It's a secret: anyone with it can deploy.

**2. Create the GitHub environments:** repo **Settings → Environments → New environment**.

| | `staging` | `production` |
|---|---|---|
| Deployment branches and tags | Selected → add rule `main` | Selected → add rule `main` |
| Required reviewers | — | ✅ yourself (leave "prevent self-review" **off**, since you're solo) |
| Environment secret `RENDER_DEPLOY_HOOK` | staging's hook URL | production's hook URL |
| Environment variable `APP_URL` | staging URL, no trailing `/` | production URL, no trailing `/` |

Same names, different values: each job gets the values of the environment it targets.

**3. Ship the deploy pipeline:**

```powershell
git switch -c lab-3-2
copy course\snippets\3-2-release.yml .github\workflows\release.yml
git add -A; git commit -m "Lab 3.2: staging and production deploys"; git push -u origin HEAD
gh pr create --fill; gh pr checks --watch; gh pr merge --squash --delete-branch
git switch main; git pull
```

🔍 **Observe** (Actions → Release):
1. `build` → `deploy-staging`: the smoke test polls `/health` until it reports **this
   commit's SHA**, then passes. A free Render service may take a minute to wake up.
2. `deploy-production` shows **Waiting**: "Review deployments" → tick production → **Approve and deploy**.
   While waiting, it uses no runner and no minutes.
3. Both jobs show **View deployment** links. The repo homepage now has a **Deployments**
   section with the history per environment.
4. Open both URLs: `/health` shows the same SHA in staging and production.

💥 **Break it: reject a release.** On a branch, change the `<h1>` in `app/static/index.html`
to `Taskflow 2`, then PR → merge. Staging updates (check the page), but **reject**
production in the review dialog. Production keeps serving the old version. Approve the
next release later.

✅ **Checkpoint:** why do both deploy jobs use `needs.build.outputs.image` instead of building again?
<details><summary>Answer</summary>Build once, deploy everywhere: production gets exactly the bits you saw on staging. A rebuild could pick up different dependency versions.</details>

---

## Lab 3.3: `GITHUB_TOKEN` & permissions (step 13)

**1. Set the safe default:** **Settings → Actions → General → Workflow permissions**
→ **Read repository contents and packages permissions** → Save. Workflows without a
`permissions:` block now get read-only tokens.

**2. See a denied permission:**

```powershell
git switch main; git pull; git switch -c lab-3-3
```

In `.github/workflows/release.yml`, delete the line `packages: write` from the `build` job.
Commit and push (no PR needed), then run it from your branch:
Actions → **Release** → **Run workflow** → branch `lab-3-3`.

🔍 **Observe:** the `docker push` fails with a permission-denied error: the token can
read code but not publish packages. You granted nothing, so the job could do nothing.
The deploy jobs are skipped because `build` failed. Even if `build` had passed, they would
have been rejected, because the environments only allow `main`.

Throw the branch away:

```powershell
git switch main; git branch -D lab-3-3; git push origin --delete lab-3-3
```

✅ **Checkpoint:** a job declares `permissions: pull-requests: write` and nothing else. Does `actions/checkout` still work?
<details><summary>Answer</summary>No. Once a permissions block exists, every unlisted scope becomes none, so contents is gone. Add `contents: read`.</details>

---

## Lab 3.4: OIDC (step 14)

**Goal:** see the identity token a cloud provider would receive, and how its `sub` claim changes.

```powershell
git switch main; git pull; git switch -c lab-3-4
copy course\snippets\3-4-oidc-lab.yml .github\workflows\oidc-lab.yml
git add -A; git commit -m "Lab 3.4: OIDC lab"; git push -u origin HEAD
gh pr create --fill; gh pr checks --watch; gh pr merge --squash --delete-branch
git switch main; git pull
```

Actions → **OIDC lab** → **Run workflow** (on `main`).

🔍 **Observe** the printed claims (the script never prints the token itself):

| Claim | `no-environment` job | `with-environment` job |
|---|---|---|
| `iss` | `https://token.actions.githubusercontent.com` | same |
| `aud` | `taskflow-lab` (requested in the URL) | same |
| `sub` | `repo:<owner>/taskflow:ref:refs/heads/main` | `repo:<owner>/taskflow:environment:staging` |
| `expires in` | a few minutes | a few minutes |

The token is signed by GitHub. A cloud provider checks the signature with GitHub's
public keys, then compares claims like `sub` against its trust policy.

✏️ **Exercise:** if this app deployed to AWS, write the trust-policy condition that
lets **only production deploy jobs** of this repo assume the production role.
<details><summary>Answer</summary>

```json
"Condition": {
  "StringEquals": {
    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
    "token.actions.githubusercontent.com:sub": "repo:<owner>/taskflow:environment:production"
  }
}
```

Combined with Lab 3.2's approval gate: GitHub enforces the human approval, and AWS
enforces that only approved jobs get credentials. With OIDC, there's no AWS key stored anywhere.
</details>

💥 **Break it:** on a branch, delete `id-token: write` from the `no-environment` job and run
the lab from that branch. It fails: there's no token-request URL without the permission.
The `with-environment` job is rejected outright: `staging` only allows `main`. Discard the branch.

---

## Lab 3.5: Supply-chain & injection security (step 15)

### A. Harden everything in one PR

```powershell
git switch main; git pull; git switch -c lab-3-5
copy course\snippets\3-5-ci.yml .github\workflows\ci.yml
copy course\snippets\3-5-release.yml .github\workflows\release.yml
copy course\snippets\3-5-coverage-comment.yml .github\workflows\coverage-comment.yml
copy course\snippets\3-5-dependabot.yml .github\dependabot.yml
git add -A; git commit -m "Lab 3.5: pin actions, scan workflows, safe PR comments"; git push -u origin HEAD
gh pr create --fill
```

Read the diff on the PR, which shows what changed and why:
- Every `uses:` is now a **full commit SHA** with a `# vX.Y.Z` comment.
- `permissions: contents: read` at the top of CI; `persist-credentials: false` on every checkout.
- A new `workflow-lint` job runs **actionlint** (correctness) and **zizmor** (security) on your workflows.
- CI uploads coverage data; `coverage-comment.yml` posts it to the PR from a separate,
  privileged workflow that never runs PR code.

**Verify a pin yourself:**

```powershell
git ls-remote --tags https://github.com/actions/checkout v7.0.1
```

The commit SHA printed (on the `^{}` line, if there is one) must match the one in `ci.yml`.

Merge when green.

### B. Watch a script injection happen (then get caught)

In PowerShell, **single quotes** keep `$(...)` literal:

```powershell
git switch main; git pull
git switch -c 'demo-$(whoami)'
copy course\snippets\3-5-injection-lab.yml .github\workflows\injection-lab.yml
git add -A; git commit -m "Injection lab"; git push -u origin HEAD
gh pr create --fill
```

🔍 **Observe:**
- **Injection lab → VULNERABLE step** prints `Branch is demo-runner`. The branch name was
  pasted into the script, and `$(whoami)` **executed on the runner**. An attacker would
  use `$(curl … | bash)`.
- **SAFE step** prints the literal `Branch is demo-$(whoami)`: through `env:`, it's just data.
- **CI → workflow-lint** fails: actionlint flags `github.head_ref` as untrusted input, and
  zizmor reports `template-injection`. The scanners would have blocked this file from ever merging.

Clean up:

```powershell
gh pr close --delete-branch
git switch main; git branch -D 'demo-$(whoami)'
```

### C. See the safe PR comment

Open any small PR (for example, fix a typo in `README.md`). When CI passes, a **Coverage
comment** run starts (Actions tab, triggered by `workflow_run`) and posts the coverage
percentage on your PR. Read `coverage-comment.yml` once more and note what it does *not*
do: no checkout, no running PR code. It validates the artifact's contents and checks
the PR's head SHA against the CI run before commenting.

### D. Repository security settings

**Settings → Actions → General:**
- **Approval for running fork pull request workflows from contributors** →
  *Require approval for all external contributors*.
- **Actions permissions** → *Allow \<owner\>, and select non-\<owner\>, actions and reusable
  workflows* → tick *Allow actions created by GitHub*. Your workflows only use `actions/*`.
  If your GitHub shows an option to *require actions to be pinned to a full-length commit SHA*, tick it.

Over the next weeks, **Dependabot** will open PRs that bump the pinned SHAs (after the
7-day cooldown). Each one runs through your full CI, like any other change.

✅ **Checkpoint:** why does `coverage-comment.yml` get a write token while CI doesn't, and why is that safe?
<details><summary>Answer</summary>A job may run untrusted code or hold write access, never both. CI runs PR code with a read-only token and no secrets; the comment workflow has write access but only reads validated data and never executes PR code.</details>

**Part 3 done.** You have real deployments with an approval gate, least-privilege
tokens, pinned actions, automated updates, and workflow security scanning.

Next: [Part 4: Reuse & scale](part-4.md)
