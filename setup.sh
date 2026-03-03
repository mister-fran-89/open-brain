#!/bin/bash
# Open Brain Bootstrap Script
# Run on fresh Debian 12 LXC: curl -fsSL <url>/setup.sh | bash

set -e

echo "========================================"
echo "       Open Brain Setup Script          "
echo "========================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log_error "Please run as root or with sudo"
    exit 1
fi

# Update system
log_info "Updating system packages..."
apt-get update
apt-get upgrade -y

# Install dependencies
log_info "Installing dependencies..."
apt-get install -y \
    curl \
    git \
    ca-certificates \
    gnupg \
    cifs-utils

# Install Docker
log_info "Installing Docker..."
if ! command -v docker &> /dev/null; then
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
        $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
        tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
else
    log_info "Docker already installed"
fi

# Create install directory
INSTALL_DIR="/opt/open-brain"
log_info "Creating installation directory: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Clone repository (or copy if local)
if [ -d ".git" ]; then
    log_info "Updating existing repository..."
    git pull
else
    log_info "Cloning repository..."
    # Replace with your actual repo URL
    git clone https://github.com/YOUR_USERNAME/open-brain.git .
fi

# Create .env from example if not exists
if [ ! -f ".env" ]; then
    log_info "Creating .env file from template..."
    cp .env.example .env
    log_warn "Please edit .env with your configuration!"
fi

# Create data directories
log_info "Creating data directories..."
mkdir -p /data
mkdir -p /vault

# Prompt for NAS mount (optional)
echo ""
log_warn "NAS Mount Configuration"
echo "If you want to mount a NAS share for the vault, add to /etc/fstab:"
echo "  //nas-ip/share /vault cifs credentials=/etc/nas-creds,uid=1000,gid=1000 0 0"
echo ""
echo "Then create /etc/nas-creds with:"
echo "  username=your_user"
echo "  password=your_pass"
echo ""

# Create brain CLI symlink
log_info "Creating brain CLI symlink..."
ln -sf "$INSTALL_DIR/cli/brain.py" /usr/local/bin/brain
chmod +x "$INSTALL_DIR/cli/brain.py"

# Summary
echo ""
echo "========================================"
echo "          Setup Complete!               "
echo "========================================"
echo ""
log_info "Next steps:"
echo "  1. Edit /opt/open-brain/.env with your configuration"
echo "  2. (Optional) Configure NAS mount for /vault"
echo "  3. Start services: cd /opt/open-brain && docker compose up -d"
echo "  4. Pull Ollama models: docker exec ollama ollama pull phi3:mini"
echo "  5. Test: brain capture 'Hello world'"
echo ""
