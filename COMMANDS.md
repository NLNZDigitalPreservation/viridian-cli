# Simulator and Fixity Equivalent Shell Commands

This file maps the CLI commands to equivalent shell commands.

## Common Variables

```bash
# Choose container engine the same way as the CLI auto mode.
if command -v podman >/dev/null 2>&1; then
	ENGINE="podman"
elif command -v docker >/dev/null 2>&1; then
	ENGINE="docker"
else
	echo "Neither podman nor docker is installed" >&2
	exit 1
fi

# Compose command selection used by the CLI.
if [ "$ENGINE" = "podman" ] && command -v podman-compose >/dev/null 2>&1; then
	COMPOSE="podman-compose"
elif [ "$ENGINE" = "podman" ]; then
	COMPOSE="podman compose"
else
	COMPOSE="docker compose"
fi

# Defaults used by the CLI.
INSTALL_PATH="${INSTALL_PATH:-/usr/local/fixity}"
DATA_PATH="${DATA_PATH:-/persistent}"

SIM_PROJECT="viridian-dev"
MASTER_PROJECT="viridian-fixity"

SIM_COMPOSE="$INSTALL_PATH/docker-compose-dev.yml"
MASTER_COMPOSE="$INSTALL_PATH/docker-compose-fixity.yml"
MASTER_ENV="$INSTALL_PATH/.env"
```

## Simulator Command Equivalents

```bash
# simulator up
mkdir -p "$DATA_PATH/containers" "$DATA_PATH/azurite" "$DATA_PATH/oracle"
sudo chown -R "$(id -un):$(id -gn)" "$DATA_PATH/containers" "$DATA_PATH/azurite"
sudo chown -R 54321:54321 "$DATA_PATH/oracle"
sudo chmod -R 777 "$DATA_PATH/oracle"
${COMPOSE} -p "$SIM_PROJECT" -f "$SIM_COMPOSE" up --detach

# simulator down
${COMPOSE} -p "$SIM_PROJECT" -f "$SIM_COMPOSE" down

# simulator logs
${COMPOSE} -p "$SIM_PROJECT" -f "$SIM_COMPOSE" logs -f

# simulator logs --no-follow
${COMPOSE} -p "$SIM_PROJECT" -f "$SIM_COMPOSE" logs
```

## Fixity Command Equivalents

```bash
# fixity up
mkdir -p "$DATA_PATH/containers" "$DATA_PATH/fixity"
sudo chown -R "$(id -un):$(id -gn)" "$DATA_PATH/containers" "$DATA_PATH/fixity"
${COMPOSE} -p "$MASTER_PROJECT" -f "$MASTER_COMPOSE" --env-file "$MASTER_ENV" up --detach

# fixity down
${COMPOSE} -p "$MASTER_PROJECT" -f "$MASTER_COMPOSE" --env-file "$MASTER_ENV" down

# fixity logs
${COMPOSE} -p "$MASTER_PROJECT" -f "$MASTER_COMPOSE" --env-file "$MASTER_ENV" logs -f

# fixity logs --no-follow
${COMPOSE} -p "$MASTER_PROJECT" -f "$MASTER_COMPOSE" --env-file "$MASTER_ENV" logs

# fixity exec
${ENGINE} exec -it fixity_master bash

# fixity exec --shell sh
${ENGINE} exec -it fixity_master sh
```

## Fixity Build and Push Equivalents

```bash
# The CLI reads version from image tag in docker-compose-fixity.yml.
# Fallback is latest if no tag is found.
VERSION="$(awk -F: '/^[[:space:]]*image:[[:space:]]*.*fixity-master:/ {v=$NF} END {gsub(/[[:space:]]+/, "", v); print (v=="" ? "latest" : v)}' "$MASTER_COMPOSE")"

PROJECT_ROOT="${PROJECT_ROOT:-.}"
DOCKERFILE="$PROJECT_ROOT/deployment/master/Dockerfile"
REGISTRY="acrdiaanlnznsbx.azurecr.io"
IMAGE="fixity-master"

# fixity build
${ENGINE} build -f "$DOCKERFILE" --tag "$IMAGE:$VERSION" "$PROJECT_ROOT"
${ENGINE} tag "$IMAGE:$VERSION" "$REGISTRY/$IMAGE:$VERSION"

# fixity push
${ENGINE} push "$REGISTRY/$IMAGE:$VERSION"
```

## Notes

- These commands assume assets were installed to the installation directory first.
- CLI commands `fixity install` and `fixity info` are workflow/orchestration commands, not single compose command wrappers.
