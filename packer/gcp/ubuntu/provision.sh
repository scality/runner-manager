#!/bin/bash
# Ubuntu provisioning script for GitHub Actions runner base image
# This script is called by Packer to configure the image

set -e

echo "=========================================="
echo "Ubuntu Provisioning Starting"
echo "=========================================="

# Update system packages
echo "Step 1/4: Updating system packages..."
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y

# Install base dependencies
echo "Step 2/4: Installing base dependencies..."
DEBIAN_FRONTEND=noninteractive apt-get install -y \
	apt-transport-https \
	ca-certificates \
	curl \
	gnupg \
	lsb-release

# Install Docker CE
echo "Step 3/4: Installing Docker CE..."
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo \
	"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${VERSION_CODENAME}") stable" |
	tee /etc/apt/sources.list.d/docker.list >/dev/null

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io

# Configure Docker
systemctl enable docker
groupadd -f docker

# Clean up
echo "Step 4/4: Cleaning up..."
apt-get clean
rm -rf /var/lib/apt/lists/*
rm -rf /tmp/*
rm -f ~/.bash_history

echo "=========================================="
echo "Ubuntu Provisioning Completed"
echo "=========================================="
