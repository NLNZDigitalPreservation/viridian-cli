# Viridian CLI

`viridian-cli` is a Python command-line toolkit for managing the local Viridian service stack. Each service is exposed as its own CLI entry point, with shared lifecycle commands for installation, container control, and status checking.

Requirements: Python 3.12 or newer.

---

## Command overview

The project installs these console entry points:

- `fixity`
- `dashboard`
- `proxy`
- `azurite`
- `oracle`
- `postgres`

Each entry point uses the same application logic and chooses its behaviour from the executable name.

### Common commands

All service entry points support the following commands:

```bash
<app> install
<app> info
<app> up
<app> down
<app> restart
<app> status
<app> logs
<app> exec
```

Examples:

```bash
dashboard install
dashboard up
dashboard logs
dashboard down

proxy install
proxy status

oracle install
oracle up
oracle logs
```

The `install` command copies the packaged compose files and environment templates into a service-specific directory, and the `info` command prints the stored installation paths for that app.

---

## Default installation paths

The CLI uses these defaults:

- install root: `/data/viridian/conf`
- persistent data root: `/data/viridian/persistent`

Each app is installed under its own subdirectory:

```bash
/data/viridian/conf/fixity
/data/viridian/conf/dashboard
/data/viridian/conf/proxy
/data/viridian/conf/azurite
/data/viridian/conf/oracle
/data/viridian/conf/postgres
```

Likewise, persistent storage is stored under:

```bash
/data/viridian/persistent/fixity
/data/viridian/persistent/dashboard
/data/viridian/persistent/proxy
/data/viridian/persistent/azurite
/data/viridian/persistent/oracle
/data/viridian/persistent/postgres
```

These paths are resolved in the code by app name, so the default directory is app-scoped rather than a single shared service path.

---

## Installation

On Ubuntu 24.04+, if the venv environment is required, then install from GitHub with `pipx`:

```bash
pipx install git+https://github.com/NLNZDigitalPreservation/viridian-cli.git
```

RHEL, if the venv envrionment is not mandatory, then install from Github with "pip":

```bash
pip3.12 install https://github.com/NLNZDigitalPreservation/viridian-cli/archive/refs/heads/main.zip --force-reinstall
```

Or install from a local checkout:

```bash
python -m pip install .
```

### Install the commands globally on Ubuntu 24.04+ (Development)

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

---

## Service-specific usage

### `fixity`

```bash
fixity install
fixity info
fixity up
fixity logs
fixity down
fixity exec
```

### `dashboard`

```bash
dashboard install
dashboard up
dashboard logs
dashboard down
```

### `proxy`

```bash
proxy install
proxy up
proxy logs
proxy down
```

### `azurite`

```bash
azurite install
azurite up
azurite logs
azurite down
```

### `oracle`

```bash
oracle install
oracle up
oracle logs
oracle down
```

### `postgres`

```bash
postgres install
postgres up
postgres logs
postgres down
```

---

## Container engine selection

The CLI accepts a container engine choice:

```bash
--container-engine auto
--container-engine podman
--container-engine docker
```

If set to `auto`, it prefers `podman` if available and otherwise falls back to `docker`.

---

## Configuration and environment files

Each install creates:

- a service-specific install directory under `/data/viridian/conf/<app>`
- a corresponding persistent storage root under `/data/viridian/persistent/<app>`
- a `.env` file generated from the bundled template, if present
- a saved config entry in the user config directory under `~/.config/viridian/config.json`

This allows the CLI to remember the install path and data path for each application without requiring the user to pass it repeatedly.

---

## `pyaz`

`pyaz` is the Azure Blob Storage helper and remains a separate CLI entry point.

```bash
python -m pyaz.cli <command> [options]
```

Typical usage includes container creation, listing, uploading, and metadata import workflows for Azurite-compatible storage.

---

## Notes

- The legacy `simulator` command is no longer part of the package.
- The stack is now grouped by app-specific entry points: `dashboard`, `proxy`, `azurite`, `oracle`, and `postgres`.
- The default install locations are no longer a single shared path for all services; they are app-scoped under `/data/viridian/conf` and `/data/viridian/persistent`.
