#!/bin/bash

# Setup npm on a new macOS PC
# This script installs Node.js and npm using Homebrew

echo "🚀 Starting npm setup..."

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "📦 Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    if [ $? -ne 0 ]; then
        echo "❌ Homebrew installation failed"
        exit 1
    fi
    echo "✅ Homebrew installed successfully"
else
    echo "✅ Homebrew already installed"
fi

# Install Node.js (includes npm)
echo "📥 Installing Node.js and npm..."
brew install node

# Verify installation
if command -v node &> /dev/null && command -v npm &> /dev/null; then
    echo "✅ Installation successful!"
    echo ""
    echo "Versions installed:"
    echo "Node: $(node --version)"
    echo "npm: $(npm --version)"
else
    echo "❌ Installation failed"
    exit 1
fi

echo ""
echo "🎉 npm is ready to use!"
