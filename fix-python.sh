#!/bin/bash
# Fix Python installation on Ubuntu 24.10 (Plucky)
# Run this first if you encounter PPA errors

echo "========================================="
echo "Fixing Python Installation"
echo "========================================="

# Remove problematic PPA
echo "Removing deadsnakes PPA..."
rm -f /etc/apt/sources.list.d/deadsnakes-ubuntu-ppa-*.list
rm -f /etc/apt/sources.list.d/deadsnakes-ubuntu-ppa-*.list.save

# Clean apt cache
apt-get clean
rm -rf /var/lib/apt/lists/*

# Update package list
echo "Updating package lists..."
apt-get update

# Check Ubuntu version
echo "Ubuntu version:"
lsb_release -a

# Try to install Python 3.11
echo ""
echo "Installing Python 3.11..."

if apt-cache show python3.11 > /dev/null 2>&1; then
    echo "Python 3.11 available in repos"
    apt-get install -y python3.11 python3.11-venv python3.11-dev
else
    echo "Python 3.11 not in default repos"
    
    # Check current python3 version
    PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
    echo "Current python3 version: $PYTHON_VERSION"
    
    # If python3 is 3.11 or higher, create symlink
    if python3 --version 2>&1 | grep -qE "Python 3\.(1[1-9]|[2-9][0-9])"; then
        echo "Python 3.11+ already installed as python3"
        echo "Creating python3.11 symlink..."
        ln -sf $(which python3) /usr/local/bin/python3.11
        
        # Install venv
        apt-get install -y python3-venv python3-dev
    else
        echo "Need to install Python 3.11 manually"
        echo "Installing dependencies..."
        apt-get install -y build-essential libssl-dev libffi-dev \
            libncurses5-dev zlib1g-dev libbz2-dev libreadline-dev \
            libsqlite3-dev wget curl llvm libncursesw5-dev \
            xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
        
        echo ""
        echo "You can either:"
        echo "1. Use pyenv to install Python 3.11"
        echo "2. Build from source"
        echo "3. Wait for Ubuntu packages to be updated"
        echo ""
        echo "For quick fix, we'll create a symlink if python3 >= 3.10"
        
        if python3 --version 2>&1 | grep -qE "Python 3\.1[0-9]"; then
            echo "Using python3 (compatible version)"
            ln -sf $(which python3) /usr/local/bin/python3.11
            apt-get install -y python3-venv python3-dev
        fi
    fi
fi

# Verify installation
echo ""
echo "========================================="
echo "Verification:"
echo "========================================="

if command -v python3.11 &> /dev/null; then
    echo "✅ python3.11: $(python3.11 --version)"
else
    echo "❌ python3.11 not found"
fi

if command -v python3 &> /dev/null; then
    echo "✅ python3: $(python3 --version)"
else
    echo "❌ python3 not found"
fi

echo ""
echo "Python executable paths:"
which python3.11 || echo "python3.11 not in PATH"
which python3 || echo "python3 not in PATH"

echo ""
echo "========================================="
echo "Fix Complete!"
echo "========================================="
echo ""
echo "Now you can run:"
echo "  ./deploy_production.sh"
echo ""
