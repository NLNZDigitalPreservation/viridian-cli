# fixity-cli

`fixity-cli` is a Python-based command-line interface for Viridian local operations. It streamlines the management of the Viridian stack, simulator environments, and Azure Blob Storage integrations.

**Requirements:** Python 3.9 or newer.

---

## Overview

The package installs two primary console entry points:

### 1. `simulator`

Manages the Azurite (Storage) and Oracle (Database) simulator stack.

- **Commands:** `up`, `down`, `logs`

### 2. `fixity`

Manages the Fixity master node and installation lifecycle.

- **Commands:** `install`, `info`, `up`, `down`, `logs`, `exec`, `build`, `push`

### Packaged Assets

The CLI bundles the following runtime assets:

- `docker-compose-dev.yml`
- `docker-compose-fixity.yml`
- Database scripts: `db/oracle/*` and `db/postgres/*`

---

## Installation

### Ubuntu 24.04+ (Development)

The following steps install Git and `pipx`, then perform a clean global installation of the CLI:

```bash
# Update system and install base dependencies
sudo apt update && sudo apt install -y git pipx

# Ensure pipx is properly configured globally
sudo pipx install pipx --force
sudo pipx ensurepath

# Clean up local pipx remnants and reinstall globally
sudo apt purge --autoremove pipx
sudo -i pipx install --global --force pipx
sudo -i rm -rf ~/.local/share/pipx ~/.local/bin/pipx ~/.local/pipx ~/.cache/pipx ~/.config/pipx

# Refresh shell hash
hash -r
sudo -i hash -r

# Install the CLI directly from GitHub
sudo pipx install --global --force git+https://github.com/NLNZDigitalPreservation/viridian-cli.git
```

### RHEL

For RHEL environments using Python 3.12:

```bash
sudo pip3.12 install https://github.com/NLNZDigitalPreservation/viridian-cli/archive/refs/heads/main.zip --force-reinstall
```

---

## Setup & Configuration

### Initial Installation

To install the Fixity master stack to the default directory (`/usr/local/fixity`):

```bash
fixity install
```

**The installation process performs the following:**

1.  **Path Selection:** Prompts for an installation directory.
2.  **Asset Deployment:** Copies bundled Compose files and DB scripts.
3.  **Environment Setup:** Creates a `.env` file from a template (if not already present).
4.  **Storage Initialization:** Creates persistent storage directories for Fixity.
5.  **Simulator Setup:** Optionally initializes simulator storage directories.

**Non-Interactive Install:**
Use the `--yes` flag to accept all defaults (Note: the simulator is **not** enabled in this mode).

```bash
fixity install --yes
```

> [!IMPORTANT]
> Edit the `.env` file in your installation directory before starting services for the first time.

### View Installation Status

To see the resolved installation path and the state of managed directories:

```bash
fixity info
```

---

## Usage Guide

### Managing Simulators

Start/stop the Azurite and Oracle stack:

```bash
simulator up       # Start stack
simulator logs     # Follow logs
simulator down     # Stop stack
```

### Managing the Fixity Master Node

Commands for the primary Fixity service:

```bash
fixity up          # Start master stack
fixity logs        # Follow logs
fixity exec        # Open a shell inside the running master container
fixity down        # Stop master stack
```

### Development Commands

- **Build:** Create the master image from a Viridian repository checkout.
  ```bash
  fixity build --project-root /path/to/repo
  ```
- **Push:** Push the tagged image to the Azure Container Registry defined in the compose file.
  ```bash
  fixity push
  ```

---

## Azure Blob Storage Management (`pyaz`)

The `pyaz` module handles Azure Blob Storage operations and Rosetta database metadata persistence.

### Command Syntax

```bash
python -m pyaz.cli <command> [options]
```

### Available Commands

| Command | Description                                                  |
| :------ | :----------------------------------------------------------- |
| `cc`    | **Create** a container                                       |
| `dc`    | **Delete** a container                                       |
| `lc`    | **List** all containers                                      |
| `lb`    | **List** blobs within a container                            |
| `id`    | **Import Directory**: Recursively upload files and update DB |
| `if`    | **Import File**: Upload a single file and update DB          |
| `db`    | **Delete** a specific blob                                   |

### Configuration Options

These can be passed as flags or set as environment variables:

| Option                      | Env Variable              | Default         |
| :-------------------------- | :------------------------ | :-------------- |
| `--connection-string`       | `CONNECTION_STRING`       | (Azurite Local) |
| `--container-name`          | `CONTAINER_NAME`          | `fixity-dev`    |
| `--rosetta-db-hostname`     | `ROSETTA_DB_HOSTNAME`     | `localhost`     |
| `--rosetta-db-username`     | `ROSETTA_DB_USERNAME`     | `system`        |
| `--rosetta-db-service-name` | `ROSETTA_DB_SERVICE_NAME` | `FREEPDB1`      |

### Behavior Flags

Toggle specific actions during import:

- `--flag-upload-blob-storage`: Upload to Azure (Default: `true`)
- `--flag-save-to-db`: Persist metadata to Rosetta (Default: `true`)
- `--flag-generate-sql`: Print SQL INSERT statements to stdout (Default: `true`)

### Example: Importing a Directory

```bash
python -m pyaz.cli id \
  --container-name fixity-dev \
  --prefix-directory /path/to/data \
  --source-directory /path/to/data \
  --flag-generate-sql true > audit.sql
```

This command uploads the files, calculates MD5 checksums, updates the `PERMANENT_INDEX` table, and logs the SQL for auditing.

---

## Operational Notes

- **Resources:** `fixity install` extracts resources from the package. Re-run this command after upgrading the `fixity-cli` package to ensure your Compose files and DB scripts are up to date.
- **Security:** `fixity install` automatically generates the key and certificate required for Azure Functions access, stored in `/persistent/fixity`.
- **Context:** `fixity build` defaults to the current directory (`.`) for the repository root unless `--project-root` is specified.
- **Configuration:** The image version and registry settings are read directly from the installed `docker-compose-fixity.yml`.

---

## Distribution & Publishing

### Build a Distribution

To package the CLI for distribution:

1.  **Install tools:** `python3 -m pip install --upgrade build twine`
2.  **Build:** Run `python3 -m build` from the `cli_tools/` directory.
3.  **Output:** Artifacts will be located in `dist/`.

### Publish to Azure Artifacts

1.  **Set Credentials:**
    ```bash
    export TWINE_USERNAME=<azure-devops-username>
    export TWINE_PASSWORD=<personal-access-token>
    ```
2.  **Upload:**
    ```bash
    python3 -m twine upload \
      --repository-url https://pkgs.dev.azure.com/<org>/<project>/_packaging/<feed>/pypi/upload/ \
      dist/*
    ```

### Install from Azure Artifacts

```bash
python3 -m pip install \
  --index-url https://pkgs.dev.azure.com/<org>/<project>/_packaging/<feed>/pypi/simple/ \
  --extra-index-url https://pypi.org/simple \
  fixity-cli
```
