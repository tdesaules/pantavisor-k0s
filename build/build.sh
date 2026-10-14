#!/usr/bin/env bash
set -euo pipefail
root=$(git rev-parse --show-toplevel)
profile=${1:-base}
case "$profile" in base) ;; *) exit 2 ;; esac
mkdir -p "$root/artifacts/build/$profile" "$root/artifacts/downloads" "$root/artifacts/sstate-cache"
configs=/work/kas/base.yml
mounts=()
if [ -n "${DOWNLOAD_CACHE:-}" ]; then mounts+=(-v "$(realpath "$DOWNLOAD_CACHE"):/work/artifacts/downloads"); fi
if [ -n "${SSTATE_CACHE:-}" ]; then mounts+=(-v "$(realpath "$SSTATE_CACHE"):/work/artifacts/sstate-cache"); fi
exec podman run --rm --userns=keep-id:uid=30000,gid=30000 --security-opt label=disable \
    -v "$root:/work" "${mounts[@]}" -w /work -e KAS_WORK_DIR=/work \
    -e "KAS_BUILD_DIR=/work/artifacts/build/$profile" \
    ghcr.io/siemens/kas/kas@sha256:22c70f90e21997c0b6743ad2d802cf1d942c28e974361c4733b8a026cb7ef809 \
    build "$configs"
