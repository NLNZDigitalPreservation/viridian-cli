# fixity-cli

`fixity-cli` is the Python command-line package for Viridian local operations.
It supports Python 3.9 and newer.

## What the CLI provides

Two console entrypoints are installed:

- **`simulator`** — manages the Azurite and Oracle simulator stack:
  - `up`
  - `down`
  - `logs`
- **`fixity`** — manages the fixity master node, plus installation:
  - `install`
  - `info`
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

Print the installed package version:

```bash
fixity --version
simulator --version
```

## Setup

Install the fixity master stack to the installation directory (default
`/usr/local/fixity`):

```bash
fixity install
```

This command:

1. Prompts for an installation directory (default `/usr/local/fixity`).
2. Copies `docker-compose-dev.yml`, `docker-compose-fixity.yml`, and `db/`
   from the bundled package resources.
3. Creates a `.env` file in the installation directory from the bundled
   template if one does not already exist.
4. Initialises fixity master persistent storage directories automatically.
5. Prompts whether to enable the simulator — if yes, initialises simulator
   persistent storage directories as well.

Use `--yes` / `-y` to accept all defaults and skip prompts (simulator is not
enabled in non-interactive mode):

```bash
fixity install --yes
```

Edit the `.env` file in the installation directory before starting any
services.

Show the resolved installation path and the state of all managed directories:

```bash
fixity info
```

## Usage

### Simulators

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

### Azure Blob Storage Management (pyaz)

The `pyaz` module provides commands for managing Azure Blob Storage operations, including uploading files, managing containers, and persisting metadata to the Rosetta database.

#### Commands

The command syntax is:

```bash
python -m pyaz.cli <command> [options]
```

Available commands:

| Command | Description                                       |
| ------- | ------------------------------------------------- |
| `cc`    | Create a container                                |
| `dc`    | Delete a container                                |
| `lc`    | List all containers                               |
| `lb`    | List blobs in a container                         |
| `id`    | Import a directory (recursively upload all files) |
| `if`    | Import a single file                              |
| `db`    | Delete a blob                                     |

#### Common Options

```
--connection-string <str>
    Azure Storage connection string (default: Azurite local emulator)
    Environment variable: CONNECTION_STRING

--container-name <str>
    Name of the blob storage container (default: fixity-dev)
    Environment variable: CONTAINER_NAME

--rosetta-db-hostname <str>
    Database hostname (default: localhost)
    Environment variable: ROSETTA_DB_HOSTNAME

--rosetta-db-port <int>
    Database port (default: 1521)
    Environment variable: ROSETTA_DB_PORT

--rosetta-db-username <str>
    Database username (default: system)
    Environment variable: ROSETTA_DB_USERNAME

--rosetta-db-password <str>
    Database password (default: Pass123Word)
    Environment variable: ROSETTA_DB_PASSWORD

--rosetta-db-sid <str>
    Database SID
    Environment variable: ROSETTA_DB_SID

--rosetta-db-service-name <str>
    Database service name (default: FREEPDB1)
    Environment variable: ROSETTA_DB_SERVICE_NAME

--rosetta-db-schemaprefix <str>
    Schema prefix for database tables (default: V2PN)
    Environment variable: ROSETTA_DB_SCHEMAPREFIX
```

#### Behavior Flags

```
--flag-upload-blob-storage true|false
    Whether to upload blobs to Azure Storage (default: true)

--flag-save-to-db true|false
    Whether to save blob metadata to the Rosetta database (default: true)

--flag-generate-sql true|false
    Whether to generate and print SQL INSERT statements (default: true)
```

#### Examples

##### List containers

```bash
python -m pyaz.cli lc
```

##### Create a container

```bash
python -m pyaz.cli cc --container-name my-container
```

##### Import a directory

```bash
python -m pyaz.cli id \
  --container-name fixity-dev \
  --prefix-directory /path/to/data \
  --source-directory /path/to/data
```

This command:

1. Recursively uploads all files from `--source-directory` to the container
2. Extracts storage entity type and ID from filenames (defaults to FILE type, or IE for `ie.xml`)
3. Computes MD5 checksum for each file
4. Saves file size and metadata to the Rosetta database (PERMANENT_INDEX table)
5. Generates INSERT SQL statements if `--flag-generate-sql` is true

##### Import a single file

```bash
python -m pyaz.cli if \
  --container-name fixity-dev \
  --source-file /path/to/file.bin \
  --prefix-directory /path/to
```

##### List blobs in a container

```bash
python -m pyaz.cli lb --container-name fixity-dev
```

##### Delete a blob

```bash
python -m pyaz.cli db \
  --container-name fixity-dev \
  --blob-name path/to/blob.bin
```

#### Generated SQL

When `--flag-generate-sql true` is set, the module prints fully-rendered SQL INSERT statements to stdout. Redirect to a file for auditing or manual execution:

```bash
python -m pyaz.cli id \
  --prefix-directory /path/to/data \
  --source-directory /path/to/data \
  --flag-generate-sql true > /tmp/audit.sql
```

The SQL includes:

- Blob metadata (file size, MD5 checksum, storage entity type)
- Storage parameters (directory root mapping)
- All values as literals (no bind parameters)

## Notes

- `simulator` uses the `docker-compose-dev.yml` extracted at install time. No `.env` file is required.
- `fixity` uses the `docker-compose-fixity.yml` extracted at install time and reads `.env` from the installation directory.
- `fixity install` copies compose files and database scripts from the bundled package resources. Re-run it after a package upgrade to refresh the compose files and `db/`.
- `fixity install` always initialises fixity master persistent storage. It prompts once whether to also initialise simulator storage; use `--yes` to skip all prompts (simulator will not be initialised).
- `fixity install` will generated the key and certificate for access to the Azure Functions. The generated files will be stored in /persistent/fixity.
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
