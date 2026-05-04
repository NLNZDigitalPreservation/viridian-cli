# fixity-cli

`fixity-cli` is the Python command-line package for Viridian local operations.
It wraps the shell workflows currently represented by `cli_dev` and `cli_fixity`
and bundles the compose files and database scripts required for those workflows.

## What the CLI provides

Two console entrypoints are installed:

- **`simulator`** — manages the Azurite and Oracle simulator stack:
  - `init`
  - `up`
  - `down`
  - `logs`
- **`fixity`** — manages the fixity master node, plus installation:
  - `install`
  - `info`
  - `init`
  - `up`
  - `down`
  - `logs`
  - `exec`
  - `build`
  - `push`
- Packaged runtime assets:
  - `docker-compose-dev.yml`
  - `docker-compose-fixity.yml`
  - `db/oracle/*`
  - `db/postgres/*`

## Install

From the `cli_tools/` directory:

```bash
python3 -m pip install .
```

After installation the two console entrypoints are available:

```bash
fixity --help
simulator --help
```

## Setup

Install the fixity master stack to the installation directory (default
`/usr/local/fixity`):

```bash
fixity install
```

This command:

1. Pulls the `acrdiaanlnznsbx.azurecr.io/fixity-master` Docker image.
2. Extracts `docker-compose-dev.yml`, `docker-compose-fixity.yml`, and `db/`
   from the image (sourced from `/opt/fixity/` inside the image).
3. Creates a `.env` file in the installation directory from the bundled
   template if one does not already exist.

Edit the `.env` file in the installation directory before starting any
services.

Show the resolved installation path and the state of all managed directories:

```bash
fixity info
```

## Usage

### Simulators

Initialise local simulator storage:

```bash
simulator init
```

Start Azurite and Oracle:

```bash
simulator up
```

Stop the simulator stack:

```bash
simulator down
```

Follow simulator logs:

```bash
simulator logs
```

### Fixity master node

Initialise persistent storage used by the master stack:

```bash
fixity init
```

Start the master stack:

```bash
fixity up
```

Stop the master stack:

```bash
fixity down
```

Follow master logs:

```bash
fixity logs
```

Open a shell in the running `fixity_master` container:

```bash
fixity exec
```

Build the master image from the Viridian repository checkout:

```bash
fixity build
```

Push the tagged image to Azure Container Registry:

```bash
fixity push
```

## Notes

- `simulator` uses the `docker-compose-dev.yml` extracted at install time. No `.env` file is required.
- `fixity` uses the `docker-compose-fixity.yml` extracted at install time and reads `.env` from the installation directory.
- `fixity install` requires Docker (or Podman) to pull and extract the image. Re-run it after an image upgrade to refresh the compose files and `db/`.
- `fixity build` requires a Viridian repository checkout. Use `--project-root <path>` if running from outside the repo root (default: `.`).
- The image version and registry are read from the installed `docker-compose-fixity.yml`; no flags are needed for `build` or `push`.

## Build a distribution

The package no longer bundles compose files or database scripts — those are
extracted from the Docker image at install time. Building a distribution only
requires the source tree and standard tooling.

Install build tooling:

```bash
python3 -m pip install --upgrade build twine
```

Build source and wheel distributions from the `cli_tools/` directory:

```bash
python3 -m build
```

Artifacts are written to `dist/`.

## Publish to Azure Artifacts PyPI

Use an Azure DevOps feed endpoint in the form:

```text
https://pkgs.dev.azure.com/<organization>/<project>/_packaging/<feed>/pypi/upload/
```

Create a Personal Access Token with package read/write permissions, then export credentials:

```bash
export TWINE_USERNAME=<azure-devops-username>
export TWINE_PASSWORD=<personal-access-token>
```

Upload the package:

```bash
python3 -m twine upload \
	--repository-url https://pkgs.dev.azure.com/<organization>/<project>/_packaging/<feed>/pypi/upload/ \
	dist/*
```

## Install from Azure Artifacts

Use the feed simple index URL:

```text
https://pkgs.dev.azure.com/<organization>/<project>/_packaging/<feed>/pypi/simple/
```

Example install:

```bash
python3 -m pip install \
	--index-url https://pkgs.dev.azure.com/<organization>/<project>/_packaging/<feed>/pypi/simple/ \
	--extra-index-url https://pypi.org/simple \
	fixity-cli
```
