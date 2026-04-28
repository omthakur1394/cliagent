#!/bin/bash
echo ""
echo "🛡️  Installing CodeGuard..."
echo ""

# Install Python if missing
if ! command -v python3 &> /dev/null; then
    echo "Python not found. Installing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # Mac
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        brew install python3
    else
        # Linux
        sudo apt-get update && sudo apt-get install -y python3 python3-pip
    fi
fi

# Install codeguard
pip3 install codeguard-ai

echo ""
echo "✅ CodeGuard installed! Run with: codeguard"
echo ""