#!/usr/bin/env bash
set -euo pipefail

REPOSITORY_URL="https://pkgs.dev.azure.com/NationalLibrary/e8df8b90-a684-46f0-a3aa-a7e7a9a03755/_packaging/fixity-cli/pypi/simple/"
EXTRA_INDEX_URL="https://pypi.org/simple"
PACKAGE_SPEC="${FIXITY_CLI_SPEC:-fixity-cli}"

source .venv/bin/activate
python3 -m pip install -q artifacts-keyring keyring

echo "Installing ${PACKAGE_SPEC} from ${REPOSITORY_URL}"
if python3 -m pip install \
  --index-url "${REPOSITORY_URL}" \
  --extra-index-url "${EXTRA_INDEX_URL}" \
  "${PACKAGE_SPEC}"; then
  exit 0
fi

# If a pinned spec (e.g. fixity-cli~=2.0.0) is unavailable, fall back to
# the latest version in the feed so older published dist can still be used.
if [[ "${PACKAGE_SPEC}" != "fixity-cli" ]]; then
  echo "Pinned spec '${PACKAGE_SPEC}' not available. Falling back to 'fixity-cli'." >&2
  python3 -m pip install \
    --index-url "${REPOSITORY_URL}" \
    --extra-index-url "${EXTRA_INDEX_URL}" \
    fixity-cli
fi

