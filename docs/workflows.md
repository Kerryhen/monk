# CI/CD Workflows

Two GitHub Actions workflows handle automated quality checks and releases.

---

## CI — Lint on Pull Request

**File:** `.github/workflows/ci.yml`
**Trigger:** Any pull request targeting `main`

Runs `ruff check` against the API service to catch lint errors before merging.

```
PR → main
  └── lint job
        ├── actions/checkout@v4
        ├── actions/setup-python@v5 (Python 3.14)
        ├── pip install pdm
        ├── pdm install --dev
        └── pdm run task lint
```

If lint fails the PR is blocked. Fix errors locally with:

```bash
cd services/api
pdm run task format   # auto-fix formatting
pdm run task lint     # verify
```

---

## Release — Build and Publish

**File:** `.github/workflows/release.yml`
**Trigger:** Manual (`workflow_dispatch` from the Actions tab on `main`)

Reads the version from `services/api/pyproject.toml`, builds the Docker image, pushes it to GHCR, and creates a GitHub release with auto-generated notes.

```
workflow_dispatch (on main)
  └── release job
        ├── actions/checkout@v4
        ├── Read version from pyproject.toml → e.g. 0.1.0
        ├── docker/login-action@v3  → ghcr.io (GITHUB_TOKEN)
        ├── docker/build-push-action@v6
        │     context: services/api
        │     tags:
        │       ghcr.io/kerryhen/monk-api:0.1.0
        │       ghcr.io/kerryhen/monk-api:latest
        └── softprops/action-gh-release@v2
              tag: v0.1.0
              release notes: auto-generated from commits
```

### How to release

1. Bump the version in `services/api/pyproject.toml`:
   ```toml
   [project]
   version = "0.2.0"
   ```
2. Commit and merge to `main` via a PR (CI lint must pass).
3. On GitHub → **Actions** → **Release** → **Run workflow** → select `main` → **Run workflow**.
4. Verify:
   - Image appears at `ghcr.io/kerryhen/monk-api` under **Packages**
   - Release tag `v0.2.0` appears under **Releases**

---

## Git Flow

```
feature/*  ──PR──►  development  ──PR──►  main  ──workflow_dispatch──►  release
                                            ↑
                                      CI lint runs
```

| Branch | Purpose |
|--------|---------|
| `main` | Production-ready, versioned releases only |
| `development` | Integration branch — merge features here first |
| `feature/*` | Short-lived feature branches, PR into `development` |

---

## Testing Workflows Locally

Workflows can be run locally with [nektos/act](https://nektosact.com) and the Docker runner image configured in `.actrc`.

```bash
# Run the CI lint job (same environment as GitHub Actions)
act pull_request -j lint

# Dry-run to see what would execute without running containers
act pull_request --dry-run
```

`act` uses `catthehacker/ubuntu:act-latest` (set in `.actrc`) which matches the `ubuntu-latest` runner used in CI.

> The release workflow requires `GITHUB_TOKEN` with `packages: write` and `contents: write` scopes. These are automatically provided by GitHub Actions but are not available when running locally via `act` — run the release only from the GitHub Actions UI.
