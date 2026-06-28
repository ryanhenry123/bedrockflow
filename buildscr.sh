#!/bin/bash
set -euo pipefail

curl_download() {
    local url="$1"
    local output="$2"
    curl -fsSL \
        --retry 5 \
        --retry-delay 2 \
        --retry-all-errors \
        --connect-timeout 30 \
        "${url}" \
        -o "${output}"
}

download_uv_asset() {
    local name="$1"
    local output="$2"
    local uv_version="$3"
    local base

    for base in \
        "https://github.com/astral-sh/uv/releases/download/${uv_version}" \
        "https://releases.astral.sh/github/uv/releases/download/${uv_version}"; do
        if curl_download "${base}/${name}" "${output}"; then
            return 0
        fi
        echo "warning: failed to download ${name} from ${base}" >&2
        rm -f "${output}"
    done

    echo "error: failed to download ${name}" >&2
    return 1
}

installdeps() {
    apt-get update && apt-get install -y --no-install-recommends curl ca-certificates
    local uv_version="0.11.25"
    local uv_target="x86_64-unknown-linux-gnu"
    local archive="/tmp/uv-${uv_target}.tar.gz"
    local checksum_file="/tmp/uv.tar.gz.sha256"

    download_uv_asset "uv-${uv_target}.tar.gz" "${archive}" "${uv_version}"
    if ! download_uv_asset "uv-${uv_target}.tar.gz.sha256" "${checksum_file}" "${uv_version}"; then
        printf '%s  uv-%s.tar.gz\n' \
            "1db18b5e76fa645a7f3865773139bdec8e2d46adbdbb35e7410b34fa8015ccd2" \
            "${uv_target}" > "${checksum_file}"
    fi

    (cd /tmp && sha256sum -c uv.tar.gz.sha256)
    tar -xzf "${archive}" -C /usr/local/bin --strip-components=1
    rm "${archive}" "${checksum_file}"
}

build() {
    local input="$1"

    case "$input" in
        installdeps) installdeps ;;
        *) echo "Error: Unknown input $input" && return 1 ;;
    esac
}

build "$1"
