#!/usr/bin/env bash
set -euo pipefail

REPOSITORY_URL="https://pkgs.dev.azure.com/NationalLibrary/e8df8b90-a684-46f0-a3aa-a7e7a9a03755/_packaging/fixity-cli/pypi/upload/"

# Use PAT-based auth and bypass keyring/browser flows in headless shells.
export PYTHON_KEYRING_BACKEND="keyring.backends.null.Keyring"

if [[ -z "${TWINE_USERNAME:-}" ]]; then
	echo "TWINE_USERNAME is required (Azure DevOps username or any non-empty value)." >&2
	exit 1
fi

if [[ -z "${TWINE_PASSWORD:-}" ]]; then
	echo "TWINE_PASSWORD is required (Azure DevOps PAT with Packaging Read & write)." >&2
	exit 1
fi

if ! ls dist/* >/dev/null 2>&1; then
	echo "No distribution files found under dist/. Run: python3 -m build" >&2
	exit 1
fi

echo "Uploading distributions to ${REPOSITORY_URL}"
python3 -m twine upload \
	--non-interactive \
	--username "${TWINE_USERNAME}" \
	--password "${TWINE_PASSWORD}" \
	--repository-url "${REPOSITORY_URL}" \
	dist/*
    
