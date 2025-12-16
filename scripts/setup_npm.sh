#!/usr/bin/env bash
set -euo pipefail

# Cross-platform setup for Node.js + npm.
# - macOS: Homebrew
# - Linux: distro package managers (apt/dnf/yum/pacman/zypper/apk)
# - Windows: winget/choco/scoop (works from Git Bash/MSYS/Cygwin/WSL shells when available)

log() { printf '%s\n' "$*"; }
die() { printf 'Error: %s\n' "$*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

detect_platform() {
    local u
    u="$(uname -s 2>/dev/null || echo unknown)"
    case "$u" in
        Darwin) echo macos ;;
        Linux) echo linux ;;
        MINGW*|MSYS*|CYGWIN*) echo windows ;;
        *) echo unknown ;;
    esac
}

verify() {
    if have node && have npm; then
        log "Installed successfully."
        log "Node: $(node --version)"
        log "npm:  $(npm --version)"
        return 0
    fi
    return 1
}

install_macos() {
    if ! have brew; then
        log "Homebrew not found. Installing Homebrew..."
        if ! have curl; then
            die "curl is required to install Homebrew. Install curl and re-run."
        fi
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi

    log "Installing Node.js (includes npm) via Homebrew..."
    brew install node
}

linux_package_manager_install() {
    if have apt-get; then
        log "Installing Node.js + npm via apt-get..."
        sudo apt-get update -y
        sudo apt-get install -y nodejs npm
        return 0
    fi

    if have dnf; then
        log "Installing Node.js + npm via dnf..."
        sudo dnf install -y nodejs npm
        return 0
    fi

    if have yum; then
        log "Installing Node.js + npm via yum..."
        sudo yum install -y nodejs npm
        return 0
    fi

    if have pacman; then
        log "Installing Node.js + npm via pacman..."
        sudo pacman -Sy --noconfirm nodejs npm
        return 0
    fi

    if have zypper; then
        log "Installing Node.js + npm via zypper..."
        sudo zypper install -y nodejs npm
        return 0
    fi

    if have apk; then
        log "Installing Node.js + npm via apk..."
        sudo apk add --no-cache nodejs npm
        return 0
    fi

    return 1
}

install_linux() {
    log "Installing Node.js (includes npm) on Linux..."
    if ! have sudo; then
        die "sudo is required for package-manager installation. Install with root privileges or install Node.js manually."
    fi
    if ! linux_package_manager_install; then
        die "Could not find a supported package manager (apt-get/dnf/yum/pacman/zypper/apk). Install Node.js LTS from https://nodejs.org/"
    fi
}

install_windows() {
    log "Installing Node.js (includes npm) on Windows..."

    if have winget; then
        log "Using winget (recommended)..."
        winget install --id OpenJS.NodeJS.LTS -e --source winget
        return 0
    fi

    if have choco; then
        log "Using Chocolatey..."
        choco install -y nodejs-lts
        return 0
    fi

    if have scoop; then
        log "Using Scoop..."
        scoop install nodejs-lts
        return 0
    fi

    die "No Windows package manager found (winget/choco/scoop). Install Node.js LTS from https://nodejs.org/ then re-run this script."
}

main() {
    log "Starting Node.js + npm setup..."

    if verify; then
        log "Already installed; nothing to do."
        exit 0
    fi

    local platform
    platform="$(detect_platform)"

    case "$platform" in
        macos) install_macos ;;
        linux) install_linux ;;
        windows) install_windows ;;
        *) die "Unsupported platform. Install Node.js LTS from https://nodejs.org/" ;;
    esac

    if ! verify; then
        die "Installation finished, but node/npm are not on PATH. Restart your terminal and try again."
    fi
}

main "$@"
